import os
import random
import re

from src.apis import gpt
from src.apis.jina_cloud import process_error_message, push_executor
from src.constants import FILE_AND_TAG_PAIRS, NUM_IMPLEMENTATION_STRATEGIES, MAX_DEBUGGING_ITERATIONS, \
    PROBLEMATIC_PACKAGES, EXECUTOR_FILE_NAME, EXECUTOR_FILE_TAG, TEST_EXECUTOR_FILE_NAME, TEST_EXECUTOR_FILE_TAG, \
    REQUIREMENTS_FILE_NAME, REQUIREMENTS_FILE_TAG, DOCKER_FILE_NAME, DOCKER_FILE_TAG
from src.options.generate.templates import template_generate_microservice_name, template_generate_possible_packages, \
    template_solve_code_issue, \
    template_solve_dependency_issue, template_is_dependency_issue, template_generate_playground, \
    template_generate_executor, template_generate_test, template_generate_requirements, template_generate_dockerfile, \
    template_chain_of_thought, template_summarize_error
from src.utils.io import persist_file, get_all_microservice_files_with_content, get_microservice_path
from src.utils.string_tools import print_colored


class Generator:
    def __init__(self, task_description, test_description, model='gpt-4'):
        self.gpt_session = gpt.GPTSession(task_description, test_description, model=model)
        self.task_description = task_description
        self.test_description = test_description

    def extract_content_from_result(self, plain_text, file_name, match_single_block=False):
        pattern = fr"^\*\*{file_name}\*\*\n```(?:\w+\n)?([\s\S]*?)```"
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

    def write_config_yml(self, microservice_name, dest_folder):
        config_content = f'''
jtype: {microservice_name}
py_modules:
  - microservice.py
metas:
  name: {microservice_name}
'''
        with open(os.path.join(dest_folder, 'config.yml'), 'w') as f:
            f.write(config_content)

    def files_to_string(self, file_name_to_content, restrict_keys=None):
        all_microservice_files_string = ''
        for file_name, tag in FILE_AND_TAG_PAIRS:
            if file_name in file_name_to_content and (not restrict_keys or file_name in restrict_keys):
                all_microservice_files_string += f'**{file_name}**\n```{tag}\n{file_name_to_content[file_name]}\n```\n\n'
        return all_microservice_files_string.strip()

    def generate_microservice(
            self,
            path,
            microservice_name,
            packages,
            num_approach,
    ):
        MICROSERVICE_FOLDER_v1 = get_microservice_path(path, microservice_name, packages, num_approach, 1)
        os.makedirs(MICROSERVICE_FOLDER_v1)

        print_colored('', '\n############# Microservice #############', 'blue')
        conversation = self.gpt_session.get_conversation()
        microservice_content_raw = conversation.chat(
            template_generate_executor.format(
                microservice_name=microservice_name,
                microservice_description=self.task_description,
                test=self.test_description,
                packages=packages,
                file_name_purpose=EXECUTOR_FILE_NAME,
                tag_name=EXECUTOR_FILE_TAG,
                file_name=EXECUTOR_FILE_NAME,
            )
        )
        microservice_content = self.extract_content_from_result(
            microservice_content_raw, 'microservice.py', match_single_block=True
        )
        if microservice_content == '':
            microservice_content_raw = conversation.chat('You must add the executor code.')
            microservice_content = self.extract_content_from_result(
                microservice_content_raw, 'microservice.py', match_single_block=True
            )
        persist_file(microservice_content, os.path.join(MICROSERVICE_FOLDER_v1, 'microservice.py'))

        print_colored('', '\n############# Test Microservice #############', 'blue')
        conversation = self.gpt_session.get_conversation()
        test_microservice_content_raw = conversation.chat(
            template_generate_test.format(
                code_files_wrapped=self.files_to_string({'microservice.py': microservice_content}),
                microservice_name=microservice_name,
                test_description=self.test_description,
                file_name_purpose=TEST_EXECUTOR_FILE_NAME,
                tag_name=TEST_EXECUTOR_FILE_TAG,
                file_name=TEST_EXECUTOR_FILE_NAME,
            )
        )
        test_microservice_content = self.extract_content_from_result(
            test_microservice_content_raw, 'microservice.py', match_single_block=True
        )
        persist_file(test_microservice_content, os.path.join(MICROSERVICE_FOLDER_v1, 'test_microservice.py'))

        print_colored('', '\n############# Requirements #############', 'blue')
        requirements_path = os.path.join(MICROSERVICE_FOLDER_v1, 'requirements.txt')
        conversation = self.gpt_session.get_conversation()
        requirements_content_raw = conversation.chat(
            template_generate_requirements.format(
                code_files_wrapped=self.files_to_string(
                    {'microservice.py': microservice_content, 'test_microservice.py': test_microservice_content}
                ),
                file_name_purpose=REQUIREMENTS_FILE_NAME,
                file_name=REQUIREMENTS_FILE_NAME,
                tag_name=REQUIREMENTS_FILE_TAG,
            )
        )

        requirements_content = self.extract_content_from_result(requirements_content_raw, 'requirements.txt',
                                                                match_single_block=True)
        persist_file(requirements_content, requirements_path)

        print_colored('', '\n############# Dockerfile #############', 'blue')
        conversation = self.gpt_session.get_conversation()
        dockerfile_content_raw = conversation.chat(
            template_generate_dockerfile.format(
                code_files_wrapped=self.files_to_string(
                    {
                        'microservice.py': microservice_content,
                        'test_microservice.py': test_microservice_content,
                        'requirements.txt': requirements_content,
                    }
                ),
                file_name_purpose=DOCKER_FILE_NAME,
                file_name=DOCKER_FILE_NAME,
                tag_name=DOCKER_FILE_TAG,
            )
        )
        dockerfile_content = self.extract_content_from_result(
            dockerfile_content_raw, 'Dockerfile', match_single_block=True
        )
        persist_file(dockerfile_content, os.path.join(MICROSERVICE_FOLDER_v1, 'Dockerfile'))

        self.write_config_yml(microservice_name, MICROSERVICE_FOLDER_v1)
        print('\nFirst version of the microservice generated. Start iterating on it to make the tests pass...')

    def generate_playground(self, microservice_name, microservice_path):
        print_colored('', '\n############# Playground #############', 'blue')

        file_name_to_content = get_all_microservice_files_with_content(microservice_path)
        conversation = self.gpt_session.get_conversation([])
        conversation.chat(
            template_generate_playground.format(
                code_files_wrapped=self.files_to_string(file_name_to_content, ['microservice.py', 'test_microservice.py']),
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
        persist_file(playground_content, os.path.join(microservice_path, 'app.py'))

    def debug_microservice(self, path, microservice_name, num_approach, packages):
        for i in range(1, MAX_DEBUGGING_ITERATIONS):
            print('Debugging iteration', i)
            print('Trying to debug the microservice. Might take a while...')
            previous_microservice_path = get_microservice_path(path, microservice_name, packages, num_approach, i)
            next_microservice_path = get_microservice_path(path, microservice_name, packages, num_approach, i + 1)
            log_hubble = push_executor(previous_microservice_path)
            error = process_error_message(log_hubble)
            if error:
                print('An error occurred during the build process. Feeding the error back to the assistent...')
                self.do_debug_iteration(error, next_microservice_path, previous_microservice_path)
                if i == MAX_DEBUGGING_ITERATIONS - 1:
                    raise self.MaxDebugTimeReachedException('Could not debug the microservice.')
            else:
                print('Successfully build microservice.')
                break

        return get_microservice_path(path, microservice_name, packages, num_approach, i)

    def do_debug_iteration(self, error, next_microservice_path, previous_microservice_path):
        os.makedirs(next_microservice_path)
        file_name_to_content = get_all_microservice_files_with_content(previous_microservice_path)

        summarized_error = self.summarize_error(error)
        is_dependency_issue = self.is_dependency_issue(error, file_name_to_content['Dockerfile'])
        if is_dependency_issue:
            all_files_string = self.files_to_string({
                key: val for key, val in file_name_to_content.items() if
                key in ['requirements.txt', 'Dockerfile']
            })
            user_query = template_solve_dependency_issue.format(
                description=self.task_description, summarized_error=summarized_error, all_files_string=all_files_string,
            )
        else:
            user_query = template_solve_code_issue.format(
                description=self.task_description, summarized_error=summarized_error, all_files_string=self.files_to_string(file_name_to_content),
            )
        conversation = self.gpt_session.get_conversation()
        returned_files_raw = conversation.chat(user_query)
        for file_name, tag in FILE_AND_TAG_PAIRS:
            updated_file = self.extract_content_from_result(returned_files_raw, file_name)
            if updated_file and (not is_dependency_issue or file_name in ['requirements.txt', 'Dockerfile']):
                file_name_to_content[file_name] = updated_file
                print(f'Updated {file_name}')
        for file_name, content in file_name_to_content.items():
            persist_file(content, os.path.join(next_microservice_path, file_name))

    class MaxDebugTimeReachedException(BaseException):
        pass

    def is_dependency_issue(self, error, docker_file: str):
        # a few heuristics to quickly jump ahead
        if any([error_message in error for error_message in ['AttributeError', 'NameError', 'AssertionError']]):
            return False

        print_colored('', 'Is it a dependency issue?', 'blue')
        conversation = self.gpt_session.get_conversation([])
        answer = conversation.chat(template_is_dependency_issue.format(error=error, docker_file=docker_file))
        return 'yes' in answer.lower()

    def generate_microservice_name(self, description):
        conversation = self.gpt_session.get_conversation()
        name_raw = conversation.chat(template_generate_microservice_name.format(description=description))
        name = self.extract_content_from_result(name_raw, 'name.txt')
        return name

    def get_possible_packages(self):
        print_colored('', '############# What packages to use? #############', 'blue')
        conversation = self.gpt_session.get_conversation()
        packages_raw = conversation.chat(
            template_generate_possible_packages.format(description=self.task_description)
        )
        packages_csv_string = self.extract_content_from_result(packages_raw, 'packages.csv')
        packages_list = [[pkg.strip() for pkg in packages_string.split(',')] for packages_string in packages_csv_string.split('\n')]
        packages_list = packages_list[:NUM_IMPLEMENTATION_STRATEGIES]
        return packages_list

    def generate(self, microservice_path):
        generated_name = self.generate_microservice_name(self.task_description)
        microservice_name = f'{generated_name}{random.randint(0, 10_000_000)}'
        packages_list = self.get_possible_packages()
        packages_list = [
            packages for packages in packages_list if len(set(packages).intersection(set(PROBLEMATIC_PACKAGES))) == 0
        ]
        for num_approach, packages in enumerate(packages_list):
            try:
                self.generate_microservice(microservice_path, microservice_name, packages, num_approach)
                final_version_path = self.debug_microservice(
                    microservice_path, microservice_name, num_approach, packages
                )
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
gptdeploy run --path {microservice_path}
gptdeploy deploy --path {microservice_path}
'''
                  )
            break

    def summarize_error(self, error):
        conversation = self.gpt_session.get_conversation([])
        error_summary = conversation.chat(template_summarize_error.format(error=error))
        return error_summary
