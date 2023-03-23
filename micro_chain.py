import random

from main import extract_content_from_result, write_config_yml, get_all_executor_files_with_content, files_to_string

from src import gpt, jina_cloud
from src.constants import FILE_AND_TAG_PAIRS
from src.jina_cloud import build_docker
from src.prompt_tasks import general_guidelines, executor_file_task, chain_of_thought_creation, test_executor_file_task, \
    chain_of_thought_optimization, requirements_file_task, docker_file_task, not_allowed
from src.utils.io import recreate_folder, persist_file
from src.utils.string_tools import print_colored


def wrap_content_in_code_block(executor_content, file_name, tag):
    return f'**{file_name}**\n```{tag}\n{executor_content}\n```\n\n'




def create_executor(
        executor_description,
        input_modality,
        output_modality,
        test_scenario,
        executor_name
):
    input_doc_field = 'text' if input_modality == 'text' else 'blob'
    output_doc_field = 'text' if output_modality == 'text' else 'blob'
    # random integer at the end of the executor name to avoid name clashes

    recreate_folder('executor')
    EXECUTOR_FOLDER_v1 = 'executor/v1'
    recreate_folder(EXECUTOR_FOLDER_v1)
    recreate_folder('flow')

    print_colored('', '############# Executor #############', 'red')
    user_query = (
            general_guidelines()
            + executor_file_task(executor_name, executor_description, input_modality, input_doc_field,
                                 output_modality, output_doc_field)
            + chain_of_thought_creation()
    )
    conversation = gpt.Conversation()
    conversation.query(user_query)
    executor_content_raw = conversation.query(f"General rules: " + not_allowed() + chain_of_thought_optimization('python', 'executor.py'))
    executor_content = extract_content_from_result(executor_content_raw, 'executor.py')
    persist_file(executor_content, EXECUTOR_FOLDER_v1 + '/executor.py')

    print_colored('', '############# Test Executor #############', 'red')
    user_query = (
            general_guidelines()
            + wrap_content_in_code_block(executor_content, 'executor.py', 'python')
            + test_executor_file_task(executor_name, test_scenario)
    )
    conversation = gpt.Conversation()
    conversation.query(user_query)
    test_executor_content_raw = conversation.query(
        f"General rules: " + not_allowed() +
        chain_of_thought_optimization('python', 'test_executor.py')
        + "Don't add any additional tests. "
    )
    test_executor_content = extract_content_from_result(test_executor_content_raw, 'test_executor.py')
    persist_file(test_executor_content, EXECUTOR_FOLDER_v1 + '/test_executor.py')

    print_colored('', '############# Requirements #############', 'red')
    user_query = (
            general_guidelines()
            + wrap_content_in_code_block(executor_content, 'executor.py', 'python')
            + wrap_content_in_code_block(test_executor_content, 'test_executor.py', 'python')
            + requirements_file_task()
    )
    conversation = gpt.Conversation()
    conversation.query(user_query)
    requirements_content_raw = conversation.query(chain_of_thought_optimization('', 'requirements.txt') + "Keep the same version of jina ")

    requirements_content = extract_content_from_result(requirements_content_raw, 'requirements.txt')
    persist_file(requirements_content, EXECUTOR_FOLDER_v1 + '/requirements.txt')

    print_colored('', '############# Dockerfile #############', 'red')
    user_query = (
            general_guidelines()
            + wrap_content_in_code_block(executor_content, 'executor.py', 'python')
            + wrap_content_in_code_block(test_executor_content, 'test_executor.py', 'python')
            + wrap_content_in_code_block(requirements_content, 'requirements.txt', '')
            + docker_file_task()
    )
    conversation = gpt.Conversation()
    conversation.query(user_query)
    dockerfile_content_raw = conversation.query(f"General rules: " + not_allowed() + chain_of_thought_optimization('dockerfile', 'Dockerfile'))
    dockerfile_content = extract_content_from_result(dockerfile_content_raw, 'Dockerfile')
    persist_file(dockerfile_content, EXECUTOR_FOLDER_v1 + '/Dockerfile')

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
The executor is hosted on {host}. 
This is an example how you can connect to the executor assuming the document (d) is already defined:
from jina import Client, Document, DocumentArray
client = Client(host='{host}')
response = client.post('/process', inputs=DocumentArray([d]))
print(response[0].text) # can also be blob in case of image/audio..., this should be visualized in the streamlit app
'''
    )
    conversation = gpt.Conversation()
    conversation.query(user_query)
    playground_content_raw = conversation.query(f"General rules: " + not_allowed() + chain_of_thought_optimization('python', 'playground.py'))
    playground_content = extract_content_from_result(playground_content_raw, 'playground.py')
    persist_file(playground_content, f'{executor_path}/playground.py')

def debug_executor():
    for i in range(1, 20):

        error = build_docker(f'executor/v{i}')
        if error:
            recreate_folder(f'executor/v{i + 1}')
            file_name_to_content = get_all_executor_files_with_content(f'executor/v{i}')
            all_files_string = files_to_string(file_name_to_content)
            user_query = (
                f"General rules: " + not_allowed()
                + 'Here are all the files I use:\n'
                + all_files_string
                + 'I got the following error:\n'
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
            conversation = gpt.Conversation()
            returned_files_raw = conversation.query(user_query)
            for file_name, tag in FILE_AND_TAG_PAIRS:
                updated_file = extract_content_from_result(returned_files_raw, file_name)
                if updated_file:
                    file_name_to_content[file_name] = updated_file

            for file_name, content in file_name_to_content.items():
                persist_file(content, f'executor/v{i + 1}/{file_name}')
        else:
            break
    return f'executor/v{i}'


def main(
        executor_description,
        input_modality,
        output_modality,
        test_scenario,
):
    executor_name = f'MicroChainExecutor{random.randint(0, 1000_000)}'
    create_executor(executor_description, input_modality, output_modality, test_scenario, executor_name)
    executor_path = debug_executor()
    print('Executor can be built locally, now we will push it to the cloud.')
    jina_cloud.push_executor(executor_path)
    print('Deploy a jina flow')
    host = jina_cloud.deploy_flow(executor_name, 'flow')
    print(f'Flow is deployed create the playground for {host}')
    executor_name = 'MicroChainExecutor48442'
    executor_path = 'executor/v2'
    host = 'grpcs://mybelovedocrflow-24a412bc63.wolf.jina.ai'
    create_playground(executor_name, executor_path, host)

if __name__ == '__main__':
    # ######## Level 1 task #########
    main(
        executor_description="The executor takes a pdf file as input, parses it and returns the text.",
        input_modality='pdf',
        output_modality='text',
        test_scenario='Takes https://www2.deloitte.com/content/dam/Deloitte/de/Documents/about-deloitte/Deloitte-Unternehmensgeschichte.pdf and returns a string that is at least 100 characters long',
    )
    # money prompt: $0.56
    # money generation: $0.22
    # total money: $0.78


    # ######## Level 2 task #########
    # main(
    #     executor_description="OCR detector",
    #     input_modality='image',
    #     output_modality='text',
    #     test_scenario='Takes https://miro.medium.com/v2/resize:fit:1024/0*4ty0Adbdg4dsVBo3.png as input and returns a string that contains "Hello, world"',
    # )


    # ######## Level 3 task #########
    # main(
    #     executor_description="The executor takes an mp3 file as input and returns bpm and pitch in the tags.",
    #     input_modality='audio',
    #     output_modality='tags',
    #     test_scenario='Takes https://miro.medium.com/v2/resize:fit:1024/0*4ty0Adbdg4dsVBo3.png as input and returns a string that contains "Hello, world"',
    # )

    ######### Level 4 task #########
    # main(
    #     executor_description="The executor takes 3D objects in obj format as input "
    #                          "and outputs a 2D image projection of that object where the full object is shown. ",
    #     input_modality='3d',
    #     output_modality='image',
    #     test_scenario='Test that 3d object from https://raw.githubusercontent.com/polygonjs/polygonjs-assets/master/models/wolf.obj '
    #                   'is put in and out comes a 2d rendering of it',
    # )
