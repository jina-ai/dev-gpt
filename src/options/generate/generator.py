import os
import random
import re

from src.apis import gpt
from src.constants import FILE_AND_TAG_PAIRS, NUM_IMPLEMENTATION_STRATEGIES, MAX_DEBUGGING_ITERATIONS
from src.apis.jina_cloud import process_error_message, push_executor
from src.options.generate.prompt_tasks import general_guidelines, chain_of_thought_creation, executor_file_task, \
    not_allowed, chain_of_thought_optimization, test_executor_file_task, requirements_file_task, docker_file_task
from src.utils.io import persist_file, get_all_microservice_files_with_content, get_microservice_path
from src.utils.string_tools import print_colored


class Generator:
    def __init__(self, model='gpt-4'):
        self.gpt_session = gpt.GPTSession(model=model)

    def extract_content_from_result(self, plain_text, file_name, match_single_block=False):
        pattern = fr"^\*\*{file_name}\*\*\n```(?:\w+\n)?([\s\S]*?)```"
        match = re.search(pattern, plain_text, re.MULTILINE)
        if match:
            return match.group(1).strip()
        else:
            # Check for a single code block
            single_code_block_pattern = r"^```(?:\w+\n)?([\s\S]*?)```"
            single_code_block_match = re.findall(single_code_block_pattern, plain_text, re.MULTILINE)
            if match_single_block and len(single_code_block_match) == 1:
                return single_code_block_match[0].strip()
            else:
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

    def files_to_string(self, file_name_to_content):
        all_microservice_files_string = ''
        for file_name, tag in FILE_AND_TAG_PAIRS:
            if file_name in file_name_to_content:
                all_microservice_files_string += f'**{file_name}**\n'
                all_microservice_files_string += f'```{tag}\n'
                all_microservice_files_string += file_name_to_content[file_name]
                all_microservice_files_string += '\n```'
        return all_microservice_files_string

    def wrap_content_in_code_block(self, microservice_content, file_name, tag):
        return f'**{file_name}**\n```{tag}\n{microservice_content}\n```\n\n'

    def generate_microservice(
            self,
            description,
            test,
            path,
            microservice_name,
            package,
            num_approach,
            is_chain_of_thought=False,
    ):
        MICROSERVICE_FOLDER_v1 = get_microservice_path(path, microservice_name, package, num_approach, 1)
        os.makedirs(MICROSERVICE_FOLDER_v1)

        print_colored('', '############# Microservice #############', 'red')
        user_query = (
                general_guidelines()
                + executor_file_task(microservice_name, description, test, package)
                + '\n\n' + chain_of_thought_creation()
        )
        conversation = self.gpt_session.get_conversation()
        microservice_content_raw = conversation.query(user_query)
        if is_chain_of_thought:
            microservice_content_raw = conversation.query(
                f"General rules: " + not_allowed() + chain_of_thought_optimization('python', 'microservice.py'))
        microservicer_content = self.extract_content_from_result(executor_content_raw, 'microservice.py', match_single_block=True)
        if microservice_content == '':
            microservice_content_raw = conversation.query('Please add the executor code.')
            microservice_content = self.extract_content_from_result(
                microservice_content_raw, 'microservice.py', match_single_block=True
            )
        persist_file(microservice_content, os.path.join(MICROSERVICE_FOLDER_v1, 'microservice.py'))

        print_colored('', '############# Test Microservice #############', 'red')
        user_query = (
                general_guidelines()
                + self.wrap_content_in_code_block(microservice_content, 'microservice.py', 'python')
                + test_executor_file_task(microservice_name, test)
        )
        conversation = self.gpt_session.get_conversation()
        test_microservice_content_raw = conversation.query(user_query)
        if is_chain_of_thought:
            test_microservice_content_raw = conversation.query(
                f"General rules: " + not_allowed() +
                chain_of_thought_optimization('python', 'test_microservice.py')
                + "Don't add any additional tests. "
            )
        microservice_content = self.extract_content_from_result(
            microservice_content_raw, 'microservice.py', match_single_block=True
        )
        persist_file(microservice_content, os.path.join(MICROSERVICE_FOLDER_v1, 'test_microservice.py'))

        print_colored('', '############# Requirements #############', 'red')
        requirements_path = os.path.join(MICROSERVICE_FOLDER_v1, 'requirements.txt')
        user_query = (
                general_guidelines()
                + self.wrap_content_in_code_block(microservice_content, 'microservice.py', 'python')
                + self.wrap_content_in_code_block(test_microservice_content, 'test_microservice.py', 'python')
                + requirements_file_task()
        )
        conversation = self.gpt_session.get_conversation()
        requirements_content_raw = conversation.query(user_query)
        if is_chain_of_thought:
            requirements_content_raw = conversation.query(
                chain_of_thought_optimization('', requirements_path) + "Keep the same version of jina ")

        requirements_content = self.extract_content_from_result(requirements_content_raw, 'requirements.txt', match_single_block=True)
        persist_file(requirements_content, requirements_path)

        print_colored('', '############# Dockerfile #############', 'red')
        user_query = (
                general_guidelines()
                + self.wrap_content_in_code_block(microservice_content, 'microservice.py', 'python')
                + self.wrap_content_in_code_block(test_microservice_content, 'test_microservice.py', 'python')
                + self.wrap_content_in_code_block(requirements_content, 'requirements.txt', '')
                + docker_file_task()
        )
        conversation = self.gpt_session.get_conversation()
        dockerfile_content_raw = conversation.query(user_query)
        if is_chain_of_thought:
            dockerfile_content_raw = conversation.query(
                f"General rules: " + not_allowed() + chain_of_thought_optimization('dockerfile', 'Dockerfile'))
        dockerfile_content = self.extract_content_from_result(dockerfile_content_raw, 'Dockerfile', match_single_block=True)
        persist_file(dockerfile_content, os.path.join(MICROSERVICE_FOLDER_v1, 'Dockerfile'))

        self.write_config_yml(microservice_name, MICROSERVICE_FOLDER_v1)
        print('First version of the microservice generated. Start iterating on it to make the tests pass...')

    def generate_playground(self, microservice_name, microservice_path):
        print_colored('', '############# Playground #############', 'red')

        file_name_to_content = get_all_microservice_files_with_content(microservice_path)
        user_query = (
                general_guidelines()
                + self.wrap_content_in_code_block(file_name_to_content['microservice.py'], 'microservice.py', 'python')
                + self.wrap_content_in_code_block(file_name_to_content['test_microservice.py'], 'test_microservice.py',
                                                  'python')
                + f'''
Create a playground for the executor {microservice_name} using streamlit.
The playground must look like it was made by a professional designer.
All the ui elements are well thought out to make them visually appealing and easy to use.
This is an example how you can connect to the executor assuming the document (d) is already defined:
```
from jina import Client, Document, DocumentArray
client = Client(host=host)
response = client.post('/', inputs=DocumentArray([d])) # always use '/'
print(response[0].text) # can also be blob in case of image/audio..., this should be visualized in the streamlit app
```
Note that the response will always be in response[0].text
Please provide the complete file with the exact same syntax to wrap the code.
The playground (app.py) must read the host from sys.argv because it will be started with a custom host: streamlit run app.py -- --host grpc://...
The playground (app.py) must not let the user configure the host on the ui.
'''
        )
        conversation = self.gpt_session.get_conversation([])
        conversation.query(user_query)
        playground_content_raw = conversation.query(chain_of_thought_optimization('python', 'app.py', 'the playground'))
        playground_content = self.extract_content_from_result(playground_content_raw, 'app.py', match_single_block=True)
        persist_file(playground_content, os.path.join(miicroservice_path, 'app.py'))


    def debug_microservice(self, path, microservice_name, num_approach, packages, description, test):
        error_before = ''
        for i in range(1, MAX_DEBUGGING_ITERATIONS):
            print('Debugging iteration', i)
            print('Trying to build the microservice. Might take a while...')
            previous_microservice_path = get_microservice_path(path, microservice_name, packages, num_approach, i)
            next_microservice_path = get_microservice_path(path, microservice_name, packages, num_approach, i + 1)
            log_hubble = push_executor(previous_microservice_path)
            error = process_error_message(log_hubble)
            if error:
                os.makedirs(next_microservice_path)
                file_name_to_content = self.get_all_microservice_files_with_content(previous_executor_path)

                is_dependency_issue = self.is_dependency_issue(error, file_name_to_content['Dockerfile'])

                if is_dependency_issue:
                    all_files_string = self.files_to_string({
                        key: val for key, val in file_name_to_content.items() if key in ['requirements.txt', 'Dockerfile']
                    })
                    user_query = (
                        f"Your task is to provide guidance on how to solve an error that occurred during the Docker "
                        f"build process. The error message is:\n{error}\nTo solve this error, you should first "
                        f"identify the type of error by examining the stack trace. Once you have identified the "
                        f"error, you should suggest how to solve it. Your response should include the files that "
                        f"need to be changed, but not files that don't need to be changed. For files that need to "
                        f"be changed, please provide the complete file with the exact same syntax to wrap the code.\n\n"
                        f"You are given the following files:\n\n{all_files_string}"
                    )
                else:
                    all_files_string = self.files_to_string(file_name_to_content)
                    user_query = (
                             f"General rules: " + not_allowed()
                            + f'Here is the description of the task the executor must solve:\n{description}'
                            + f'\n\nHere is the test scenario the executor must pass:\n{test}'
                            + f'Here are all the files I use:\n{all_files_string}'
                            + f'\n\nThis error happens during the docker build process:\n{error}\n\n'
                            + ((f'This is an error that is already fixed before:\n{error_before}\n\n') if error_before else '')
                            + 'Look at exactly at the stack trace. First, think about what kind of error is this? '
                              'Then think about possible reasons which might have caused it. Then suggest how to '
                              'solve it. Output the files that need change. '
                              "Don't output files that don't need change. If you output a file, then write the "
                              "complete file. Use the exact same syntax to wrap the code:\n"
                              f"**...**\n"
                              f"```...\n"
                              f"...code...\n"
                              f"```"
                    )

                conversation = self.gpt_session.get_conversation()
                returned_files_raw = conversation.query(user_query)
                for file_name, tag in FILE_AND_TAG_PAIRS:
                    updated_file = self.extract_content_from_result(returned_files_raw, file_name)
                    if updated_file and (not is_dependency_issue or file_name in ['requirements.txt', 'Dockerfile']):
                        file_name_to_content[file_name] = updated_file

                for file_name, content in file_name_to_content.items():
                    persist_file(content, os.path.join(next_microservice_path, file_name))
                error_before = error

            else:
                print('Successfully build microservice.')
                break
            if i == MAX_DEBUGGING_ITERATIONS - 1:
                raise self.MaxDebugTimeReachedException('Could not debug the microservice.')
        return get_microservice_path(path, microservice_name, packages, num_approach, i)

    class MaxDebugTimeReachedException(BaseException):
        pass

    def is_dependency_issue(self, error, docker_file: str):
        # a few heuristics to quickly jump ahead
        if any([error_message in error for error_message in ['AttributeError', 'NameError', 'AssertionError']]):
            return False

        conversation = self.gpt_session.get_conversation([])
        answer = conversation.query(
            f'Your task is to assist in identifying the root cause of a Docker build error for a python application. '
            f'The error message is as follows::\n\n{error}\n\n'
            f'The docker file is as follows:\n\n{docker_file}\n\n'
            f'Is this a dependency installation failure? Answer with "yes" or "no".'
        )
        return 'yes' in answer.lower()

    def generate_microservice_name(self, description):
        conversation = self.gpt_session.get_conversation()
        user_query = f'''
Generate a name for the executor matching the description:
"{description}"
The executor name must fulfill the following criteria:
- camel case
- start with a capital letter
- only consists of lower and upper case characters
- end with Executor.

The output is a the raw string wrapped into ``` and starting with **name.txt** like this:
**name.txt**
```
PDFParserExecutor
```
'''
        name_raw = conversation.query(user_query)
        name = self.extract_content_from_result(name_raw, 'name.txt')
        return name

    def get_possible_packages(self, description):
        print_colored('', '############# What package to use? #############', 'red')
        user_query = f'''
Here is the task description of the problme you need to solve:
"{description}"
First, write down all the subtasks you need to solve which require python packages.
For each subtask:
    Provide a list of 1 to 3 python packages you could use to solve the subtask. Prefer modern packages.
    For each package:
        Write down some non-obvious thoughts about the challenges you might face for the task and give multiple approaches on how you handle them.
        For example, there might be some packages you must not use because they do not obay the rules:
        {not_allowed()}
        Discuss the pros and cons for all of these packages.
Create a list of package subsets that you could use to solve the task.
The list is sorted in a way that the most promising subset of packages is at the top.
The maximum length of the list is 5.

The output must be a list of lists wrapped into ``` and starting with **packages.csv** like this:
**packages.csv**
```
package1,package2
package2,package3,...
...
```
'''
        conversation = self.gpt_session.get_conversation()
        packages_raw = conversation.query(user_query)
        packages_csv_string = self.extract_content_from_result(packages_raw, 'packages.csv')
        packages = [package.split(',') for package in packages_csv_string.split('\n')]
        packages = packages[:NUM_IMPLEMENTATION_STRATEGIES]
        return packages

    def generate(self, description, test, microservice_path):
        generated_name = self.generate_microservice_name(description)
        microservice_name = f'{generated_name}{random.randint(0, 10_000_000)}'
        packages_list = self.get_possible_packages(description)
        for num_approach, packages in enumerate(packages_list):
            try:
                self.generate_microservice(description, test, microservice_path, microservice_name, packages, num_approach)
                final_version_path = self.debug_microservice(microservice_path, microservice_name, num_approach, packages, description, test)
                self.generate_playground(microservice_name, final_version_path)
            except self.MaxDebugTimeReachedException:
                print('Could not debug the Microservice.')
                continue
            print(f'''
You can now run or deploy your microservice:
gptdeploy run --path {microservice_path}
gptdeploy deploy --path {microservice_path}
'''
                  )
            break

