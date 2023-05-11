from dev_gpt import env  # noqa: F401 to make sure certain environment variables are set
import functools
import os

import click

from dev_gpt.apis.gpt import configure_openai_api_key
from dev_gpt.apis.jina_cloud import jina_auth_login
from dev_gpt.options.configure.key_handling import set_api_key

def openai_api_key_needed(func):
    def wrapper(*args, **kwargs):
        configure_openai_api_key()
        return func(*args, **kwargs)
    return wrapper

def exception_interceptor(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            raise type(e)(f'''
{str(e)}

😱😱😱 Sorry for this experience. 
Could you please report an issue about this on our github repo? We'll try to fix it asap.
https://github.com/jina-ai/dev-gpt/issues/new
''') from e
    return wrapper

def path_param(func):
    @click.option('--path', default='microservice', help='Path to the generated microservice.')
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        path = os.path.expanduser(kwargs['path'])
        path = os.path.abspath(path)
        if os.path.exists(path) and os.listdir(path):
                click.echo(f"Error: The path {path} you provided via --path is not empty. Please choose a directory that does not exist or is empty.")
                exit(1)
        kwargs['path'] = path
        return func(*args, **kwargs)
    return wrapper


@click.group(invoke_without_command=True)
@click.pass_context
@exception_interceptor
def main(ctx):
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@openai_api_key_needed
@main.command()
@click.option('--description', required=False, help='Description of the microservice.')
@click.option('--model', default='gpt-4', help='GPT model to use (default: gpt-4).')
@click.option('--verbose', default=False, is_flag=True, help='Verbose mode.')   # only for development
@path_param
def generate(
        description,
        model,
        verbose,
        path,
):
    os.environ['VERBOSE'] = str(verbose)
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    if os.path.exists(path):
        if os.listdir(path):
            click.echo(f"Error: The path {path} you provided via --path is not empty. Please choose a directory that does not exist or is empty.")
            return

    from dev_gpt.options.generate.generator import Generator
    generator = Generator(description, path=path, model=model)
    generator.generate()

@openai_api_key_needed
@main.command()
@path_param
def run(path):
    from dev_gpt.options.run import Runner
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    Runner().run(path)

@openai_api_key_needed
@main.command()
@path_param
def deploy(path):
    jina_auth_login()
    from dev_gpt.options.deploy.deployer import Deployer
    path = os.path.expanduser(path)
    path = os.path.abspath(path)
    Deployer().deploy(path)

@main.command()
@click.option('--key', required=True, help='Your OpenAI API key.')
def configure(key):
    set_api_key(key)


if __name__ == '__main__':
    main()
