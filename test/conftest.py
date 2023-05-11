import os
from typing import List, Generator

import pytest


def input_generator(input_sequence: list) -> Generator[str, None, None]:
    """
    Creates a generator that yields input strings from the given sequence.

    :param input_sequence: A list of input strings.
    :return: A generator that yields input strings.
    """
    yield from input_sequence


@pytest.fixture
def mock_input_sequence(request, monkeypatch) -> None:
    def get_next(_):
        next_val = next(gen)
        print(f"mocked user input: {next_val}")
        return next_val

    gen = input_generator(request.param)
    monkeypatch.setattr("builtins.input", get_next)

@pytest.fixture
def microservice_dir(tmpdir) -> str:
    """
    Creates a temporary directory for a microservice.

    :param tmpdir: A temporary directory.
    :return: The path of the temporary directory.
    """
    return os.path.join(str(tmpdir), "microservice")

