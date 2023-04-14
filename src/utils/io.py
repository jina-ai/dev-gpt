import os
import shutil
import concurrent.futures
import concurrent.futures
from typing import Generator
import sys
from contextlib import contextmanager


def persist_file(file_content, file_path):
    with open(file_path, 'w') as f:
        f.write(file_content)


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