import os

import concurrent.futures
import concurrent.futures
from typing import Generator
import sys
from contextlib import contextmanager

import docker
from docker import APIClient


def get_microservice_path(path, microservice_name, package, num_approach, version):
    package_path = '_'.join(package)
    return os.path.join(path, microservice_name, f'{num_approach}_{package_path}', f'v{version}')

def persist_file(file_content, file_path):
    with open(file_path, 'w') as f:
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


class GenerationTimeoutError(Exception):
    pass

def timeout_generator_wrapper(generator, timeout):
    def generator_func():
        for item in generator:
            yield item

    def wrapper() -> Generator:
        gen = generator_func()
        while True:
            try:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(next, gen)
                    yield future.result(timeout=timeout)
            except StopIteration:
                break
            except concurrent.futures.TimeoutError:
                raise GenerationTimeoutError(f"Generation took longer than {timeout} seconds")

    return wrapper()

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
        from hubble import __windows__
        _client = docker.from_env()
        # low-level client
        _raw_client = APIClient(
            base_url=docker.constants.DEFAULT_NPIPE
            if __windows__
            else docker.constants.DEFAULT_UNIX_SOCKET
        )
    except Exception:
        return False
    return True