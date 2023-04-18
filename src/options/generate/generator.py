import os
import random
import re

from src.apis import gpt
from src.apis.jina_cloud import process_error_message, push_executor
from src.constants import FILE_AND_TAG_PAIRS, NUM_IMPLEMENTATION_STRATEGIES, MAX_DEBUGGING_ITERATIONS, \
    PROBLEMATIC_PACKAGES
from src.options.generate.prompt_tasks import general_guidelines, executor_file_task, \
    not_allowed_executor, chain_of_thought_optimization, test_executor_file_task, requirements_file_task, \
    docker_file_task, not_allowed_docker
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
            packages,
            num_approach,
    ):
        MICROSERVICE_FOLDER_v1 = get_microservice_path(path, microservice_name, packages, num_approach, 1)
        os.makedirs(MICROSERVICE_FOLDER_v1)

        print_colored('', '############# Microservice #############', 'blue')
        user_query = (
                general_guidelines()
                + executor_file_task(microservice_name, description, test, packages)
        )
        conversation = self.gpt_session.get_conversation()
        microservice_content_raw = conversation.query(user_query)
        microservice_content = self.extract_content_from_result(microservice_content_raw, 'microservice.py',
                                                                match_single_block=True)
        if microservice_content == '':
            microservice_content_raw = conversation.query('You must add the executor code.')
            microservice_content = self.extract_content_from_result(
                microservice_content_raw, 'microservice.py', match_single_block=True
            )
        persist_file(microservice_content, os.path.join(MICROSERVICE_FOLDER_v1, 'microservice.py'))

        print_colored('', '############# Test Microservice #############', 'blue')
        user_query = (
                general_guidelines()
                + self.wrap_content_in_code_block(microservice_content, 'microservice.py', 'python')
                + test_executor_file_task(microservice_name, test)
        )
        conversation = self.gpt_session.get_conversation()
        test_microservice_content_raw = conversation.query(user_query)
        test_microservice_content = self.extract_content_from_result(
            test_microservice_content_raw, 'microservice.py', match_single_block=True
        )
        persist_file(test_microservice_content, os.path.join(MICROSERVICE_FOLDER_v1, 'test_microservice.py'))

        print_colored('', '############# Requirements #############', 'blue')
        requirements_path = os.path.join(MICROSERVICE_FOLDER_v1, 'requirements.txt')
        user_query = (
                general_guidelines()
                + self.wrap_content_in_code_block(microservice_content, 'microservice.py', 'python')
                + self.wrap_content_in_code_block(test_microservice_content, 'test_microservice.py', 'python')
                + requirements_file_task()
        )
        conversation = self.gpt_session.get_conversation()
        requirements_content_raw = conversation.query(user_query)

        requirements_content = self.extract_content_from_result(requirements_content_raw, 'requirements.txt',
                                                                match_single_block=True)
        persist_file(requirements_content, requirements_path)

        print_colored('', '############# Dockerfile #############', 'blue')
        user_query = (
                general_guidelines()
                + self.wrap_content_in_code_block(microservice_content, 'microservice.py', 'python')
                + self.wrap_content_in_code_block(test_microservice_content, 'test_microservice.py', 'python')
                + self.wrap_content_in_code_block(requirements_content, 'requirements.txt', '')
                + docker_file_task()
        )
        conversation = self.gpt_session.get_conversation()
        dockerfile_content_raw = conversation.query(user_query)
        dockerfile_content = self.extract_content_from_result(dockerfile_content_raw, 'Dockerfile',
                                                              match_single_block=True)
        persist_file(dockerfile_content, os.path.join(MICROSERVICE_FOLDER_v1, 'Dockerfile'))

        self.write_config_yml(microservice_name, MICROSERVICE_FOLDER_v1)
        print('First version of the microservice generated. Start iterating on it to make the tests pass...')

    def generate_playground(self, microservice_name, microservice_path):
        print_colored('', '############# Playground #############', 'blue')

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
You must provide the complete file with the exact same syntax to wrap the code.
The playground (app.py) must read the host from sys.argv[-1] because it will be started with a custom host: streamlit run app.py -- --host grpc://...
The playground (app.py) must not let the user configure the host on the ui.
'''
        )
        conversation = self.gpt_session.get_conversation([])
        conversation.query(user_query)
        playground_content_raw = conversation.query(chain_of_thought_optimization('python', 'app.py', 'the playground'))
        playground_content = self.extract_content_from_result(playground_content_raw, 'app.py', match_single_block=True)
        persist_file(playground_content, os.path.join(microservice_path, 'app.py'))

    def debug_microservice(self, path, microservice_name, num_approach, packages, description, test):
        for i in range(1, MAX_DEBUGGING_ITERATIONS):
            print('Debugging iteration', i)
            print('Trying to build the microservice. Might take a while...')
            previous_microservice_path = get_microservice_path(path, microservice_name, packages, num_approach, i)
            next_microservice_path = get_microservice_path(path, microservice_name, packages, num_approach, i + 1)
            log_hubble = push_executor(previous_microservice_path)
            error = process_error_message(log_hubble)
            if error:
                print('An error occurred during the build process. Feeding the error back to the assistent...')
                self.do_debug_iteration(description, error, next_microservice_path,
                                        previous_microservice_path, test)
                if i == MAX_DEBUGGING_ITERATIONS - 1:
                    raise self.MaxDebugTimeReachedException('Could not debug the microservice.')
            else:
                print('Successfully build microservice.')
                break

        return get_microservice_path(path, microservice_name, packages, num_approach, i)

    def do_debug_iteration(self, description, error, next_microservice_path, previous_microservice_path,
                           test):
        os.makedirs(next_microservice_path)
        file_name_to_content = get_all_microservice_files_with_content(previous_microservice_path)

        summarized_error = self.summarize_error(error)
        is_dependency_issue = self.is_dependency_issue(error, file_name_to_content['Dockerfile'])
        if is_dependency_issue:
            all_files_string = self.files_to_string({
                key: val for key, val in file_name_to_content.items() if
                key in ['requirements.txt', 'Dockerfile']
            })
            user_query = self.get_user_query_dependency_issue(all_files_string, summarized_error)
        else:
            user_query = self.get_user_query_code_issue(description, summarized_error, file_name_to_content,
                                                        test)
        conversation = self.gpt_session.get_conversation()
        returned_files_raw = conversation.query(user_query)
        for file_name, tag in FILE_AND_TAG_PAIRS:
            updated_file = self.extract_content_from_result(returned_files_raw, file_name)
            if updated_file and (not is_dependency_issue or file_name in ['requirements.txt', 'Dockerfile']):
                file_name_to_content[file_name] = updated_file
                print(f'Updated {file_name}')
        for file_name, content in file_name_to_content.items():
            persist_file(content, os.path.join(next_microservice_path, file_name))


    def get_user_query_dependency_issue(self, all_files_string, summarized_error):
        user_query = (
            f'''
