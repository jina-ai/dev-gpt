import os

from src import gpt, jina_cloud
from src.constants import TAG_TO_FILE_NAME, EXECUTOR_FOLDER, CLIENT_FILE_NAME
from src.jina_cloud import run_client_file
from src.prompt_examples import executor_example, docarray_example, client_example
from src.prompt_tasks import general_guidelines, executor_file_task, requirements_file_task, \
    test_executor_file_task, docker_file_task, client_file_task
from src.utils.io import recreate_folder
from src.utils.string import find_between, clean_content


def extract_content_from_result(plain_text, tag):
    content = find_between(plain_text, f'$$$start_{tag}$$$', f'$$$end_{tag}$$$')
    clean = clean_content(content)
    return clean


def extract_and_write(plain_text):
    for tag, file_name in TAG_TO_FILE_NAME.items():
        clean = extract_content_from_result(plain_text, tag)
        full_path = os.path.join(EXECUTOR_FOLDER, file_name)
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

def get_all_executor_files_with_content():
    folder_path = 'executor'
    file_name_to_content = {}
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                file_name_to_content[filename] = content

    return file_name_to_content

async def main(
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
    recreate_folder(EXECUTOR_FOLDER)
    system_definition = (
            "You are a principal engineer working at Jina - an open source company."
            "Using the Jina framework, users can define executors. "
            + executor_example
            + docarray_example
            + client_example
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
    )

    plain_text = gpt.get_response(system_definition, user_query)

    extract_and_write(plain_text)

    write_config_yml(executor_name)

    jina_cloud.push_executor()

    host = await jina_cloud.deploy_flow(executor_name, do_validation)

    run_client_file(f'executor/{CLIENT_FILE_NAME}', host, do_validation)

    return get_all_executor_files_with_content()


if __name__ == '__main__':
    main(
        executor_name='MyCoolOcrExecutor',
        executor_description="OCR detector",
        input_modality='image',
        input_doc_field='uri',
        output_modality='text',
        output_doc_field='text',
        test_in='https://miro.medium.com/v2/resize:fit:1024/0*4ty0Adbdg4dsVBo3.png',
        test_out='> Hello, world!_',
    )
