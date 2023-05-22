import json
import os
import random
import re
import shutil
import sys
from typing import Callable
from typing import List, Text, Optional

from langchain import PromptTemplate
from langchain.schema import SystemMessage, AIMessage
from pydantic.dataclasses import dataclass

from dev_gpt.apis import gpt
from dev_gpt.apis.gpt import _GPTConversation, ask_gpt
from dev_gpt.apis.jina_cloud import process_error_message, push_executor, is_executor_in_hub
from dev_gpt.apis.pypi import is_package_on_pypi, clean_requirements_txt
from dev_gpt.constants import FILE_AND_TAG_PAIRS, NUM_IMPLEMENTATION_STRATEGIES, MAX_DEBUGGING_ITERATIONS, \
    BLACKLISTED_PACKAGES, EXECUTOR_FILE_NAME, TEST_EXECUTOR_FILE_NAME, TEST_EXECUTOR_FILE_TAG, \
    REQUIREMENTS_FILE_NAME, REQUIREMENTS_FILE_TAG, DOCKER_FILE_NAME, IMPLEMENTATION_FILE_NAME, \
    IMPLEMENTATION_FILE_TAG, LANGUAGE_PACKAGES, UNNECESSARY_PACKAGES, DOCKER_BASE_IMAGE_VERSION, SEARCH_PACKAGES, \
    INDICATOR_TO_IMPORT_STATEMENT
from dev_gpt.options.generate.pm.pm import PM
from dev_gpt.options.generate.templates_user import template_generate_microservice_name, \
    template_generate_possible_packages, \
    template_implement_solution_code_issue, \
    template_solve_pip_dependency_issue, template_is_dependency_issue, template_generate_playground, \
    template_generate_function_constructor, template_generate_test, template_generate_requirements, \
    template_chain_of_thought, template_summarize_error, \
    template_solve_apt_get_dependency_issue, \
    template_suggest_solutions_code_issue, template_was_error_seen_before, \
    template_was_solution_tried_before, response_format_was_error_seen_before, \
    response_format_was_solution_tried_before, response_format_suggest_solutions
from dev_gpt.utils.io import persist_file, get_all_microservice_files_with_content, get_microservice_path
from dev_gpt.utils.string_tools import print_colored


@dataclass
class TaskSpecification:
    task: Optional[Text]
    test: Optional[Text]