Your task is to provide guidance on how to solve an error that occurred during the Docker build process. 
Here is the summary of the error that occurred:
{summarized_error}

To solve this error, you should:
1. Suggest 3 to 5 possible solutions on how to solve it. You have no access to the documentation of the package.
2. Decide for the best solution and explain it in detail.
3. Write down the files that need to be changed, but not files that don't need to be changed. 
For files that need to be changed, you must provide the complete file with the exact same syntax to wrap the code.
Obey the following rules: {not_allowed_docker()}

You are given the following files:

{all_files_string}"

Output all the files that need change. 
Don't output files that don't need change. If you output a file, then write the 
complete file. Use the exact following syntax to wrap the code:

**...**
```
...code...
```

Example:

**requirements.txt**
```
jina==2.0.0
```

'''
        )
        return user_query

    def get_user_query_code_issue(self, description, summarized_error, file_name_to_content, test):
        all_files_string = self.files_to_string(file_name_to_content)
        return f'''
General rules: {not_allowed_executor()}
Here is the description of the task the executor must solve:
{description}

Here is the test scenario the executor must pass:\n{test}
Here are all the files I use:
{all_files_string}


Here is the summary of the error that occurred:
{summarized_error}

To solve this error, you should:
1. Suggest 3 to 5 possible solutions on how to solve it. You have no access to the documentation of the package.
2. Decide for the best solution and explain it in detail.
3. Write down the files that need to be changed, but not files that don't need to be changed. 
Obey the following rules: 
{not_allowed_executor()}
{not_allowed_docker()}


Output all the files that need change. 
Don't output files that don't need change. If you output a file, then write the 
complete file. Use the exact following syntax to wrap the code:

**...**
```...
...code...
```

Example:

**microservice.py**
```python
print('hello world')
```

'''

    class MaxDebugTimeReachedException(BaseException):
        pass

    def is_dependency_issue(self, error, docker_file: str):
        # a few heuristics to quickly jump ahead
        if any([error_message in error for error_message in ['AttributeError', 'NameError', 'AssertionError']]):
            return False

        print_colored('', 'Is it a dependency issue?', 'blue')
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
        print_colored('', '############# What packages to use? #############', 'blue')
        user_query = f'''
Here is the task description of the problem you need to solve:
"{description}"
1. Write down all the non-trivial subtasks you need to solve.
2. Find out what is the core problem to solve.
3. List up to 15 Python packages that are specifically designed or have functionalities to solve the complete core problem.
4. For each of the 15 package think if it fulfills the following requirements:
a) specifically designed or have functionalities to solve the complete core problem.
b) has a stable api among different versions
c) does not have system requirements
d) can solve the task when running in a docker container
e) the implementation of the core problem using the package would obey the following rules:
{not_allowed_executor()}
When answering, just write "yes" or "no".

5. Output the most suitable 5 python packages starting with the best one. 
If the package is mentioned in the description, then it is automatically the best one.

The output must be a list of lists wrapped into ``` and starting with **packages.csv** like this:
**packages.csv**
```
package1a, package1b ...
package2a, package2b, package2c
package3a ...
package4a ...
package5a ...
...
```
'''
        conversation = self.gpt_session.get_conversation()
        packages_raw = conversation.query(user_query)
        packages_csv_string = self.extract_content_from_result(packages_raw, 'packages.csv')
        packages_list = [[pkg.strip() for pkg in packages_string.split(',')] for packages_string in packages_csv_string.split('\n')]
        packages_list = packages_list[:NUM_IMPLEMENTATION_STRATEGIES]
        return packages_list

    def generate(self, microservice_path):
        generated_name = self.generate_microservice_name(self.task_description)
        microservice_name = f'{generated_name}{random.randint(0, 10_000_000)}'
        packages_list = self.get_possible_packages(self.task_description)
        packages_list = [packages for packages in packages_list if len(set(packages).intersection(set(PROBLEMATIC_PACKAGES))) == 0]
        for num_approach, packages in enumerate(packages_list):
            try:
                self.generate_microservice(self.task_description, self.test_description, microservice_path, microservice_name, packages,
                                           num_approach)
                final_version_path = self.debug_microservice(microservice_path, microservice_name, num_approach,
                                                             packages, self.task_description, self.test_description)
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
        user_query = f'''
Here is an error message I encountered during the docker build process:
"{error}"
Your task is to summarize the error message as compact and informative as possible while maintaining all information necessary to debug the core issue.
Warnings are not worth mentioning.
'''
        error_summary = conversation.query(user_query)
        return error_summary
