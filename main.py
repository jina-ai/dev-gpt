import os
import re

from src import gpt, jina_cloud
from src.constants import FILE_AND_TAG_PAIRS, EXECUTOR_FOLDER_v1, EXECUTOR_FOLDER_v2, CLIENT_FILE_NAME, STREAMLIT_FILE_NAME
from src.jina_cloud import update_client_line_in_file
from src.prompt_system import system_base_definition
from src.prompt_tasks import general_guidelines, executor_file_task, requirements_file_task, \
    test_executor_file_task, docker_file_task, client_file_task, streamlit_file_task
from src.utils.io import recreate_folder
from src.utils.string import find_differences


def extract_content_from_result(plain_text, file_name):
    pattern = fr"^\*\*{file_name}\*\*\n```(?:\w+\n)?([\s\S]*?)```"
    match = re.search(pattern, plain_text, re.MULTILINE)
    if match:
        return match.group(1).strip()
    else:
        return None


def extract_and_write(plain_text, dest_folder):
    for file_name, tag in FILE_AND_TAG_PAIRS:
        clean = extract_content_from_result(plain_text, file_name)
        full_path = os.path.join(dest_folder, file_name)
        with open(full_path, 'w') as f:
            f.write(clean)


def write_config_yml(executor_name):
    config_content = f'''
jtype: {executor_name}
py_modules:
  - executor.py
metas:
  name: {executor_name}
    '''
    with open('executor/config.yml', 'w') as f:
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


def build_prototype_implementation(executor_description, executor_name, input_doc_field, input_modality,
                                   output_doc_field, output_modality, test_in, test_out):
    system_definition = (
            system_base_definition
            + "The user is asking you to create an executor with all the necessary files "
              "and you write the complete code without leaving something out. "
    )
    user_query = (
            general_guidelines()
            + executor_file_task(executor_name, executor_description, input_modality, input_doc_field,
                                 output_modality, output_doc_field)
            + test_executor_file_task(executor_name, test_in, test_out)
            + requirements_file_task()
            + docker_file_task()
            + client_file_task()
            + streamlit_file_task()
            + "First, write down some non-obvious thoughts about the challenges of the task and how you handle them. "
              "Then write as I told you. "
    )
    plain_text = gpt.get_response(system_definition, user_query)
    return plain_text


def build_production_ready_implementation(all_executor_files_string):
    system_definition = (
            system_base_definition
            + f"The user gives you the code of the executor and all other files needed ({', '.join([e[0] for e in FILE_AND_TAG_PAIRS])}) "
              f"The files may contain bugs. Fix all of them. "
              f"Some files might have only prototype implementations and are not production ready. Add all the missing code. "
              f"Some imports might be missing. Make sure to add them. Output all the files in the same format like given to you. "
    )
    user_query = (
        "Fix all files, add all missing code and imports. Make it production ready. "
        "Keep the same format as given to you. "
        "First write down some non-obvious thoughts about what parts could need an adjustment and why. "
        "Then write as I told you. "
        "Here are the files: \n\n"
        + all_executor_files_string
    )
    all_executor_files_string_improved = gpt.get_response(system_definition, user_query)
    print('DIFFERENCES:', find_differences(all_executor_files_string, all_executor_files_string_improved))
    return all_executor_files_string_improved

def files_to_string(file_name_to_content):
    all_executor_files_string = ''
    for file_name, tag in FILE_AND_TAG_PAIRS:
        all_executor_files_string += f'**{file_name}**\n'
        all_executor_files_string += f'```{tag}\n'
        all_executor_files_string += file_name_to_content[file_name]
        all_executor_files_string += '\n```\n\n'
    return all_executor_files_string


def main(
        executor_name,
        executor_description,
        input_modality,
        input_doc_field,
        output_modality,
        output_doc_field,
        test_in,
        test_out,
        do_validation=True
):
    recreate_folder(EXECUTOR_FOLDER_v1)
    recreate_folder(EXECUTOR_FOLDER_v2)

    all_executor_files_string = build_prototype_implementation(executor_description, executor_name, input_doc_field, input_modality,
                                                output_doc_field, output_modality, test_in, test_out)
    extract_and_write(all_executor_files_string, EXECUTOR_FOLDER_v1)

    file_name_to_content_v1 = get_all_executor_files_with_content(EXECUTOR_FOLDER_v1)

    all_executor_files_string_no_instructions = files_to_string(file_name_to_content_v1)

    all_executor_files_string_improved = build_production_ready_implementation(all_executor_files_string_no_instructions)

    extract_and_write(all_executor_files_string_improved, EXECUTOR_FOLDER_v2)

    write_config_yml(executor_name)

    jina_cloud.push_executor()

    host = jina_cloud.deploy_flow(executor_name, do_validation)

    update_client_line_in_file(f'executor/{CLIENT_FILE_NAME}', host)
    update_client_line_in_file(f'executor/{STREAMLIT_FILE_NAME}', host)
    if do_validation:
        pass

    return get_all_executor_files_with_content(EXECUTOR_FOLDER_v2)


if __name__ == '__main__':
    ######### Level 2 task #########
    main(
        executor_name='My3DTo2DExecutor',
        executor_description="The executor takes 3D objects in obj format as input and outputs a 2D image projection of that object",
        input_modality='3d',
        input_doc_field='blob',
        output_modality='image',
        output_doc_field='blob',
        test_in='https://raw.githubusercontent.com/makehumancommunity/communityassets-wip/master/clothes/leotard_fs/leotard_fs.obj',
        test_out='the output should be exactly one image in png format',
        do_validation=False
    )

    ######### Level 1 task #########
    # main(
    #     executor_name='MyCoolOcrExecutor',
    #     executor_description="OCR detector",
    #     input_modality='image',
    #     input_doc_field='uri',
    #     output_modality='text',
    #     output_doc_field='text',
    #     test_in='https://miro.medium.com/v2/resize:fit:1024/0*4ty0Adbdg4dsVBo3.png',
    #     test_out='> Hello, world!_',
    #     do_validation=False
    # )

    # main(
    #     executor_name='MySentimentAnalyzer',
    #     executor_description="Sentiment analysis executor",
    #     input_modality='text',
    #     input_doc_field='text',
    #     output_modality='sentiment',
    #     output_doc_field='sentiment_label',
    #     test_in='This is a fantastic product! I love it!',
    #     test_out='positive',
    #     do_validation=False
    # )