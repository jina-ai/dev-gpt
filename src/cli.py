import click

from src.executor_factory import ExecutorFactory
from src.jina_cloud import jina_auth_login
from src.key_handling import set_api_key


@click.group(invoke_without_command=True)
def main():
    jina_auth_login()


@main.command()
@click.option('--description', required=True, help='Description of the executor.')
@click.option('--test', required=True, help='Test scenario for the executor.')
@click.option('--num_approaches', default=3, type=int,
              help='Number of num_approaches to use to fulfill the task (default: 3).')
@click.option('--output_path', default='executor', help='Path to the output folder (must be empty). ')
def create(
        description,
        test,
        num_approaches=3,
        output_path='executor',
):
    executor_factory = ExecutorFactory()
    executor_factory.create(description, num_approaches, output_path, test)


@main.command()
@click.option('--key', required=True, help='Your OpenAI API key.')
def configure(key):
    set_api_key(key)


if __name__ == '__main__':
    main()
