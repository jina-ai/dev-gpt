import os
from src.options.generate.generator import Generator

def test_generator(tmpdir):
    os.environ['VERBOSE'] = 'true'
    generator = Generator("The microservice is very simple, it does not take anything as input and only outputs the word 'test'", "my test", str(tmpdir) + 'microservice', 'gpt-3.5-turbo')
    generator.generate()
