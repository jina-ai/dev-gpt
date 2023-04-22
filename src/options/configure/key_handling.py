import os
import platform
import re
import subprocess

import click

try:
    import psutil
except ImportError:
    psutil = None


def get_shell():
    if psutil is None:
        return None

    shell_names = ["bash", "zsh", "sh", "fish", "csh", "tcsh", "ksh", "dash"]

    # Check the SHELL environment variable first
    shell_env = os.environ.get('SHELL')
    if shell_env:
        shell_name = os.path.basename(shell_env)
        if shell_name in shell_names:
            return shell_name

    # Fallback to traversing the process tree
    try:
        p = psutil.Process(os.getpid())

        # Traverse the process tree
        while p.parent():
            p = p.parent()
            if p.name() in shell_names:
                return p.name()

        return None
    except Exception as e:
        click.echo(f"Error detecting shell: {e}")
        return None


def get_shell_config(key):
    return {
        "bash": {"config_file": "~/.bashrc", "export_line": f"export OPENAI_API_KEY={key}"},
        "zsh": {"config_file": "~/.zshrc", "export_line": f"export OPENAI_API_KEY={key}"},
        "sh": {"config_file": "~/.profile", "export_line": f"export OPENAI_API_KEY={key}"},
        "fish": {
            "config_file": "~/.config/fish/config.fish",
            "export_line": f"set -gx OPENAI_API_KEY {key}",
        },
        "csh": {"config_file": "~/.cshrc", "export_line": f"setenv OPENAI_API_KEY {key}"},
        "tcsh": {"config_file": "~/.tcshrc", "export_line": f"setenv OPENAI_API_KEY {key}"},
        "ksh": {"config_file": "~/.kshrc", "export_line": f"export OPENAI_API_KEY={key}"},
        "dash": {"config_file": "~/.profile", "export_line": f"export OPENAI_API_KEY={key}"}
    }


def set_env_variable(shell, key):
    shell_config = get_shell_config(key)
    if shell not in shell_config:
        click.echo("Sorry, your shell is not supported. Please add the key OPENAI_API_KEY manually.")
        return

    config_file = os.path.expanduser(shell_config[shell]["config_file"])

    try:
        with open(config_file, "r", encoding='utf-8') as file:
            content = file.read()

        export_line = shell_config[shell]['export_line']

        # Update the existing API key if it exists, otherwise append it to the config file
        if f"OPENAI_API_KEY" in content:
            content = re.sub(r'OPENAI_API_KEY=.*', f'OPENAI_API_KEY={key}', content, flags=re.MULTILINE)

            with open(config_file, "w", encoding='utf-8') as file:
                file.write(content)
        else:
            with open(config_file, "a", encoding='utf-8') as file:
                file.write(f"\n{export_line}\n")

        click.echo(f'''
✅ Success, OPENAI_API_KEY has been set in {config_file}.
Please restart your shell to apply the changes or run:
source {config_file}
'''
                   )

    except FileNotFoundError:
        click.echo(f"Error: {config_file} not found. Please set the environment variable manually.")


def set_api_key(key):
    system_platform = platform.system().lower()

    if system_platform == "windows":
        set_env_variable_command = f'setx OPENAI_API_KEY "{key}"'
        subprocess.call(set_env_variable_command, shell=True)
        click.echo('''
✅ Success, OPENAI_API_KEY has been set.
Please restart your Command Prompt to apply the changes.
'''
                   )

    elif system_platform in ["linux", "darwin"]:
        if "OPENAI_API_KEY" in os.environ or is_key_set_in_config_file(key):
            if not click.confirm("OPENAI_API_KEY is already set. Do you want to overwrite it?"):
                click.echo("Aborted.")
                return

        shell = get_shell()
        if shell is None:
            click.echo(
                "Error: Unable to detect your shell or psutil is not available. Please set the environment variable manually.")
            return

        set_env_variable(shell, key)
    else:
        click.echo("Sorry, this platform is not supported.")


def is_key_set_in_config_file(key):
    shell = get_shell()
    if shell is None:
        return False

    shell_config = get_shell_config(key)

    config_file = os.path.expanduser(shell_config[shell]["config_file"])

    try:
        with open(config_file, "r", encoding='utf-8') as file:
            content = file.read()
            if f"OPENAI_API_KEY" in content:
                return True
    except FileNotFoundError:
        pass

    return False
