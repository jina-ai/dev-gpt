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


def get_shell_config(name, key):
    return {
        "bash": {"config_file": "~/.bashrc", "export_line": f"export {name}={key}"},
        "zsh": {"config_file": "~/.zshrc", "export_line": f"export {name}={key}"},
        "sh": {"config_file": "~/.profile", "export_line": f"export {name}={key}"},
        "fish": {
            "config_file": "~/.config/fish/config.fish",
            "export_line": f"set -gx {name} {key}",
        },
        "csh": {"config_file": "~/.cshrc", "export_line": f"setenv {name} {key}"},
        "tcsh": {"config_file": "~/.tcshrc", "export_line": f"setenv {name} {key}"},
        "ksh": {"config_file": "~/.kshrc", "export_line": f"export {name}={key}"},
        "dash": {"config_file": "~/.profile", "export_line": f"export {name}={key}"}
    }


def set_env_variable(shell, name, key):
    shell_config = get_shell_config(name, key)
    if shell not in shell_config:
        click.echo(f"Sorry, your shell is not supported. Please add the key {name} manually.")
        return

    config_file = os.path.expanduser(shell_config[shell]["config_file"])

    try:
        with open(config_file, "r", encoding='utf-8') as file:
            content = file.read()

        export_line = shell_config[shell]['export_line']

        # Update the existing API key if it exists, otherwise append it to the config file
        if f"{name}" in content:
            content = re.sub(rf'{name}=.*', f'{name}={key}', content, flags=re.MULTILINE)

            with open(config_file, "w", encoding='utf-8') as file:
                file.write(content)
        else:
            with open(config_file, "a", encoding='utf-8') as file:
                file.write(f"\n{export_line}\n")

        click.echo(f'''
✅ Success, {name} has been set in {config_file}.
Please restart your shell to apply the changes or run:
source {config_file}
'''
                   )

    except FileNotFoundError:
        click.echo(f"Error: {config_file} not found. Please set the environment variable manually.")


def set_api_key(name, key):
    system_platform = platform.system().lower()

    if system_platform == "windows":
        set_env_variable_command = f'setx {name} "{key}"'
        subprocess.call(set_env_variable_command, shell=True)
        click.echo(f'''
✅ Success, {name} has been set.
Please restart your Command Prompt to apply the changes.
'''
                   )

    elif system_platform in ["linux", "darwin"]:
        if f"{name}" in os.environ or is_key_set_in_config_file(key):
            if not click.confirm(f"{name} is already set. Do you want to overwrite it?"):
                click.echo("Aborted.")
                return

        shell = get_shell()
        if shell is None:
            click.echo(
                "Error: Unable to detect your shell or psutil is not available. Please set the environment variable manually.")
            return

        set_env_variable(shell, name, key)
    else:
        click.echo("Sorry, this platform is not supported.")


def is_key_set_in_config_file(name, key):
    shell = get_shell()
    if shell is None:
        return False

    shell_config = get_shell_config(name, key)

    config_file = os.path.expanduser(shell_config[shell]["config_file"])

    try:
        with open(config_file, "r", encoding='utf-8') as file:
            content = file.read()
            if f"{name}" in content:
                return True
    except FileNotFoundError:
        pass

    return False
