import os


def get_latest_folder(path):
    return max([os.path.join(path, f) for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))])

def get_latest_version_path(microservice_path):
    executor_name_path = get_latest_folder(microservice_path)
    latest_approach_path = get_latest_folder(executor_name_path)
    latest_version_path = get_latest_folder(latest_approach_path)
    return latest_version_path

def get_executor_name(microservice_path):
    return get_latest_folder(microservice_path).split('/')[-1]


def validate_folder_is_correct(microservice_path):
    if not os.path.exists(microservice_path):
        raise ValueError(f'Path {microservice_path} does not exist')
    if not os.path.isdir(microservice_path):
        raise ValueError(f'Path {microservice_path} is not a directory')
    if len(os.listdir(microservice_path)) == 0:
        raise ValueError(f'Path {microservice_path} is empty. Please generate a microservice first. Type `gptdeploy generate` for further instructions.')
    if len(os.listdir(microservice_path)) > 1:
        raise ValueError(f'Path {microservice_path} needs to contain only one folder. Please make sure that you only have one microservice in this folder.')
    latest_version_path = get_latest_version_path(microservice_path)
    required_files = [
        'app.py',
        'requirements.txt',
        'Dockerfile',
        'config.yml',
        'microservice.py',
        'test_microservice.py',
    ]
    for file_name in required_files:
        if not os.path.exists(os.path.join(latest_version_path, file_name)):
            raise ValueError(f'Path {latest_version_path} needs to contain a file named {file_name}')
