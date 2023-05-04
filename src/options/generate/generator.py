import json
import os
import random
import re
import shutil
from typing import Callable
from typing import List, Text, Optional

from langchain import PromptTemplate
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from pydantic.dataclasses import dataclass

from src.apis import gpt
from src.apis.gpt import _GPTConversation
from src.apis.jina_cloud import process_error_message, push_executor, is_executor_in_hub
from src.apis.pypi import is_package_on_pypi, get_latest_package_version, clean_requirements_txt
from src.constants import FILE_AND_TAG_PAIRS, NUM_IMPLEMENTATION_STRATEGIES, MAX_DEBUGGING_ITERATIONS, \
    BLACKLISTED_PACKAGES, EXECUTOR_FILE_NAME, TEST_EXECUTOR_FILE_NAME, TEST_EXECUTOR_FILE_TAG, \
    REQUIREMENTS_FILE_NAME, REQUIREMENTS_FILE_TAG, DOCKER_FILE_NAME, IMPLEMENTATION_FILE_NAME, \
    IMPLEMENTATION_FILE_TAG, LANGUAGE_PACKAGES, UNNECESSARY_PACKAGES
from src.options.generate.templates_system import system_task_iteration, system_task_introduction, system_test_iteration
from src.options.generate.templates_user import template_generate_microservice_name, \
    template_generate_possible_packages, \
    template_solve_code_issue, \
    template_solve_pip_dependency_issue, template_is_dependency_issue, template_generate_playground, \
    template_generate_function, template_generate_test, template_generate_requirements, \
    template_chain_of_thought, template_summarize_error, \
    template_solve_apt_get_dependency_issue, template_pm_task_iteration, \
    template_pm_test_iteration
from src.options.generate.ui import get_random_employee
from src.utils.io import persist_file, get_all_microservice_files_with_content, get_microservice_path
from src.utils.string_tools import print_colored


@dataclass
class TaskSpecification:
    task: Optional[Text]
    test: Optional[Text]


