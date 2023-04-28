import os
from src.options.generate.generator import Generator

# The cognitive difficulty level is determined by the number of Requirements the microservice has.

def test_generation_level_0(tmpdir):
    """
    Requirements:
    pip packages: ❌
    environment: ❌
    GPT-3.5-turbo: ❌
    APIs: ❌
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator("The microservice is very simple, it does not take anything as input and only outputs the word 'test'", str(tmpdir) + 'microservice', 'gpt-3.5-turbo')
    generator.generate()

def test_generation_level_1(tmpdir):
    """
    Requirements:
    pip packages: ✅
    environment: ❌
    GPT-3.5-turbo: ❌
    APIs: ❌
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator("The input is a PDF like https://www.africau.edu/images/default/sample.pdf and the output the parsed text", str(tmpdir) + 'microservice', 'gpt-3.5-turbo')
    generator.generate()