class Generator:
    def __init__(self, task_description, path, model='gpt-4', self_healing=True):
        self.gpt_session = gpt.GPTSession(os.path.join(path, 'log.json'), model=model)
        self.microservice_specification = TaskSpecification(task=task_description, test=None)
        self.self_healing = self_healing
        self.microservice_root_path = path
        self.microservice_name = None
        self.previous_microservice_path = None
        self.cur_microservice_path = None
        self.previous_errors = []
        self.previous_solutions = []

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
            destination_folder: str = None,
            file_name_s: List[str] = None,
            parse_result_fn: Callable = None,
            use_custom_system_message: bool = True,
            response_format_example: str = None,
            post_process_fn: Callable = None,
            **template_kwargs
    ):
        """This function generates file(s) using the given template and persists it/them in the given destination folder.
        It also returns the generated content as a dictionary mapping file_name to its content.

        Args:
            section_title (str): The title of the section to be printed in the console.
            template (PromptTemplate): The template to be used for generating the file(s).
            destination_folder (str): The destination folder where the generated file(s) should be persisted. If None,
                the current microservice path is used. Defaults to None.
            file_name_s (List[str], optional): The name of the file(s) to be generated. Defaults to None.
            parse_result_fn (Callable, optional): A function that parses the generated content and returns a dictionary
                mapping file_name to its content. If no content could be extract, it returns an empty dictionary.
                Defaults to None. If None, default parsing is used which uses the file_name to extract from the generated content.
            use_custom_system_message (bool, optional): whether to use custom system message or not. Defaults to True.
            **template_kwargs: The keyword arguments to be passed to the template.
        """
        if destination_folder is None:
            destination_folder = self.cur_microservice_path

        if parse_result_fn is None:
            parse_result_fn = self.get_default_parse_result_fn(file_name_s)

        print_colored('', f'\n\n############# {section_title} #############', 'blue')
        if use_custom_system_message:
            system_introduction_message = _GPTConversation._create_system_message(
                self.microservice_specification.task,
                self.microservice_specification.test
            )
        else:
            system_introduction_message = SystemMessage(content='You are a helpful assistant.')
        conversation = self.gpt_session.get_conversation(
            messages=[system_introduction_message] if use_custom_system_message else []
        )
        template_kwargs = {k: v for k, v in template_kwargs.items() if k in template.input_variables}
        if 'file_name' in template.input_variables and len(file_name_s) == 1:
            template_kwargs['file_name'] = file_name_s[0]
        content_raw = conversation.chat(
            template.format(
                **template_kwargs
            )
        )
        content = parse_result_fn(content_raw)
        if post_process_fn is not None:
            content = post_process_fn(content)
        if content == {}:
            conversation = self.gpt_session.get_conversation(
                messages=[SystemMessage(content='You are a helpful assistant.'), AIMessage(content=content_raw)]
            )
            if response_format_example is not None:
                file_wrapping_example = response_format_example
            elif len(file_name_s) == 1:
                file_ending = file_name_s[0].split('.')[-1]
                if file_ending == 'py':
                    tag = 'python'
                elif file_ending == 'json':
                    tag = 'json'
                else:
                    tag = ''
                file_wrapping_example = f'''**{file_name_s[0]}**
```{tag}
<content_of_file>
```'''
            else:
                file_wrapping_example = '''**file_name.file_ending**
```<json|py|...
<content_of_file>
```'''
            content_raw = conversation.chat(
                'Based on your previous response, only output the content' + (f' for `{file_name_s[0]}`' if len(file_name_s) == 1 else '') +
                '. Like this:\n' +
                file_wrapping_example
            )
            content = parse_result_fn(content_raw)
        for _file_name, _file_content in content.items():
            persist_file(_file_content, os.path.join(destination_folder, _file_name))
        return content

    def generate_microservice(
            self,
            packages,
            num_approach,
    ):
        self.cur_microservice_path = get_microservice_path(
            self.microservice_root_path, self.microservice_name, packages, num_approach, 1
        )
        os.makedirs(self.cur_microservice_path)

        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'jina_wrapper.py'), 'r', encoding='utf-8') as f:
            microservice_executor_boilerplate = f.read()
        microservice_executor_code = microservice_executor_boilerplate \
            .replace('class DevGPTExecutor(Executor):', f'class {self.microservice_name}(Executor):')
        persist_file(microservice_executor_code, os.path.join(self.cur_microservice_path, EXECUTOR_FILE_NAME))

        for additional_file in ['google_custom_search.py', 'gpt_3_5_turbo.py']:
            with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', additional_file), 'r', encoding='utf-8') as f:
                persist_file(f.read(), os.path.join(self.cur_microservice_path, additional_file))

        is_using_gpt_3_5_turbo = 'gpt_3_5_turbo' in packages or 'gpt-3-5-turbo' in packages
        is_using_google_custom_search = 'google_custom_search' in packages or 'google-custom-search' in packages
        microservice_content = self.generate_and_persist_file(
            section_title='Microservice',
            template=template_generate_function_constructor(is_using_gpt_3_5_turbo, is_using_google_custom_search),
            microservice_description=self.microservice_specification.task,
            test_description=self.microservice_specification.test,
            packages=packages,
            file_name_purpose=IMPLEMENTATION_FILE_NAME,
            tag_name=IMPLEMENTATION_FILE_TAG,
            file_name_s=[IMPLEMENTATION_FILE_NAME],
            post_process_fn=self.add_missing_imports_post_process_fn,
        )[IMPLEMENTATION_FILE_NAME]

        test_microservice_content = self.generate_and_persist_file(
            'Test Microservice',
            template_generate_test,
            code_files_wrapped=self.files_to_string({EXECUTOR_FILE_NAME: microservice_content}),
            microservice_name=self.microservice_name,
            microservice_description=self.microservice_specification.task,
            test_description=self.microservice_specification.test,
            file_name_purpose=TEST_EXECUTOR_FILE_NAME,
            tag_name=TEST_EXECUTOR_FILE_TAG,
            file_name_s=[TEST_EXECUTOR_FILE_NAME],
            post_process_fn=self.add_missing_imports_post_process_fn,
        )[TEST_EXECUTOR_FILE_NAME]

        self.generate_and_persist_file(
            'Requirements',
            template_generate_requirements,
            code_files_wrapped=self.files_to_string({
                IMPLEMENTATION_FILE_NAME: microservice_content,
                TEST_EXECUTOR_FILE_NAME: test_microservice_content,
            }),
            file_name_purpose=REQUIREMENTS_FILE_NAME,
            file_name_s=[REQUIREMENTS_FILE_NAME],
            parse_result_fn=self.parse_result_fn_requirements,
            tag_name=REQUIREMENTS_FILE_TAG,
        )

        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'Dockerfile'), 'r',
                  encoding='utf-8') as f:
            docker_file_template_lines = f.readlines()
        docker_file_template_lines = [
            line.replace('{{APT_GET_PACKAGES}}', '').replace('{{DOCKER_BASE_IMAGE_VERSION}}', DOCKER_BASE_IMAGE_VERSION)
            for line in docker_file_template_lines
        ]
        docker_file_content = ''.join(docker_file_template_lines)
        persist_file(docker_file_content, os.path.join(self.cur_microservice_path, 'Dockerfile'))

        self.write_config_yml(self.microservice_name, self.cur_microservice_path)

        print('\nFirst version of the microservice generated. Start iterating on it to make the tests pass...')


    def add_missing_imports_post_process_fn(self, content_dict: dict):
        for file_name, file_content in content_dict.items():
            file_content = self.add_missing_imports_for_file(file_content)
            content_dict[file_name] = file_content
        return content_dict

    def add_missing_imports_for_file(self, file_content):
        for indicator, import_statement in INDICATOR_TO_IMPORT_STATEMENT.items():
            if indicator in file_content and import_statement not in file_content:
                file_content = f'{import_statement}\n{file_content}'
        return file_content

    @staticmethod
    def read_docker_template():
        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'microservice', 'Dockerfile'), 'r', encoding='utf-8') as f:
            return f.read()

    def parse_result_fn_dockerfile(self, content_raw: str):
        json_string = self.extract_content_from_result(content_raw, 'apt-get-packages.json', match_single_block=True)
        packages = ' '.join(json.loads(json_string)['packages'])

        docker_file_template = self.read_docker_template()
        return {DOCKER_FILE_NAME: docker_file_template.replace('{{APT_GET_PACKAGES}}', '{APT_GET_PACKAGES}').replace('{{DOCKER_BASE_IMAGE_VERSION}}', DOCKER_BASE_IMAGE_VERSION).format(
            APT_GET_PACKAGES=packages)}

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

    def generate_playground(self):
        print_colored('', '\n\n############# Playground #############', 'blue')

        with open(os.path.join(os.path.dirname(__file__), 'static_files', 'gateway', 'app_template.py'), 'r', encoding='utf-8') as f:
            playground_template = f.read()
        file_name_to_content = get_all_microservice_files_with_content(self.cur_microservice_path)
        conversation = self.gpt_session.get_conversation()
        conversation.chat(
            template_generate_playground.format(
                code_files_wrapped=self.files_to_string(file_name_to_content, ['test_microservice.py', 'microservice.py']),
                microservice_name=self.microservice_name,
                playground_template=playground_template,
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
        playground_content = self.add_missing_imports_for_file(playground_content)

        gateway_path = os.path.join(self.cur_microservice_path, 'gateway')
        shutil.copytree(os.path.join(os.path.dirname(__file__), 'static_files', 'gateway'), gateway_path)
        persist_file(playground_content, os.path.join(gateway_path, 'app.py'))

        # fill-in name of microservice
        gateway_name = f'Gateway{self.microservice_name}'
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
            raise Exception(f'{self.microservice_name} not in hub. Hubble logs: {hubble_log}')

    def debug_microservice(self, num_approach, packages, self_healing):
        for i in range(1, MAX_DEBUGGING_ITERATIONS):
            print('Debugging iteration', i)
            print('Trying to debug the microservice. Might take a while...')
            clean_requirements_txt(self.cur_microservice_path)
            log_hubble = push_executor(self.cur_microservice_path)
            error = process_error_message(log_hubble)
            if error:
                if not self_healing:
                    print(error)
                    raise Exception('Self-healing is disabled. Please fix the error manually.')
                print('An error occurred during the build process. Feeding the error back to the assistant...')
                self.previous_microservice_path = self.cur_microservice_path
                self.cur_microservice_path = get_microservice_path(
                    self.microservice_root_path, self.microservice_name, packages, num_approach, i + 1
                )
                os.makedirs(self.cur_microservice_path)
                self.do_debug_iteration(error)
                if i == MAX_DEBUGGING_ITERATIONS - 1:
                    raise self.MaxDebugTimeReachedException('Could not debug the microservice.')
            else:
                # at the moment, there can be cases where no error log is extracted but the executor is still not published
                # it leads to problems later on when someone tries a run or deployment
                if is_executor_in_hub(self.microservice_name):
                    print('Successfully build microservice.')
                    break
                else:
                    raise Exception(f'{self.microservice_name} not in hub. Hubble logs: {log_hubble}')

    def do_debug_iteration(self, error):
        file_name_to_content = get_all_microservice_files_with_content(self.previous_microservice_path)
        for file_name, content in file_name_to_content.items():
            persist_file(content, os.path.join(self.cur_microservice_path, file_name))

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
                file_name_s=['apt-get-packages.json'],
                parse_result_fn=self.parse_result_fn_dockerfile,
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
                    file_name_s=[REQUIREMENTS_FILE_NAME],
                    summarized_error=summarized_error,
                    all_files_string=dock_req_string,
                )
            else:
                all_files_string = self.files_to_string(
                    {key: val for key, val in file_name_to_content.items() if key != EXECUTOR_FILE_NAME}
                )

                suggested_solution = self.generate_solution_suggestion(summarized_error, all_files_string)

                self.generate_and_persist_file(
                    section_title='Implementing suggestion solution for code issue',
                    template=template_implement_solution_code_issue,
                    file_name_s=[IMPLEMENTATION_FILE_NAME, TEST_EXECUTOR_FILE_NAME, REQUIREMENTS_FILE_NAME],
                    summarized_error=summarized_error,
                    task_description=self.microservice_specification.task,
                    test_description=self.microservice_specification.test,
                    all_files_string=all_files_string,
                    suggested_solution=suggested_solution,
                )

                self.previous_errors.append(summarized_error)
                self.previous_solutions.append(suggested_solution)

    def generate_solution_suggestion(self, summarized_error, all_files_string):
        suggested_solutions = json.loads(
            self.generate_and_persist_file(
                section_title='Suggest solution for code issue',
                template=template_suggest_solutions_code_issue,
                file_name_s=['solutions.json'],
                summarized_error=summarized_error,
                task_description=self.microservice_specification.task,
                test_description=self.microservice_specification.test,
                all_files_string=all_files_string,
                response_format_example=response_format_suggest_solutions,
            )['solutions.json']
        )

        if len(self.previous_errors) > 0:
            was_error_seen_before = json.loads(
                self.generate_and_persist_file(
                    section_title='Check if error was seen before',
                    template=template_was_error_seen_before,
                    file_name_s=['was_error_seen_before.json'],
                    summarized_error=summarized_error,
                    previous_errors='- "' + f'"{os.linesep}- "'.join(self.previous_errors) + '"',
                    use_custom_system_message=False,
                    response_format_example=response_format_was_error_seen_before,
                )['was_error_seen_before.json']
            )['was_error_seen_before'].lower() == 'yes'

            suggested_solution = None
            if was_error_seen_before:
                for _num_solution in range(1, len(suggested_solutions) + 1):
                    _suggested_solution = suggested_solutions[str(_num_solution)]
                    was_solution_tried_before = json.loads(
                        self.generate_and_persist_file(
                            section_title='Check if solution was tried before',
                            template=template_was_solution_tried_before,
                            file_name_s=['will_lead_to_different_actions.json'],
                            tried_solutions='- "' + f'"{os.linesep}- "'.join(self.previous_solutions) + '"',
                            suggested_solution=_suggested_solution,
                            use_custom_system_message=False,
                            response_format_example=response_format_was_solution_tried_before,
                        )['will_lead_to_different_actions.json']
                    )['will_lead_to_different_actions'].lower() == 'no'
                    if not was_solution_tried_before:
                        suggested_solution = _suggested_solution
                        break
            else:
                suggested_solution = suggested_solutions['1']

            if suggested_solution is None:
                suggested_solution = f"solve error: {summarized_error}"
        else:
            suggested_solution = suggested_solutions['1']

        return suggested_solution

    class MaxDebugTimeReachedException(BaseException):
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
        return ask_gpt(template_generate_microservice_name, description=description)

    def get_possible_packages(self):
        print_colored('', '\n\n############# What packages to use? #############', 'blue')
        packages_json_string = self.generate_and_persist_file(
            section_title='Generate possible packages',
            template=template_generate_possible_packages,
            destination_folder=self.microservice_root_path,
            file_name_s=['strategies.json'],
            description=self.microservice_specification.task
        )['strategies.json']
        packages_list = [[pkg.strip().lower() for pkg in packages] for packages in json.loads(packages_json_string)]
        packages_list = [[self.replace_with_tool_if_possible(pkg) for pkg in packages] for packages in
                         packages_list]

        packages_list = self.filter_packages_list(packages_list)
        packages_list = self.remove_duplicates_from_packages_list(packages_list)
        packages_list = packages_list[:NUM_IMPLEMENTATION_STRATEGIES]
        return packages_list


    def generate(self):
        os.makedirs(self.microservice_root_path)
        self.microservice_specification.task, self.microservice_specification.test = PM().refine_specification(self.microservice_specification.task)
        generated_name = self.generate_microservice_name(self.microservice_specification.task)
        self.microservice_name = f'{generated_name}{random.randint(0, 10_000_000)}'
        packages_list = self.get_possible_packages()
        for num_approach, packages in enumerate(packages_list):
            try:
                self.generate_microservice(packages, num_approach)
                self.debug_microservice(num_approach, packages, self.self_healing)
                self.generate_playground()
            except self.MaxDebugTimeReachedException:
                print('Could not debug the Microservice with the approach:', packages)
                if num_approach == len(packages_list) - 1:
                    print_colored('',
                                  f'Could not debug the Microservice with any of the approaches: {packages} giving up.',
                                  'red')
                    return -1
                continue
            command = 'dev-gpt' if sys.argv[0] == 'dev-gpt' else 'python main.py'
            print(f'''
You can now run or deploy your microservice:
{command} run --path {self.microservice_root_path}
{command} deploy --path {self.microservice_root_path}
'''
                  )
            return 0

    def summarize_error(self, error):
        conversation = self.gpt_session.get_conversation()
        error_summary = conversation.chat(template_summarize_error.format(error=error))
        return error_summary


    @staticmethod
    def replace_with_tool_if_possible(pkg):
        if pkg in LANGUAGE_PACKAGES:
            return 'gpt_3_5_turbo'
        if pkg in SEARCH_PACKAGES:
            return 'google_custom_search'
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

    @staticmethod
    def remove_duplicates_from_packages_list(packages_list):
        return [list(set(packages)) for packages in packages_list]

#     def create_prototype_implementation(self):
#         microservice_py_lines = ['''\
# Class {microservice_name}:''']
#         for sub_task in self.pm.iterate_over_sub_tasks_pydantic(self.sub_task_tree):
#             microservice_py_lines.append(f'    {sub_task.python_fn_signature}')
#             microservice_py_lines.append(f'        """')
#             microservice_py_lines.append(f'        {sub_task.python_fn_docstring}')
#             microservice_py_lines.append(f'        """')
#             microservice_py_lines.append(f'        raise NotImplementedError')
#         microservice_py_str = '\n'.join(microservice_py_lines)
#         persist_file(os.path.join(self.microservice_root_path, 'microservice.py'), microservice_py_str)

