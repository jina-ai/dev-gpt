import os
import shutil
import concurrent.futures
import concurrent.futures
from typing import Generator

def recreate_folder(folder_path):
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        shutil.rmtree(folder_path)
    os.makedirs(folder_path)

def persist_file(file_content, file_name):
    with open(f'executor/{file_name}', 'w') as f:
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

# def my_generator():
#     for i in range(10):
#         sleep(3)
#         yield 1
#
#
# my_generator_with_timeout = timeout_generator_wrapper(my_generator, 2.9)
# for item in my_generator_with_timeout():
#     print(item)