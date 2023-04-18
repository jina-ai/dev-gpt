from src.constants import EXECUTOR_FILE_NAME, REQUIREMENTS_FILE_NAME, TEST_EXECUTOR_FILE_NAME, DOCKER_FILE_NAME, \
    DOCKER_FILE_TAG, CLIENT_FILE_TAG, CLIENT_FILE_NAME, STREAMLIT_FILE_TAG, STREAMLIT_FILE_NAME, EXECUTOR_FILE_TAG, \
    REQUIREMENTS_FILE_TAG, TEST_EXECUTOR_FILE_TAG


def general_guidelines():
    return '''
The code you write is production ready.
Every file starts with comments describing what the code is doing before the first import.
Comments can only be written within code blocks.
Then all imports are listed.
It is important to import all modules that could be needed in the Executor code.
Always import:
from jina import Executor, DocumentArray, Document, requests
import json
from io import BytesIO
import requests as req


Start from top-level and then fully implement all methods.

'''


def _task(task, tag_name, file_name, purpose=None):
    into_string = file_name
    if purpose:
        into_string += f"/{purpose}"

    return (
            task + f"The code will go into {into_string}. Make sure to wrap the code into ``` marks even if you only "
                   f"output code:\n"
                   f"**{file_name}**\n"
                   f"```{tag_name}\n"
                   f"...code...\n"
                   f"```\nYou must provide the complete file with the exact same syntax to wrap the code."
    )


def executor_file_task(executor_name, executor_description, test_scenario, package):
    return _task(f'''
Write the executor called '{executor_name}'. The name is very important to keep.
It matches the following description: '{executor_description}'.
It will be tested with the following scenario: '{test_scenario}'.
For the implementation use the following package: '{package}'.

Obey the following rules:
Have in mind that d.uri is never a path to a local file. It is always a url.
{not_allowed_executor()}
Your approach:
1. Identify the core challenge when implementing the executor.
2. Think about possible solutions for these challenges.
3. Decide for one of the solutions.
4. Write the code.
''', EXECUTOR_FILE_TAG, EXECUTOR_FILE_NAME)


def test_executor_file_task(executor_name, test_scenario):
    return _task(
        "Write a small unit test for the executor. "
        "Start the test with an extensive comment about the test case. "
        + (
            f"Write a single test case that tests the following scenario: '{test_scenario}'. "
            f"In case the test scenario is not precise enough, test a general case without any assumptions."
            if test_scenario else ""
        )
        + "Use the following import to import the executor: "
          f"```\nfrom microservice import {executor_name}\n```"
        + not_allowed_executor()
        + "The test must not open local files. "
        + "The test must not mock a function of the executor. "
        + "The test must not use other data than the one provided in the test scenario. ",
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
        "It is important to make sure that all libs are installed that are required by the python packages. "
        "Usually libraries are installed with apt-get. "
        "Be aware that the machine the docker container is running on does not have a GPU - only CPU. "
        "Add the config.yml file to the Dockerfile. Note that the Dockerfile only has access to the files: "
        "microservice.py, requirements.txt, config.yml, test_microservice.py. "
        "The base image of the Dockerfile is FROM jinaai/jina:3.14.1-py39-standard. "
        'The entrypoint is ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]. '
        'Make sure the all files are in the /workdir. '
        "The Dockerfile runs the test during the build process. " + not_allowed_docker(),
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

def chain_of_thought_optimization(tag_name, file_name, file_name_function=None):
    file_name_or_function = file_name
    if file_name_function:
        file_name_or_function += f"/{file_name_function}"
    return _task(
        f'First, write down an extensive list of obvious and non-obvious observations about {file_name_or_function} that could need an adjustment. Explain why. '
        f"Think if all the changes are required and finally decide for the changes you want to make, "
        f"but you are not allowed disregard the instructions in the previous message. "
        f"Be very hesitant to change the code. Only make a change if you are sure that it is necessary. "

        f"Output only {file_name_or_function} "
        f"Write the whole content of {file_name_or_function} - even if you decided to change only a small thing or even nothing. ",
        tag_name,
        file_name,
        file_name_function
    )

def not_allowed_executor():
    return '''
The executor and the test must not use the GPU.
The executor and the test must not access a database.
The executor and the test must not access a display.
The executor and the test must not access external apis except unless it is explicitly mentioned in the description or test case (e.g. by mentioning the api that should be used or by providing a URL to access the data). 
The executor and the test must not load data from the local file system unless it was created by the executor itself.
The executor and the test must not use a pre-trained model unless it is explicitly mentioned in the description.
The executor and the test must not train a model.
The executor and the test must not use any attribute of Document accept Document.text.
The executor and the test must not contain prototype or placeholder implementations.
The executor and the test must run in a docker container based on debian.
'''

def not_allowed_docker():
    return '''
Note that the Dockerfile only has access to the files: microservice.py, requirements.txt, config.yml, test_microservice.py.
Note that the Dockerfile runs the test_microservice.py during the build process.
The Dockerfile must not attach a virtual display when running test_microservice.py.
'''
