import random

from main import extract_content_from_result, write_config_yml, get_all_executor_files_with_content, files_to_string

from src import gpt, jina_cloud
from src.constants import FILE_AND_TAG_PAIRS
from src.jina_cloud import build_docker
from src.prompt_tasks import general_guidelines, executor_file_task, chain_of_thought_creation, test_executor_file_task, \
    chain_of_thought_optimization, requirements_file_task, docker_file_task
from src.utils.io import recreate_folder, persist_file
from src.utils.string_tools import print_colored


def wrap_content_in_code_block(executor_content, file_name, tag):
    return f'**{file_name}**\n```{tag}\n{executor_content}\n```\n\n'


def main(
        executor_description,
        input_modality,
        # input_doc_field,
        output_modality,
        # output_doc_field,
        test_scenario,
        do_validation=True
):
    # input_doc_field = 'text' if input_modality == 'text' else 'blob'
    # output_doc_field = 'text' if output_modality == 'text' else 'blob'
    # # random integer at the end of the executor name to avoid name clashes
    # executor_name = f'MicroChainExecutor{random.randint(0, 1000_000)}'
    # recreate_folder('executor')
    # EXECUTOR_FOLDER_v1 = 'executor/v1'
    # recreate_folder(EXECUTOR_FOLDER_v1)
    # recreate_folder('flow')
    #
    # print_colored('', '############# Executor #############', 'red')
    # user_query = (
    #         general_guidelines()
    #         + executor_file_task(executor_name, executor_description, input_modality, input_doc_field,
    #                              output_modality, output_doc_field)
    #         + chain_of_thought_creation()
    # )
    # conversation = gpt.Conversation()
    # conversation.query(user_query)
    # executor_content_raw = conversation.query(chain_of_thought_optimization('python', 'executor.py'))
    # executor_content = extract_content_from_result(executor_content_raw, 'executor.py')
    # persist_file(executor_content, 'executor.py')
    #
    # print_colored('', '############# Test Executor #############', 'red')
    # user_query = (
    #         general_guidelines()
    #         + wrap_content_in_code_block(executor_content, 'executor.py', 'python')
    #         + test_executor_file_task(executor_name, test_scenario)
    # )
    # conversation = gpt.Conversation()
    # conversation.query(user_query)
    # test_executor_content_raw = conversation.query(
    #     chain_of_thought_optimization('python', 'test_executor.py')
    #     + "Don't add any additional tests. "
    # )
    # test_executor_content = extract_content_from_result(test_executor_content_raw, 'test_executor.py')
    # persist_file(test_executor_content, 'test_executor.py')
    #
    # print_colored('', '############# Requirements #############', 'red')
    # user_query = (
    #         general_guidelines()
    #         + wrap_content_in_code_block(executor_content, 'executor.py', 'python')
    #         + wrap_content_in_code_block(test_executor_content, 'test_executor.py', 'python')
    #         + requirements_file_task()
    # )
    # conversation = gpt.Conversation()
    # conversation.query(user_query)
    # requirements_content_raw = conversation.query(chain_of_thought_optimization('', 'requirements.txt') + "Keep the same version of jina ")
    #
    # requirements_content = extract_content_from_result(requirements_content_raw, 'requirements.txt')
    # persist_file(requirements_content, 'requirements.txt')
    #
    # print_colored('', '############# Dockerfile #############', 'red')
    # user_query = (
    #         general_guidelines()
    #         + wrap_content_in_code_block(executor_content, 'executor.py', 'python')
    #         + wrap_content_in_code_block(test_executor_content, 'test_executor.py', 'python')
    #         + wrap_content_in_code_block(requirements_content, 'requirements.txt', '')
    #         + docker_file_task()
    # )
    # conversation = gpt.Conversation()
    # conversation.query(user_query)
    # dockerfile_content_raw = conversation.query(chain_of_thought_optimization('dockerfile', 'Dockerfile'))
    # dockerfile_content = extract_content_from_result(dockerfile_content_raw, 'Dockerfile')
    # persist_file(dockerfile_content, 'Dockerfile')
    #
    # write_config_yml(executor_name, EXECUTOR_FOLDER_v1)

    for i in range(1, 20):
        conversation = gpt.Conversation()
        error = build_docker(f'executor_level2/v{i}')
        if error:
            recreate_folder(f'executor_level2/v{i + 1}')
            file_name_to_content = get_all_executor_files_with_content(f'executor_level2/v{i}')
            all_files_string = files_to_string(file_name_to_content)
            user_query = (
                'Here are all the files I use:\n'
                + all_files_string
                + 'I got the following error:\n'
                + error
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
            returned_files_raw = conversation.query(user_query)
            for file_name, tag in FILE_AND_TAG_PAIRS:
                updated_file = extract_content_from_result(returned_files_raw, file_name)
                if updated_file:
                    file_name_to_content[file_name] = updated_file

            for file_name, content in file_name_to_content.items():
                persist_file(content, f'executor_level2/v{i + 1}/{file_name}')
        else:
            break


    error = jina_cloud.push_executor('executor_level2')
    host = jina_cloud.deploy_flow(executor_name, do_validation, 'flow')

    # create playgorund and client.py


if __name__ == '__main__':
    # ######## Level 1 task #########
    # main(
    #     executor_description="OCR detector",
    #     input_modality='image',
    #     # input_doc_field='blob',
    #     output_modality='text',
    #     # output_doc_field='text',
    #     test_scenario='Takes https://miro.medium.com/v2/resize:fit:1024/0*4ty0Adbdg4dsVBo3.png as input and returns a string that contains "Hello, world"',
    #     do_validation=False
    # )

    ######### Level 2 task #########
    main(
        executor_description="The executor takes 3D objects in obj format as input "
                             "and outputs a 2D image projection of that object where the full object is shown. ",
        input_modality='3d',
        output_modality='image',
        test_scenario='Test that 3d object from https://raw.githubusercontent.com/makehumancommunity/communityassets-wip/master/clothes/leotard_fs/leotard_fs.obj '
                      'is put in and out comes a 2d rendering of it',
        do_validation=False
    )
