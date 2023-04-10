import random

import click

from src import gpt, jina_cloud
from src.jina_cloud import push_executor, process_error_message, jina_auth_login
from src.key_handling import set_api_key
from src.prompt_tasks import general_guidelines, executor_file_task, chain_of_thought_creation, test_executor_file_task, \
    chain_of_thought_optimization, requirements_file_task, docker_file_task, not_allowed
from src.utils.io import recreate_folder, persist_file
from src.utils.string_tools import print_colored


import os
import re

from src.constants import FILE_AND_TAG_PAIRS

gpt_session = gpt.GPTSession()

def extract_content_from_result(plain_text, file_name):
    pattern = fr"^\*\*{file_name}\*\*\n```(?:\w+\n)?([\s\S]*?)```"
    match = re.search(pattern, plain_text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    else:
        return ''

def write_config_yml(executor_name, dest_folder):
    config_content = f'''
jtype: {executor_name}
py_modules:
  - executor.py
metas:
  name: {executor_name}
    '''
    with open(os.path.join(dest_folder, 'config.yml'), 'w') as f:
        f.write(config_content)

def get_all_executor_files_with_content(folder_path):
    file_name_to_content = {}
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                file_name_to_content[filename] = content

    return file_name_to_content

def files_to_string(file_name_to_content):
    all_executor_files_string = ''
    for file_name, tag in FILE_AND_TAG_PAIRS:
        if file_name in file_name_to_content:
            all_executor_files_string += f'**{file_name}**\n'
            all_executor_files_string += f'```{tag}\n'
            all_executor_files_string += file_name_to_content[file_name]
            all_executor_files_string += '\n```\n\n'
    return all_executor_files_string


def wrap_content_in_code_block(executor_content, file_name, tag):
    return f'**{file_name}**\n```{tag}\n{executor_content}\n```\n\n'


def create_executor(
        description,
        test,
        output_path,
        executor_name,
        package,
        is_chain_of_thought=False,
):
    EXECUTOR_FOLDER_v1 = get_executor_path(output_path, package, 1)
    recreate_folder(EXECUTOR_FOLDER_v1)
    recreate_folder('../flow')

    print_colored('', '############# Executor #############', 'red')
    user_query = (
            general_guidelines()
            + executor_file_task(executor_name, description, test, package)
            + chain_of_thought_creation()
    )
    conversation = gpt_session.get_conversation()
    executor_content_raw = conversation.query(user_query)
    if is_chain_of_thought:
        executor_content_raw = conversation.query(
            f"General rules: " + not_allowed() + chain_of_thought_optimization('python', 'executor.py'))
    executor_content = extract_content_from_result(executor_content_raw, 'executor.py')

    persist_file(executor_content, os.path.join(EXECUTOR_FOLDER_v1, 'executor.py'))

    print_colored('', '############# Test Executor #############', 'red')
    user_query = (
            general_guidelines()
            + wrap_content_in_code_block(executor_content, 'executor.py', 'python')
            + test_executor_file_task(executor_name, test)
    )
    conversation = gpt_session.get_conversation()
    test_executor_content_raw = conversation.query(user_query)
    if is_chain_of_thought:
        test_executor_content_raw = conversation.query(
            f"General rules: " + not_allowed() +
            chain_of_thought_optimization('python', 'test_executor.py')
            + "Don't add any additional tests. "
        )
    test_executor_content = extract_content_from_result(test_executor_content_raw, 'test_executor.py')
    persist_file(test_executor_content, os.path.join(EXECUTOR_FOLDER_v1, 'test_executor.py'))

    print_colored('', '############# Requirements #############', 'red')
    user_query = (
            general_guidelines()
            + wrap_content_in_code_block(executor_content, 'executor.py', 'python')
            + wrap_content_in_code_block(test_executor_content, 'test_executor.py', 'python')
            + requirements_file_task()
    )
    conversation = gpt_session.get_conversation()
    requirements_content_raw = conversation.query(user_query)
    if is_chain_of_thought:
        requirements_content_raw = conversation.query(
            chain_of_thought_optimization('', '../requirements.txt') + "Keep the same version of jina ")

    requirements_content = extract_content_from_result(requirements_content_raw, '../requirements.txt')
    persist_file(requirements_content, os.path.join(EXECUTOR_FOLDER_v1, '../requirements.txt'))

    print_colored('', '############# Dockerfile #############', 'red')
    user_query = (
            general_guidelines()
            + wrap_content_in_code_block(executor_content, 'executor.py', 'python')
            + wrap_content_in_code_block(test_executor_content, 'test_executor.py', 'python')
            + wrap_content_in_code_block(requirements_content, '../requirements.txt', '')
            + docker_file_task()
    )
    conversation = gpt_session.get_conversation()
    dockerfile_content_raw = conversation.query(user_query)
    if is_chain_of_thought:
        dockerfile_content_raw = conversation.query(
            f"General rules: " + not_allowed() + chain_of_thought_optimization('dockerfile', 'Dockerfile'))
    dockerfile_content = extract_content_from_result(dockerfile_content_raw, 'Dockerfile')
    persist_file(dockerfile_content, os.path.join(EXECUTOR_FOLDER_v1, 'Dockerfile'))

    write_config_yml(executor_name, EXECUTOR_FOLDER_v1)


def create_playground(executor_name, executor_path, host):
    print_colored('', '############# Playground #############', 'red')

    file_name_to_content = get_all_executor_files_with_content(executor_path)
    user_query = (
            general_guidelines()
            + wrap_content_in_code_block(file_name_to_content['executor.py'], 'executor.py', 'python')
            + wrap_content_in_code_block(file_name_to_content['test_executor.py'], 'test_executor.py', 'python')
            + f'''
Create a playground for the executor {executor_name} using streamlit.
The playground must look like it was made by a professional designer.
All the ui elements are well thought out to make them visually appealing and easy to use.
The executor is hosted on {host}. 
This is an example how you can connect to the executor assuming the document (d) is already defined:
from jina import Client, Document, DocumentArray
client = Client(host='{host}')
response = client.post('/', inputs=DocumentArray([d])) # always use '/'
print(response[0].text) # can also be blob in case of image/audio..., this should be visualized in the streamlit app
'''
    )
    conversation = gpt_session.get_conversation()
    conversation.query(user_query)
    playground_content_raw = conversation.query(
        f"General rules: " + not_allowed() + chain_of_thought_optimization('python', 'app.py'))
    playground_content = extract_content_from_result(playground_content_raw, 'app.py')
    persist_file(playground_content, os.path.join(executor_path, 'app.py'))

def get_executor_path(output_path, package, version):
    package_path = '_'.join(package)
    return os.path.join(output_path, package_path, f'v{version}')

def debug_executor(output_path, package, description, test):
    MAX_DEBUGGING_ITERATIONS = 10
    error_before = ''
    for i in range(1, MAX_DEBUGGING_ITERATIONS):
        previous_executor_path = get_executor_path(output_path, package, i)
        next_executor_path = get_executor_path(output_path, package, i + 1)
        log_hubble = push_executor(previous_executor_path)
        error = process_error_message(log_hubble)
        if error:
            recreate_folder(next_executor_path)
            file_name_to_content = get_all_executor_files_with_content(previous_executor_path)
            all_files_string = files_to_string(file_name_to_content)
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
                    + 'Think quickly about possible reasons. '
                      'Then output the files that need change. '
                      "Don't output files that don't need change. "
                      "If you output a file, then write the complete file. "
                      "Use the exact same syntax to wrap the code:\n"
                      f"**...**\n"
                      f"```...\n"
                      f"...code...\n"
                      f"```\n\n"
            )
            conversation = gpt_session.get_conversation()
            returned_files_raw = conversation.query(user_query)
            for file_name, tag in FILE_AND_TAG_PAIRS:
                updated_file = extract_content_from_result(returned_files_raw, file_name)
                if updated_file:
                    file_name_to_content[file_name] = updated_file

            for file_name, content in file_name_to_content.items():
                persist_file(content, os.path.join(next_executor_path, file_name))
            error_before = error

        else:
            break
        if i == MAX_DEBUGGING_ITERATIONS - 1:
            raise MaxDebugTimeReachedException('Could not debug the executor.')
    return get_executor_path(output_path, package, i)

