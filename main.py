import os

from docarray import DocumentArray, Document
from jina import Client

from src import gpt, jina_cloud
from src.constants import TAG_TO_FILE_NAME, EXECUTOR_FOLDER
from src.prompt_examples import executor_example, docarray_example
from src.prompt_tasks import general_guidelines, executor_name_task, executor_file_task, requirements_file_task, \
    test_executor_file_task, docker_file_task
from src.utils.io import recreate_folder
from src.utils.string import find_between, clean_content

input_executor_description = "Write an executor that takes image bytes as input (document.blob within a DocumentArray) and use BytesIO to convert it to PIL and detects ocr " \
                             "and returns the texts as output (as DocumentArray). "

input_test_description = 'The test downloads the image ' \
                         'https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Onlineocr.png/640px-Onlineocr.png ' \
                         ' loads it as bytes, takes it as input to the executor and asserts that the output is "Hello World".'


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


def main():
    recreate_folder(EXECUTOR_FOLDER)
    system_definition = (
            "You are a principal engineer working at Jina - an open source company."
            "Using the Jina framework, users can define executors."
            + executor_example
            + docarray_example
    )

    user_query = (
            input_executor_description
            + general_guidelines
            + executor_name_task()
            + executor_file_task()
            + test_executor_file_task()
            + requirements_file_task()
            + docker_file_task()
            + input_test_description
    )

    plain_text = gpt.get_response(system_definition, user_query)
    extract_and_write(plain_text)

    executor_name = extract_content_from_result(plain_text, 'executor_name')

    write_config_yml(executor_name)

    jina_cloud.push_executor()

    host = jina_cloud.deploy_flow(executor_name)

    client = Client(host=host)

    d = Document(uri='data/txt.png')
    d.load_uri_to_blob()
    response = client.post('/index', inputs=DocumentArray([d]))
    response[0].summary()


if __name__ == '__main__':
    main()
