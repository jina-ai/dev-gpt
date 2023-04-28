import os
import random
import re
import shutil
from typing import List, Callable, Union

from langchain import PromptTemplate

from src.apis import gpt
from src.apis.jina_cloud import process_error_message, push_executor, is_executor_in_hub
from src.constants import FILE_AND_TAG_PAIRS, NUM_IMPLEMENTATION_STRATEGIES, MAX_DEBUGGING_ITERATIONS, \
    PROBLEMATIC_PACKAGES, EXECUTOR_FILE_NAME, TEST_EXECUTOR_FILE_NAME, TEST_EXECUTOR_FILE_TAG, \
    REQUIREMENTS_FILE_NAME, REQUIREMENTS_FILE_TAG, DOCKER_FILE_NAME, UNNECESSARY_PACKAGES, IMPLEMENTATION_FILE_NAME, \
    IMPLEMENTATION_FILE_TAG
from src.options.generate.templates_user import template_generate_microservice_name, \
    template_generate_possible_packages, \
    template_solve_code_issue, \
    template_solve_pip_dependency_issue, template_is_dependency_issue, template_generate_playground, \
    template_generate_function, template_generate_test, template_generate_requirements, \
    template_chain_of_thought, template_summarize_error, \
    template_generate_apt_get_install, template_solve_apt_get_dependency_issue
from src.utils.io import persist_file, get_all_microservice_files_with_content, get_microservice_path
from src.utils.string_tools import print_colored