class MaxDebugTimeReachedException(BaseException):
    pass


def generate_executor_name(description):
    conversation = gpt_session.get_conversation()
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
    name = extract_content_from_result(name_raw, 'name.txt')
    return name

def get_possible_packages(description, threads):
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
    conversation = gpt_session.get_conversation()
    packages_raw = conversation.query(user_query)
    packages_csv_string = extract_content_from_result(packages_raw, 'packages.csv')
    packages = [package.split(',') for package in packages_csv_string.split('\n')]
    packages = packages[:threads]
    return packages

@click.group(invoke_without_command=True)
def main():
    pass

@main.command()
@click.option('--description', required=True, help='Description of the executor.')
@click.option('--test', required=True, help='Test scenario for the executor.')
@click.option('--num_approaches', default=3, type=int, help='Number of num_approaches to use to fulfill the task (default: 3).')
@click.option('--output_path', default='executor', help='Path to the output folder (must be empty). ')
def create(
        description,
        test,
        num_approaches=3,
        output_path='executor',
):
    jina_auth_login()

    generated_name = generate_executor_name(description)
    executor_name = f'{generated_name}{random.randint(0, 1000_000)}'

    packages_list = get_possible_packages(description, num_approaches)
    recreate_folder(output_path)
    # packages_list = [['a']]
    # executor_name = 'ColorPaletteGeneratorExecutor5946'
    # executor_path = '/Users/florianhonicke/jina/gptdeploy/executor/colorsys_colorharmony/v5'
    # host = 'grpcs://gptdeploy-5f6ea44fc8.wolf.jina.ai'
    for packages in packages_list:
        try:
            create_executor(description, test, output_path, executor_name, packages)
            executor_path = debug_executor(output_path, packages, description, test)
            print('Deploy a jina flow')
            host = jina_cloud.deploy_flow(executor_name, executor_path)
            print(f'Flow is deployed create the playground for {host}')
            create_playground(executor_name, executor_path, host)
        except MaxDebugTimeReachedException:
            print('Could not debug the executor.')
            continue
        print(
            'Executor name:', executor_name, '\n',
            'Executor path:', executor_path, '\n',
            'Host:', host, '\n',
            'Playground:', f'streamlit run {os.path.join(executor_path, "app.py")}', '\n',
        )
        break

@main.command()
@click.option('--key', required=True, help='Your OpenAI API key.')
def configure(key):
    set_api_key(key)


if __name__ == '__main__':
    main()