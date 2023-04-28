import os

from src.constants import REQUIREMENTS_FILE_NAME, DOCKER_FILE_NAME, IMPLEMENTATION_FILE_NAME, TEST_EXECUTOR_FILE_NAME


def list_dirs_no_hidden(path):
    """
    List all non-hidden directories in the specified path.

    :param path: str, optional (default is '.')
        The path to the directory you want to list files and directories from.
    :return: list
        A list of directory names that are not hidden.
    """
    return [entry for entry in os.listdir(path) if not entry.startswith('.') and os.path.isdir(os.path.join(path, entry))]


def get_latest_folder(path, max_fn=max):
    return max_fn([os.path.join(path, f) for f in list_dirs_no_hidden(path)])

def version_max_fn(path_list):
    version_list = [int(os.path.split(path)[-1].replace('v', '')) for path in path_list]
    max_version = max(version_list)
    max_index = version_list.index(max_version)
    return path_list[max_index]

def get_latest_version_path(microservice_path):
    executor_name_path = get_latest_folder(microservice_path)
    latest_approach_path = get_latest_folder(executor_name_path)
    latest_version_path = get_latest_folder(latest_approach_path, max_fn=version_max_fn)
    return latest_version_path

def get_executor_name(microservice_path):
    latest_folder = get_latest_folder(microservice_path)
    return os.path.split(latest_folder)[-1]


def validate_folder_is_correct(microservice_path):
    if not os.path.exists(microservice_path):
        raise ValueError(f'Path {microservice_path} does not exist')
    if not os.path.isdir(microservice_path):
        raise ValueError(f'Path {microservice_path} is not a directory')
    if len(list_dirs_no_hidden(microservice_path)) == 0:
        raise ValueError(f'Path {microservice_path} is empty. Please generate a microservice first. Type `gptdeploy generate` for further instructions.')
    if len(list_dirs_no_hidden(microservice_path)) > 1:
        raise ValueError(f'Path {microservice_path} needs to contain only one folder. Please make sure that you only have one microservice in this folder.')
    latest_version_path = get_latest_version_path(microservice_path)
    required_files = [
        'gateway/app.py',
        REQUIREMENTS_FILE_NAME,
        DOCKER_FILE_NAME,
        IMPLEMENTATION_FILE_NAME,
        TEST_EXECUTOR_FILE_NAME,
        'config.yml',
    ]
    for file_name in required_files:
        if not os.path.exists(os.path.join(latest_version_path, file_name)):
            raise ValueError(f'Path {latest_version_path} needs to contain a file named {file_name}')
