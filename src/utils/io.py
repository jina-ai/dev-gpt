import os
import re

import subprocess
import sys
from contextlib import contextmanager


def get_microservice_path(path, microservice_name, packages, num_approach, version):
    package_path = '_'.join(packages).replace(' ', '_').lower()
    invalid_chars_regex = re.compile(r'[<>:"/\\|?*]')
    package_path = invalid_chars_regex.sub('', package_path)
    return os.path.join(path, microservice_name, f'{num_approach}_{package_path}', f'v{version}')

def persist_file(file_content, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(file_content)


def get_all_microservice_files_with_content(folder_path):
    file_name_to_content = {}
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)

        if os.path.isfile(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                file_name_to_content[filename] = content

    return file_name_to_content


@contextmanager
def suppress_stdout():
    original_stdout = sys.stdout
    sys.stdout = open(os.devnull, 'w')
    try:
        yield
    finally:
        sys.stdout.close()
        sys.stdout = original_stdout


def is_docker_running():
    try:
        if sys.platform.startswith('win'):
            command = 'docker info'
        else:
            command = 'docker info 2> /dev/null'

        subprocess.check_output(command, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False
