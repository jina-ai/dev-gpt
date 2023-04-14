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
    def __init__(self):
        self.gpt_session = gpt.GPTSession()

    def extract_content_from_result(self, plain_text, file_name):
        pattern = fr"^\*\*{file_name}\*\*\n```(?:\w+\n)?([\s\S]*?)```"
        match = re.search(pattern, plain_text, re.MULTILINE)
        if match:
            return match.group(1).strip()
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
                all_microservice_files_string += '\n```\n\n'
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
                + chain_of_thought_creation()
        )
        conversation = self.gpt_session.get_conversation()
        microservice_content_raw = conversation.query(user_query)
        if is_chain_of_thought:
            microservice_content_raw = conversation.query(
                f"General rules: " + not_allowed() + chain_of_thought_optimization('python', 'microservice.py'))
        microservice_content = self.extract_content_from_result(microservice_content_raw, 'microservice.py')

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
        test_microservice_content = self.extract_content_from_result(test_microservice_content_raw, 'test_microservice.py')
        persist_file(test_microservice_content, os.path.join(MICROSERVICE_FOLDER_v1, 'test_microservice.py'))

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

        requirements_content = self.extract_content_from_result(requirements_content_raw, 'requirements.txt')
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
        dockerfile_content = self.extract_content_from_result(dockerfile_content_raw, 'Dockerfile')
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
The playground must be started with a custom host: streamlit run app.py -- --host grpc://...
The playground must not let the user configure the --host grpc://... on the ui.
This is an example how you can connect to the executor assuming the document (d) is already defined:
from jina import Client, Document, DocumentArray
client = Client(host=host)
response = client.post('/', inputs=DocumentArray([d])) # always use '/'
print(response[0].text) # can also be blob in case of image/audio..., this should be visualized in the streamlit app
'''
        )
        conversation = self.gpt_session.get_conversation()
        conversation.query(user_query)
        playground_content_raw = conversation.query(
            f"General rules: " + not_allowed() + chain_of_thought_optimization('python', 'app.py'))
        playground_content = self.extract_content_from_result(playground_content_raw, 'app.py')
        persist_file(playground_content, os.path.join(microservice_path, 'app.py'))


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
                file_name_to_content = get_all_microservice_files_with_content(previous_microservice_path)
                all_files_string = self.files_to_string(file_name_to_content)
                user_query = (
                        f"General rules: " + not_allowed()
                        + 'Here is the description of the task the executor must solve:\n'
                        + description
                        + '\n\nHere is the test scenario the executor must pass:\n'
                        + test
                        + 'Here are all the files I use:\n'
                        + all_files_string
                        + (('This is an error that is already fixed before:\n'
                            + error_before) if error_before else '')
                        + '\n\nNow, I get the following error:\n'
                        + error + '\n'
                        + 'Think quickly about possible reasons the error might caused by. '
                          'Decide which files need to be changed. '
                          'Then output the files that need change. '
                          "Don't output files that don't need change. "
                          "If you output a file, then write the complete file. "
                          "Use the exact same syntax to wrap the code:\n"
                          f"**...**\n"
                          f"```...\n"
                          f"...code...\n"
                          f"```\n\n"
                )
                conversation = self.gpt_session.get_conversation()
                returned_files_raw = conversation.query(user_query)
                for file_name, tag in FILE_AND_TAG_PAIRS:
                    updated_file = self.extract_content_from_result(returned_files_raw, file_name)
                    if updated_file:
                        file_name_to_content[file_name] = updated_file

                for file_name, content in file_name_to_content.items():
                    persist_file(content, os.path.join(next_microservice_path, file_name))
                error_before = error

            else:
                break
            if i == MAX_DEBUGGING_ITERATIONS - 1:
                raise self.MaxDebugTimeReachedException('Could not debug the microservice.')
        return get_microservice_path(path, microservice_name, packages, num_approach, i)

    class MaxDebugTimeReachedException(BaseException):
        pass

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