class Generator:
    def __init__(self, task_description, path, model='gpt-4'):
        self.gpt_session = gpt.GPTSession(task_description, model=model)
        self.microservice_specification = TaskSpecification(task=task_description, test=None)
        self.microservice_root_path = path

    @staticmethod
    def extract_content_from_result(plain_text, file_name, match_single_block=False, can_contain_code_block=True):
        optional_line_break = '\n' if can_contain_code_block else ''  # the \n at the end makes sure that ``` within the generated code is not matched because it is not right before a line break
        pattern = fr"(?:\*|\*\*| ){file_name}\*?\*?\n```(?:\w+\n)?([\s\S]*?){optional_line_break}```"
        matches = re.findall(pattern, plain_text, re.MULTILINE)
        if matches:
            return matches[-1].strip()
        elif match_single_block:
            # Check for a single code block
            single_code_block_pattern = r"```(?:\w+\n)?([\s\S]*?)```"
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
                _content = self.extract_content_from_result(x, _file_name, match_single_block=len(files_names) == 1)
                if _content != '':
                    _parsed_results[_file_name] = _content
            return _parsed_results

        return _default_parse_result_fn

    def generate_and_persist_file(
            self,
            section_title: str,
            template: PromptTemplate,
            destination_folder: str,
            file_name_s: List[str] = None,
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
            file_name_s (List[str], optional): The name of the file(s) to be generated. Defaults to None.
            parse_result_fn (Callable, optional): A function that parses the generated content and returns a dictionary
                mapping file_name to its content. If no content could be extract, it returns an empty dictionary.
                Defaults to None. If None, default parsing is used which uses the file_name to extract from the generated content.
            system_definition_examples (List[str], optional): The system definition examples to be used for the conversation. Defaults to [].
            **template_kwargs: The keyword arguments to be passed to the template.
        """
        if parse_result_fn is None:
            parse_result_fn = self.get_default_parse_result_fn(file_name_s)

        print_colored('', f'\n\n############# {section_title} #############', 'blue')
        system_introduction_message = _GPTConversation._create_system_message(self.microservice_specification.task,
                                                                              self.microservice_specification.test,
                                                                              system_definition_examples)
        conversation = self.gpt_session.get_conversation(messages=[system_introduction_message])
        template_kwargs = {k: v for k, v in template_kwargs.items() if k in template.input_variables}
        if 'file_name' in template.input_variables and len(file_name_s) == 1:
            template_kwargs['file_name'] = file_name_s[0]
        content_raw = conversation.chat(
            template.format(
                **template_kwargs
            )
        )
        content = parse_result_fn(content_raw)
        if content == {}:
            content_raw = conversation.chat(
                'You must add the content' + (f' for {file_name_s[0]}' if len(file_name_s) == 1 else ''))
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
        MICROSERVICE_FOLDER_v1 = get_microservice_path(self.microservice_root_path, microservice_name, packages,
                                                       num_approach, 1)
        os.makedirs(MICROSERVICE_FOLDER_v1)

        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'jina_wrapper.py'), 'r', encoding='utf-8') as f:
            microservice_executor_boilerplate = f.read()
        microservice_executor_code = microservice_executor_boilerplate.replace('class GPTDeployExecutor(Executor):',
                                                                               f'class {microservice_name}(Executor):')
        persist_file(microservice_executor_code, os.path.join(MICROSERVICE_FOLDER_v1, EXECUTOR_FILE_NAME))

        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'apis.py'), 'r', encoding='utf-8') as f:
            persist_file(f.read(), os.path.join(MICROSERVICE_FOLDER_v1, 'apis.py'))

        microservice_content = self.generate_and_persist_file(
            section_title='Microservice',
            template=template_generate_function,
            destination_folder=MICROSERVICE_FOLDER_v1,
            microservice_description=self.microservice_specification.task,
            test_description=self.microservice_specification.test,
            packages=packages,
            file_name_purpose=IMPLEMENTATION_FILE_NAME,
            tag_name=IMPLEMENTATION_FILE_TAG,
            file_name_s=[IMPLEMENTATION_FILE_NAME],
        )[IMPLEMENTATION_FILE_NAME]

        test_microservice_content = self.generate_and_persist_file(
            'Test Microservice',
            template_generate_test,
            MICROSERVICE_FOLDER_v1,
            code_files_wrapped=self.files_to_string({EXECUTOR_FILE_NAME: microservice_content}),
            microservice_name=microservice_name,
            microservice_description=self.microservice_specification.task,
            test_description=self.microservice_specification.test,
            file_name_purpose=TEST_EXECUTOR_FILE_NAME,
            tag_name=TEST_EXECUTOR_FILE_TAG,
            file_name_s=[TEST_EXECUTOR_FILE_NAME],
        )[TEST_EXECUTOR_FILE_NAME]

        requirements_content = self.generate_and_persist_file(
            'Requirements',
            template_generate_requirements,
            MICROSERVICE_FOLDER_v1,
            code_files_wrapped=self.files_to_string({
                IMPLEMENTATION_FILE_NAME: microservice_content,
                TEST_EXECUTOR_FILE_NAME: test_microservice_content,
            }),
            file_name_purpose=REQUIREMENTS_FILE_NAME,
            file_name_s=[REQUIREMENTS_FILE_NAME],
            parse_result_fn=self.parse_result_fn_requirements,
            tag_name=REQUIREMENTS_FILE_TAG,
        )[REQUIREMENTS_FILE_NAME]

        # I deactivated this because 3.5-turbo was halucinating packages that were not needed
        # now, in the first iteration the default dockerfile is used
        # self.generate_and_persist_file(
        #     section_title='Generate Dockerfile',
        #     template=template_generate_apt_get_install,
        #     destination_folder=MICROSERVICE_FOLDER_v1,
        #     file_name_s=None,
        #     parse_result_fn=self.parse_result_fn_dockerfile,
        #     docker_file_wrapped=self.read_docker_template(),
        #     requirements_file_wrapped=self.files_to_string({
        #         REQUIREMENTS_FILE_NAME: requirements_content,
        #     })
        # )

        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'Dockerfile'), 'r',
                  encoding='utf-8') as f:
            docker_file_template_lines = f.readlines()
        docker_file_template_lines = [
            line.replace('{{apt_get_packages}}', '')
            for line in docker_file_template_lines
        ]
        docker_file_content = '\n'.join(docker_file_template_lines)
        persist_file(docker_file_content, os.path.join(MICROSERVICE_FOLDER_v1, 'Dockerfile'))

        self.write_config_yml(microservice_name, MICROSERVICE_FOLDER_v1)

        print('\nFirst version of the microservice generated. Start iterating on it to make the tests pass...')

    @staticmethod
    def read_docker_template():
        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'Dockerfile'), 'r', encoding='utf-8') as f:
            return f.read()

    def parse_result_fn_dockerfile(self, content_raw: str):
        json_string = self.extract_content_from_result(content_raw, 'apt-get-packages.json', match_single_block=True)
        packages = ' '.join(json.loads(json_string)['packages'])

        docker_file_template = self.read_docker_template()
        return {DOCKER_FILE_NAME: docker_file_template.replace('{{apt_get_packages}}', '{apt_get_packages}').format(
            apt_get_packages=packages)}

    def parse_result_fn_requirements(self, content_raw: str):
        content_parsed = self.extract_content_from_result(content_raw, 'requirements.txt', match_single_block=True)

        lines = content_parsed.split('\n')
        lines = [line for line in lines if
                 not any([pkg in line for pkg in ['jina', 'docarray', 'openai', 'pytest', 'gpt_3_5_turbo']])]
        content_modified = f'''jina==3.15.1.dev14
docarray==0.21.0
openai==0.27.5
pytest
{os.linesep.join(lines)}'''
        return {REQUIREMENTS_FILE_NAME: content_modified}

    def generate_playground(self, microservice_name, microservice_path):
        print_colored('', '\n\n############# Playground #############', 'blue')

        file_name_to_content = get_all_microservice_files_with_content(microservice_path)
        conversation = self.gpt_session.get_conversation()
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
            previous_microservice_path = get_microservice_path(self.microservice_root_path, microservice_name, packages,
                                                               num_approach, i)
            next_microservice_path = get_microservice_path(self.microservice_root_path, microservice_name, packages,
                                                           num_approach, i + 1)
            clean_requirements_txt(previous_microservice_path)
            log_hubble = push_executor(previous_microservice_path)
            error = process_error_message(log_hubble)
            if error:
                print('An error occurred during the build process. Feeding the error back to the assistant...')
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
                file_name_s=['apt-get-packages.json'],
                parse_result_fn=self.parse_result_fn_dockerfile,
                system_definition_examples=[],
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
                    file_name_s=[REQUIREMENTS_FILE_NAME],
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
                    task_description=self.microservice_specification.task,
                    test_description=self.microservice_specification.test,
                    all_files_string=self.files_to_string(
                        {key: val for key, val in file_name_to_content.items() if key != EXECUTOR_FILE_NAME}),
                )

    class MaxDebugTimeReachedException(BaseException):
        pass

    class TaskRefinementException(BaseException):
        pass

    def is_dependency_issue(self, summarized_error, dock_req_string: str, package_manager: str):
        # a few heuristics to quickly jump ahead
        if any([error_message in summarized_error for error_message in
                ['AttributeError', 'NameError', 'AssertionError']]):
            return False
        if package_manager.lower() == 'pip' and any(
                [em in summarized_error for em in ['ModuleNotFoundError', 'ImportError']]):
            return True

        print_colored('', f'Is it a {package_manager} dependency issue?', 'blue')
        conversation = self.gpt_session.get_conversation()
        answer_raw = conversation.chat(
            template_is_dependency_issue.format(summarized_error=summarized_error,
                                                all_files_string=dock_req_string).replace('PACKAGE_MANAGER',
                                                                                          package_manager)
        )
        answer_json_string = self.extract_content_from_result(answer_raw, 'response.json', match_single_block=True, )
        answer = json.loads(answer_json_string)['dependency_installation_failure']
        return 'yes' in answer.lower()

    def generate_microservice_name(self, description):
        name = self.generate_and_persist_file(
            section_title='Generate microservice name',
            template=template_generate_microservice_name,
            destination_folder=self.microservice_root_path,
            file_name_s=['name.txt'],
            description=description
        )['name.txt']
        return name

    def get_possible_packages(self):
        print_colored('', '\n\n############# What packages to use? #############', 'blue')
        packages_json_string = self.generate_and_persist_file(
            section_title='Generate possible packages',
            template=template_generate_possible_packages,
            destination_folder=self.microservice_root_path,
            file_name_s=['strategies.json'],
            system_definition_examples=[],
            description=self.microservice_specification.task
        )['strategies.json']
        packages_list = [[pkg.strip().lower() for pkg in packages] for packages in json.loads(packages_json_string)]
        packages_list = [[self.replace_with_gpt_3_5_turbo_if_possible(pkg) for pkg in packages] for packages in
                         packages_list]

        packages_list = self.filter_packages_list(packages_list)
        packages_list = packages_list[:NUM_IMPLEMENTATION_STRATEGIES]
        return packages_list

    def generate(self):
        self.refine_specification()
        os.makedirs(self.microservice_root_path)
        generated_name = self.generate_microservice_name(self.microservice_specification.task)
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
                    return -1
                continue
            print(f'''
You can now run or deploy your microservice:
gptdeploy run --path {self.microservice_root_path}
gptdeploy deploy --path {self.microservice_root_path}
'''
                  )
            return 0

    def summarize_error(self, error):
        conversation = self.gpt_session.get_conversation()
        error_summary = conversation.chat(template_summarize_error.format(error=error))
        return error_summary

    def refine_specification(self):
        pm = get_random_employee('pm')
        print(f'{pm.emoji}👋 Hi, I\'m {pm.name}, a PM at Jina AI. Gathering the requirements for our engineers.')
        original_task = self.microservice_specification.task
        while True:
            try:
                self.microservice_specification.test = None
                if not original_task:
                    self.microservice_specification.task = self.get_user_input(pm, 'What should your microservice do?')

                self.refine_requirements(
                    pm,
                    [
                        SystemMessage(content=system_task_introduction + system_task_iteration),
                    ],
                    'task',
                    '',
                    template_pm_task_iteration,
                    micro_service_initial_description=f'''Microservice description:
```
{self.microservice_specification.task}
```
''',
                )
                self.refine_requirements(
                    pm,
                    [
                        SystemMessage(content=system_task_introduction + system_test_iteration),
                    ],
                    'test',
                    '''Note that the test scenario must not contain information that was already mentioned in the microservice description.
Note that you must not ask for information that were already mentioned before.''',
                    template_pm_test_iteration,
                    micro_service_initial_description=f'''Microservice original description: 
```
{original_task}
```
Microservice refined description: 
```
{self.microservice_specification.task}
```
''',
                )
                break
            except self.TaskRefinementException as e:

                print_colored('', f'{pm.emoji} Could not refine your requirements. Please try again...', 'red')

        print(f'''
{pm.emoji} 👍 Great, I will handover the following requirements to our engineers:
Description of the microservice:
{self.microservice_specification.task}
Test scenario:
{self.microservice_specification.test}
''')

    def refine_requirements(self, pm, messages, refinement_type, custom_suffix, template_pm_iteration,
                            micro_service_initial_description=None):
        user_input = self.microservice_specification.task
        num_parsing_tries = 0
        while True:
            conversation = self.gpt_session.get_conversation(messages,
                                                             print_stream=os.environ['VERBOSE'].lower() == 'true',
                                                             print_costs=False)
            agent_response_raw = conversation.chat(
                template_pm_iteration.format(
                    custom_suffix=custom_suffix,
                    micro_service_initial_description=micro_service_initial_description if len(messages) == 1 else '',
                ),
                role='user'
            )
            messages.append(HumanMessage(content=user_input))
            agent_question = self.extract_content_from_result(agent_response_raw, 'prompt.json',
                                                              can_contain_code_block=False)
            final = self.extract_content_from_result(agent_response_raw, 'final.json', can_contain_code_block=False)
            if final:
                messages.append(AIMessage(content=final))
                setattr(self.microservice_specification, refinement_type, final)
                break
            elif agent_question:
                question_parsed = json.loads(agent_question)['question']
                messages.append(AIMessage(content=question_parsed))
                user_input = self.get_user_input(pm, question_parsed)
            else:
                if num_parsing_tries > 2:
                    raise self.TaskRefinementException()
                num_parsing_tries += 1
                messages.append(AIMessage(content=agent_response_raw))
                messages.append(
                    SystemMessage(content='You did not put your answer into the right format using *** and ```.'))

    @staticmethod
    def get_user_input(employee, prompt_to_user):
        val = input(f'{employee.emoji}❓ {prompt_to_user}\nyou: ')
        print()
        while not val:
            val = input('you: ')
        return val

    @staticmethod
    def replace_with_gpt_3_5_turbo_if_possible(pkg):
        if pkg in LANGUAGE_PACKAGES:
            return 'gpt_3_5_turbo'
        return pkg

    @staticmethod
    def filter_packages_list(packages_list):
        # filter out complete package lists
        packages_list = [
            packages for packages in packages_list if all([
                pkg not in BLACKLISTED_PACKAGES  # no package is allowed to be blacklisted
                for pkg in packages
            ])
        ]
        # filter out single packages
        packages_list = [
            [
                package for package in packages
                if (package not in UNNECESSARY_PACKAGES)
                   and (  # all packages must be on pypi or it is gpt_3_5_turbo
                           is_package_on_pypi(package)
                           or package == 'gpt_3_5_turbo'
                   )
            ] for packages in packages_list
        ]
        return packages_list