class Generator:
    def __init__(self, task_description, test_description, path, model='gpt-4'):
        self.gpt_session = gpt.GPTSession(task_description, test_description, model=model)
        self.task_description = task_description
        self.test_description = test_description
        self.microservice_root_path = path

    def extract_content_from_result(self, plain_text, file_name, match_single_block=False):
        pattern = fr"^\*\*{file_name}\*\*\n```(?:\w+\n)?([\s\S]*?)\n```" # the \n at the end makes sure that ``` within the generated code is not matched
        match = re.search(pattern, plain_text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        elif match_single_block:
            # Check for a single code block
            single_code_block_pattern = r"^```(?:\w+\n)?([\s\S]*?)```"
            single_code_block_match = re.findall(single_code_block_pattern, plain_text, re.MULTILINE)
            if len(single_code_block_match) == 1:
                return single_code_block_match[0].strip()
        return ''

    def write_config_yml(self, class_name, dest_folder, python_file=EXECUTOR_FILE_NAME):
        config_content = f'''jtype: {class_name}
py_modules:
  - {python_file}
metas:
  name: {class_name}
'''
        with open(os.path.join(dest_folder, 'config.yml'), 'w', encoding='utf-8') as f:
            f.write(config_content)

    def files_to_string(self, file_name_to_content, restrict_keys=None):
        all_microservice_files_string = ''
        for file_name, tag in FILE_AND_TAG_PAIRS:
            if file_name in file_name_to_content and (not restrict_keys or file_name in restrict_keys):
                all_microservice_files_string += f'**{file_name}**\n```{tag}\n{file_name_to_content[file_name]}\n```\n\n'
        return all_microservice_files_string.strip()

    def get_default_parse_result_fn(self, files_names: List[str]):
        def _default_parse_result_fn(x):
            _parsed_results = {}
            for _file_name in files_names:
                _content = self.extract_content_from_result(x, _file_name, match_single_block=len(files_names)==1)
                if _content != '':
                    _parsed_results[_file_name] = _content
            return _parsed_results
        return _default_parse_result_fn

    def generate_and_persist_file(
            self,
            section_title: str,
            template: PromptTemplate,
            destination_folder: str,
            file_name_s: Union[str, List[str]] = None,
            parse_result_fn: Callable = None,
            system_definition_examples: List[str] = [],
            **template_kwargs
    ):
        """This function generates file(s) using the given template and persists it/them in the given destination folder.
        It also returns the generated content as a dictionary mapping file_name to its content.

        Args:
            section_title (str): The title of the section to be printed in the console.
            template (PromptTemplate): The template to be used for generating the file(s).
            destination_folder (str): The destination folder where the generated file(s) should be persisted.
            file_name_s (Union[str, List[str]], optional): The name of the file(s) to be generated. Defaults to None.
            parse_result_fn (Callable, optional): A function that parses the generated content and returns a dictionary
                mapping file_name to its content. If no content could be extract, it returns an empty dictionary.
                Defaults to None. If None, default parsing is used which uses the file_name to extract from the generated content.
            system_definition_examples (List[str], optional): The system definition examples to be used for the conversation.
                Defaults to ['gpt', 'executor', 'docarray', 'client'].
            **template_kwargs: The keyword arguments to be passed to the template.
        """
        if parse_result_fn is None:
            parse_result_fn = self.get_default_parse_result_fn([file_name_s] if isinstance(file_name_s, str) else file_name_s)

        print_colored('', f'\n\n############# {section_title} #############', 'blue')
        conversation = self.gpt_session.get_conversation(system_definition_examples=system_definition_examples)
        template_kwargs = {k: v for k, v in template_kwargs.items() if k in template.input_variables}
        if 'file_name' in template.input_variables:
            template_kwargs['file_name'] = file_name_s
        content_raw = conversation.chat(
            template.format(
                **template_kwargs
            )
        )
        content = parse_result_fn(content_raw)
        if content == {}:
            content_raw = conversation.chat('You must add the content' + (f' for {file_name_s}' if isinstance(file_name_s, str) else ''))
            content = parse_result_fn(content_raw)
        for _file_name, _file_content in content.items():
            persist_file(_file_content, os.path.join(destination_folder, _file_name))
        return content

    def generate_microservice(
            self,
            microservice_name,
            packages,
            num_approach,
    ):
        MICROSERVICE_FOLDER_v1 = get_microservice_path(self.microservice_root_path, microservice_name, packages, num_approach, 1)
        os.makedirs(MICROSERVICE_FOLDER_v1)

        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'microservice.py'), 'r') as f:
            microservice_executor_boilerplate = f.read()
        microservice_executor_code = microservice_executor_boilerplate.replace('class GPTDeployExecutor(Executor):', f'class {microservice_name}(Executor):')
        persist_file(microservice_executor_code, os.path.join(MICROSERVICE_FOLDER_v1, EXECUTOR_FILE_NAME))

        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'apis.py'), 'r') as f:
            persist_file(f.read(), os.path.join(MICROSERVICE_FOLDER_v1, 'apis.py'))

        microservice_content = self.generate_and_persist_file(
            section_title='Microservice',
            template=template_generate_function,
            destination_folder=MICROSERVICE_FOLDER_v1,
            # microservice_name=microservice_name,
            microservice_description=self.task_description,
            test_description=self.test_description,
            packages=packages,
            file_name_purpose=IMPLEMENTATION_FILE_NAME,
            tag_name=IMPLEMENTATION_FILE_TAG,
            file_name_s=IMPLEMENTATION_FILE_NAME,
        )[IMPLEMENTATION_FILE_NAME]

        test_microservice_content = self.generate_and_persist_file(
            'Test Microservice',
            template_generate_test,
            MICROSERVICE_FOLDER_v1,
            code_files_wrapped=self.files_to_string({EXECUTOR_FILE_NAME: microservice_content}),
            microservice_name=microservice_name,
            microservice_description=self.task_description,
            test_description=self.test_description,
            file_name_purpose=TEST_EXECUTOR_FILE_NAME,
            tag_name=TEST_EXECUTOR_FILE_TAG,
            file_name_s=TEST_EXECUTOR_FILE_NAME,
        )[TEST_EXECUTOR_FILE_NAME]

        requirements_content = self.generate_and_persist_file(
            'Requirements',
            template_generate_requirements,
            MICROSERVICE_FOLDER_v1,
            system_definition_examples=None,
            code_files_wrapped=self.files_to_string({
                IMPLEMENTATION_FILE_NAME: microservice_content,
                TEST_EXECUTOR_FILE_NAME: test_microservice_content,
            }),
            file_name_purpose=REQUIREMENTS_FILE_NAME,
            file_name_s=REQUIREMENTS_FILE_NAME,
            tag_name=REQUIREMENTS_FILE_TAG,
        )[REQUIREMENTS_FILE_NAME]

        self.generate_and_persist_file(
            section_title='Generate Dockerfile',
            template=template_generate_apt_get_install,
            destination_folder=MICROSERVICE_FOLDER_v1,
            file_name_s=None,
            parse_result_fn=self.parse_result_fn_dockerfile,
            docker_file_wrapped=self.read_docker_template(),
            requirements_file_wrapped=self.files_to_string({
                REQUIREMENTS_FILE_NAME: requirements_content,
            })
        )

        self.write_config_yml(microservice_name, MICROSERVICE_FOLDER_v1)

        print('\nFirst version of the microservice generated. Start iterating on it to make the tests pass...')

    @staticmethod
    def read_docker_template():
        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'Dockerfile'), 'r') as f:
            return f.read()

    def parse_result_fn_dockerfile(self, content_raw: str):
        docker_file_template = self.read_docker_template()
        return {DOCKER_FILE_NAME: docker_file_template.replace('{{apt_get_packages}}', '{apt_get_packages}').format(apt_get_packages=content_raw)}

    def generate_playground(self, microservice_name, microservice_path):
        print_colored('', '\n\n############# Playground #############', 'blue')

        file_name_to_content = get_all_microservice_files_with_content(microservice_path)
        conversation = self.gpt_session.get_conversation(None)
        conversation.chat(
            template_generate_playground.format(
                code_files_wrapped=self.files_to_string(file_name_to_content, ['test_microservice.py']),
                microservice_name=microservice_name,
            )
        )
        playground_content_raw = conversation.chat(
            template_chain_of_thought.format(
                file_name_purpose='app.py/the playground',
                file_name='app.py',
                tag_name='python',
            )
        )
        playground_content = self.extract_content_from_result(playground_content_raw, 'app.py', match_single_block=True)
        if playground_content == '':
            content_raw = conversation.chat(f'You must add the app.py code. You most not output any other code')
            playground_content = self.extract_content_from_result(
                content_raw, 'app.py', match_single_block=True
            )

        gateway_path = os.path.join(microservice_path, 'gateway')
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'static_files', 'gateway'), gateway_path)
        persist_file(playground_content, os.path.join(gateway_path, 'app.py'))

        # fill-in name of microservice
        gateway_name = f'Gateway{microservice_name}'
        custom_gateway_path = os.path.join(gateway_path, 'custom_gateway.py')
        with open(custom_gateway_path, 'r', encoding='utf-8') as f:
            custom_gateway_content = f.read()
        custom_gateway_content = custom_gateway_content.replace(
            'class CustomGateway(CompositeGateway):',
            f'class {gateway_name}(CompositeGateway):'
        )
        with open(custom_gateway_path, 'w', encoding='utf-8') as f:
            f.write(custom_gateway_content)

        # write config.yml
        self.write_config_yml(gateway_name, gateway_path, 'custom_gateway.py')

        # push the gateway
        print('Final step...')
        hubble_log = push_executor(gateway_path)
        if not is_executor_in_hub(gateway_name):
            raise Exception(f'{microservice_name} not in hub. Hubble logs: {hubble_log}')

    def debug_microservice(self, microservice_name, num_approach, packages):
        for i in range(1, MAX_DEBUGGING_ITERATIONS):
            print('Debugging iteration', i)
            print('Trying to debug the microservice. Might take a while...')
            previous_microservice_path = get_microservice_path(self.microservice_root_path, microservice_name, packages, num_approach, i)
            next_microservice_path = get_microservice_path(self.microservice_root_path, microservice_name, packages, num_approach, i + 1)
            log_hubble = push_executor(previous_microservice_path)
            error = process_error_message(log_hubble)
            if error:
                print('An error occurred during the build process. Feeding the error back to the assistent...')
                self.do_debug_iteration(error, next_microservice_path, previous_microservice_path)
                if i == MAX_DEBUGGING_ITERATIONS - 1:
                    raise self.MaxDebugTimeReachedException('Could not debug the microservice.')
            else:
                # at the moment, there can be cases where no error log is extracted but the executor is still not published
                # it leads to problems later on when someone tries a run or deployment
                if is_executor_in_hub(microservice_name):
                    print('Successfully build microservice.')
                    break
                else:
                    raise Exception(f'{microservice_name} not in hub. Hubble logs: {log_hubble}')

        return get_microservice_path(self.microservice_root_path, microservice_name, packages, num_approach, i)

    def do_debug_iteration(self, error, next_microservice_path, previous_microservice_path):
        os.makedirs(next_microservice_path)
        file_name_to_content = get_all_microservice_files_with_content(previous_microservice_path)
        for file_name, content in file_name_to_content.items():
            persist_file(content, os.path.join(next_microservice_path, file_name))

        summarized_error = self.summarize_error(error)
        dock_req_string = self.files_to_string({
            key: val for key, val in file_name_to_content.items() if
            key in ['requirements.txt', 'Dockerfile']
        })

        is_apt_get_dependency_issue = self.is_dependency_issue(summarized_error, dock_req_string, 'apt-get')
        if is_apt_get_dependency_issue:
            self.generate_and_persist_file(
                section_title='Debugging apt-get dependency issue',
                template=template_solve_apt_get_dependency_issue,
                destination_folder=next_microservice_path,
                file_name_s=None,
                parse_result_fn=self.parse_result_fn_dockerfile,
                system_definition_examples=None,
                summarized_error=summarized_error,
                all_files_string=dock_req_string,
            )
            print('Dockerfile updated')
        else:
            is_pip_dependency_issue = self.is_dependency_issue(summarized_error, dock_req_string, 'PIP')
            if is_pip_dependency_issue:
                self.generate_and_persist_file(
                    section_title='Debugging pip dependency issue',
                    template=template_solve_pip_dependency_issue,
                    destination_folder=next_microservice_path,
                    file_name_s=REQUIREMENTS_FILE_NAME,
                    summarized_error=summarized_error,
                    all_files_string=dock_req_string,
                )
            else:
                self.generate_and_persist_file(
                    section_title='Debugging code issue',
                    template=template_solve_code_issue,
                    destination_folder=next_microservice_path,
                    file_name_s=[IMPLEMENTATION_FILE_NAME, TEST_EXECUTOR_FILE_NAME, REQUIREMENTS_FILE_NAME],
                    summarized_error=summarized_error,
                    task_description=self.task_description,
                    test_description=self.test_description,
                    all_files_string=self.files_to_string({key: val for key, val in file_name_to_content.items() if key != EXECUTOR_FILE_NAME}),
                )

    class MaxDebugTimeReachedException(BaseException):
        pass

    def is_dependency_issue(self, summarized_error, dock_req_string: str, package_manager: str):
        # a few heuristics to quickly jump ahead
        if any([error_message in summarized_error for error_message in ['AttributeError', 'NameError', 'AssertionError']]):
            return False
        if package_manager.lower() == 'pip' and any([em in summarized_error for em in ['ModuleNotFoundError', 'ImportError']]):
            return True

        print_colored('', f'Is it a {package_manager} dependency issue?', 'blue')
        conversation = self.gpt_session.get_conversation(None)
        answer = conversation.chat(
            template_is_dependency_issue.format(summarized_error=summarized_error, all_files_string=dock_req_string).replace('PACKAGE_MANAGER', package_manager)
        )
        return 'yes' in answer.lower()

    def generate_microservice_name(self, description):
        print_colored('', '\n\n############# What should be the name of the Microservice? #############', 'blue')
        name = self.generate_and_persist_file(
            section_title='Generate microservice name',
            template=template_generate_microservice_name,
            destination_folder=self.microservice_root_path,
            file_name_s='name.txt',
            description=description
        )['name.txt']
        return name

    def get_possible_packages(self):
        print_colored('', '\n\n############# What packages to use? #############', 'blue')
        packages_csv_string = self.generate_and_persist_file(
            section_title='Generate possible packages',
            template=template_generate_possible_packages,
            destination_folder=self.microservice_root_path,
            file_name_s='packages.csv',
            system_definition_examples=[],
            description=self.task_description
        )['packages.csv']
        packages_list = [[pkg.strip().lower() for pkg in packages_string.split(',')] for packages_string in packages_csv_string.split('\n')]
        packages_list = [
            packages for packages in packages_list if len(set(packages).intersection(set(PROBLEMATIC_PACKAGES))) == 0
        ]
        packages_list = [
            [package for package in packages if package not in UNNECESSARY_PACKAGES] for packages in packages_list
        ]
        packages_list = packages_list[:NUM_IMPLEMENTATION_STRATEGIES]
        return packages_list

    def generate(self):
        os.makedirs(self.microservice_root_path)
        generated_name = self.generate_microservice_name(self.task_description)
        microservice_name = f'{generated_name}{random.randint(0, 10_000_000)}'
        packages_list = self.get_possible_packages()
        for num_approach, packages in enumerate(packages_list):
            try:
                self.generate_microservice(microservice_name, packages, num_approach)
                final_version_path = self.debug_microservice(microservice_name, num_approach, packages)
                self.generate_playground(microservice_name, final_version_path)
            except self.MaxDebugTimeReachedException:
                print('Could not debug the Microservice with the approach:', packages)
                if num_approach == len(packages_list) - 1:
                    print_colored('',
                                  f'Could not debug the Microservice with any of the approaches: {packages} giving up.',
                                  'red')
                continue
            print(f'''
You can now run or deploy your microservice:
gptdeploy run --path {self.microservice_root_path}
gptdeploy deploy --path {self.microservice_root_path}
'''
                  )
            break

    def summarize_error(self, error):
        conversation = self.gpt_session.get_conversation(None)
        error_summary = conversation.chat(template_summarize_error.format(error=error))
        return error_summary

