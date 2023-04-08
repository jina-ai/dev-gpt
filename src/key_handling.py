import os
import platform
import subprocess
import click

try:
    import psutil
except ImportError:
    psutil = None


def get_shell():
    if psutil is None:
        return None

    try:
        p = psutil.Process(os.getpid())
        while p.parent() and p.parent().name() != "init":
            p = p.parent()
        return p.name()
    except Exception as e:
        click.echo(f"Error detecting shell: {e}")
        return None


def set_env_variable(shell, key):
    shell_config = {
        "bash": {"config_file": "~/.bashrc", "export_line": f"export OPENAI_API_KEY={key}"},
        "zsh": {"config_file": "~/.zshrc", "export_line": f"export OPENAI_API_KEY={key}"},
        "fish": {
            "config_file": "~/.config/fish/config.fish",
            "export_line": f"set -gx OPENAI_API_KEY {key}",
        },
    }

    if shell not in shell_config:
        click.echo("Sorry, your shell is not supported.")
        return

    config_file = os.path.expanduser(shell_config[shell]["config_file"])

    with open(config_file, "a") as file:
        file.write(f"\n{shell_config[shell]['export_line']}\n")
        click.echo(f"OPENAI_API_KEY has been set in {config_file}.")


def set_api_key(key):
    system_platform = platform.system().lower()

    if system_platform == "windows":
        set_env_variable_command = f'setx OPENAI_API_KEY "{key}"'
        subprocess.call(set_env_variable_command, shell=True)
        click.echo("OPENAI_API_KEY has been set.")
    elif system_platform in ["linux", "darwin"]:
        if "OPENAI_API_KEY" in os.environ:
            if not click.confirm("OPENAI_API_KEY is already set. Do you want to overwrite it?"):
                click.echo("Aborted.")
                return

        shell = get_shell()
        if shell is None:
            click.echo("Error: Unable to detect your shell or psutil is not available. Please set the environment variable manually.")
            return

        set_env_variable(shell, key)
    else:
        click.echo("Sorry, this platform is not supported.")


