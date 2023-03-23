from src.constants import EXECUTOR_FILE_NAME, REQUIREMENTS_FILE_NAME, TEST_EXECUTOR_FILE_NAME, DOCKER_FILE_NAME, \
    DOCKER_FILE_TAG, CLIENT_FILE_TAG, CLIENT_FILE_NAME, STREAMLIT_FILE_TAG, STREAMLIT_FILE_NAME, EXECUTOR_FILE_TAG, \
    REQUIREMENTS_FILE_TAG, TEST_EXECUTOR_FILE_TAG


def general_guidelines():
    return (
        "The code you write is production ready. "
        "Every file starts with comments describing what the code is doing before the first import. "
        "Comments can only be written between tags. "
        "Then all imports are listed. "
        "It is important to import all modules that could be needed in the executor code. "
        "Always import: "
        "from jina import Executor, DocumentArray, Document, requests "
        "Start from top-level and then fully implement all methods. "
        "\n"
    )


def _task(task, tag_name, file_name):
    return (
            task + f"The code will go into {file_name}. Wrap the code into:\n"
                   f"**{file_name}**\n"
                   f"```{tag_name}\n"
                   f"...code...\n"
                   f"```\n\n"
    )


def executor_file_task(executor_name, executor_description, input_modality, input_doc_field,
                       output_modality, output_doc_field):
    return _task(f'''
Write the executor called '{executor_name}'.
It matches the following description: '{executor_description}'.
It gets a DocumentArray as input where each document has the input modality '{input_modality}' and can be accessed via document.{input_doc_field}.
It returns a DocumentArray as output where each document has the output modality '{output_modality}' that is stored in document.{output_doc_field}.
Have in mind that d.uri is never a path to a local file. It is always a url.
''' + not_allowed(),
                 EXECUTOR_FILE_TAG,
                 EXECUTOR_FILE_NAME
                 )


def test_executor_file_task(executor_name, test_scenario):
    return _task(
        "Write a small unit test for the executor. "
        "Start the test with an extensive comment about the test case. "
        + (
            f"Write a single test case that tests the following scenario: '{test_scenario}'. "
            if test_scenario else ""
        )
        + "Use the following import to import the executor: "
          f"from executor import {executor_name} "
        + not_allowed()
        + "The test is not allowed to open local files. ",
        TEST_EXECUTOR_FILE_TAG,
        TEST_EXECUTOR_FILE_NAME
    )

def requirements_file_task():
    return _task(
        "Write the content of the requirements.txt file. "
        "Make sure to include pytest. "
        "Make sure that jina==3.14.1. "
        "All versions are fixed using ~=, ==, <, >, <=, >=. The package versions should not have conflicts. ",
        REQUIREMENTS_FILE_TAG,
        REQUIREMENTS_FILE_NAME
    )


def docker_file_task():
    return _task(
        "Write the Dockerfile that defines the environment with all necessary dependencies that the executor uses. "
        "The Dockerfile runs the test during the build process. "
        "It is important to make sure that all libs are installed that are required by the python packages. "
        "Usually libraries are installed with apt-get. "
        "Be aware that the machine the docker container is running on does not have a GPU - only CPU. "
        "Add the config.yml file to the Dockerfile. "
        "The base image of the Dockerfile is FROM jinaai/jina:3.14.1-py39-standard. "
        'The entrypoint is ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]. '
        'Make sure the all files are in the /workdir. '
        "The Dockerfile runs the test during the build process. " + not_allowed(),
        DOCKER_FILE_TAG,
        DOCKER_FILE_NAME
    )


def client_file_task():
    return _task(
        "Write the client file. ",
        CLIENT_FILE_TAG,
        CLIENT_FILE_NAME
    )


def streamlit_file_task():
    return _task(
        "Write the streamlit file allowing to make requests . ",
        STREAMLIT_FILE_TAG,
        STREAMLIT_FILE_NAME
    )


def chain_of_thought_creation():
    return (
        "First, write down some non-obvious thoughts about the challenges of the task and give multiple approaches on how you handle them. "
        "For example, there are different libraries you could use and not all of them obay the rules: "
        + not_allowed()
        + "Discuss the pros and cons for all of these approaches and then decide for one of the approaches. "
        "Then write as I told you. "
    )


def chain_of_thought_optimization(tag_name, file_name):
    return _task(
        f'First, write down an extensive list of obvious and non-obvious observations about {file_name} that could need an adjustment. Explain why. '
        f"Think if all the changes are required and finally decide for the changes you want to make, "
        f"but you are not allowed disregard the instructions in the previous message. "
        f"Be very hesitant to change the code. Only make a change if you are sure that it is necessary. "

        f"Output only {file_name} "
        f"Write the whole content of {file_name} - even if you decided to change only a small thing or even nothing. ",
        tag_name,
        file_name
    )

def not_allowed():
    return '''
The executor is not allowed to use the GPU.
The executor is not allowed to access a database.
The executor is not allowed to access a display.
The executor is not allowed to access external apis. 
'''