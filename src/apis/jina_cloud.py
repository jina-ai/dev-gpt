import hashlib
import json
import os
import re
import subprocess
import threading
import time
import webbrowser
from pathlib import Path
from typing import Dict

import click
import hubble
import requests
from hubble.executor.helper import upload_file, archive_package, get_full_version
from jcloud.flow import CloudFlow
from jina import Flow

from src.constants import DEMO_TOKEN
from src.utils.io import suppress_stdout, is_docker_running
from src.utils.string_tools import print_colored


def wait_until_app_is_ready(url):
    is_app_ready = False
    while not is_app_ready:
        try:
            response = requests.get(url)
            print('waiting for app to be ready...')
            if response.status_code == 200:
                is_app_ready = True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)


def open_streamlit_app(host: str):
    url = f"{host}/playground"
    wait_until_app_is_ready(url)
    webbrowser.open(url, new=2)


def redirect_callback(href):
    print(
        f'You need login to Jina first to use GPTDeploy\n'
        f'Please open this link if it does not open automatically in your browser: {href}'
    )
    webbrowser.open(href, new=0, autoraise=True)


def jina_auth_login():
    try:
        hubble.Client(jsonify=True).get_user_info(log_error=False)
    except hubble.AuthenticationRequiredError:
        print('You need login to Jina first to use GPTDeploy')
        print_colored('', '''
If you just created an account, it can happen that the login callback is not working.
In this case, please cancel this run, rerun your gptdeploy command and login into your account again. 
''', 'green'
                      )
        hubble.login(prompt='login', redirect_callback=redirect_callback)


def push_executor(dir_path):
    for i in range(3):
        try:
            return _push_executor(dir_path)
        except Exception as e:
            if i == 2:
                raise e
            print(f'connection error - retrying in 5 seconds...')
            time.sleep(5)

def get_request_header() -> Dict:
    """Return the header of request with an authorization token.

    :return: request header
    """
    metas, envs = get_full_version()

    headers = {
        **{f'jinameta-{k}': str(v) for k, v in metas.items()},
        **envs,
    }
    headers['Authorization'] = f'token {DEMO_TOKEN}'

    return headers

def _push_executor(dir_path):
    dir_path = Path(dir_path)
    md5_hash = hashlib.md5()
    bytesio = archive_package(dir_path)
    content = bytesio.getvalue()
    md5_hash.update(content)
    md5_digest = md5_hash.hexdigest()

    form_data = {
        'public': 'True',
        'private': 'False',
        'verbose': 'True',
        'buildEnv': f'{{"OPENAI_API_KEY": "{os.environ["OPENAI_API_KEY"]}"}}',
        'md5sum': md5_digest,
    }
    with suppress_stdout():
        headers = get_request_header()

    resp = upload_file(
        'https://api.hubble.jina.ai/v2/rpc/executor.push',
        'filename',
        content,
        dict_data=form_data,
        headers=headers,
        stream=False,
        method='post',
    )
    json_lines_str = resp.content.decode('utf-8')
    if 'AuthenticationRequiredWithBearerChallengeError' in json_lines_str:
        raise Exception('The executor is not authorized to be pushed to Jina Cloud.')
    if 'exited on non-zero code' not in json_lines_str:
        return ''
    responses = []
    for json_line in json_lines_str.splitlines():
        if 'exit code:' in json_line:
            break

        d = json.loads(json_line)

        if 'payload' in d and type(d['payload']) == str:
            responses.append(d['payload'])
        elif type(d) == str:
            responses.append(d)
    return '\n'.join(responses)

def is_executor_in_hub(microservice_name):
    url = f'https://api.hubble.jina.ai/v2/rpc/executor.list?search={microservice_name}&withAnonymous=true'
    resp = requests.get(url)
    executor_list = resp.json()['data']
    for executor in executor_list:
        if 'name' in executor and executor['name'] == microservice_name:
            return True
    return False

def get_user_name(token=None):
    client = hubble.Client(max_retries=None, jsonify=True, token=token)
    response = client.get_user_info()
    return response['data']['name']


def _deploy_on_jcloud(flow_yaml):
    cloud_flow = CloudFlow(path=flow_yaml)
    return cloud_flow.__enter__().endpoints['gateway']


def deploy_on_jcloud(executor_name, microservice_path):
    print('Deploy a jina flow')
    full_flow_path = create_flow_yaml(microservice_path, executor_name, use_docker=True, use_custom_gateway=True)

    for i in range(3):
        try:
            host = _deploy_on_jcloud(flow_yaml=full_flow_path)
            break
        except Exception as e:
            print(f'Could not deploy on Jina Cloud. Trying again in 5 seconds. Error: {e}')
            time.sleep(5)
        except SystemExit as e:
            raise SystemExit(f'''
Looks like you either ran out of credits or something went wrong in the generation and we didn't catch it.
To check if you ran out of credits, please go to https://cloud.jina.ai.
If you have credits left, please create an issue here https://github.com/jina-ai/gptdeploy/issues/new/choose
and add details on the microservice you are trying to create.
In that case, you can upgrade your GPT Deploy version, if not using latest, and try again.
''') from e
    if i == 2:
        raise Exception('''
Could not deploy on Jina Cloud. 
This can happen when the microservice is buggy, if it requires too much memory or if the Jina Cloud is overloaded. 
Please try again later.
'''
                        )

    print(f'''
Your Microservice is deployed at {host} and the playground is available at {host}/playground
We open now the playground in your browser.
''')
    open_streamlit_app(host)
    return host


def run_streamlit_app(app_path):
    subprocess.run(['streamlit', 'run', app_path, 'server.address', '0.0.0.0', '--server.port', '8081'])


def run_locally(executor_name, microservice_version_path):
    if is_docker_running():
        use_docker = True
    else:
        click.echo('''
Docker daemon doesn\'t seem to be running (possible reasons: incorrect docker installation, docker command isn\'t in system path, insufficient permissions, docker is running but unrespnsive).
It might be important to run your microservice within a docker container.
Your machine might not have all the dependencies installed.
You have 3 options:
a) start the docker daemon
b) run gptdeploy deploy... to deploy your microservice on Jina Cloud. All dependencies will be installed there.
c) try to run your microservice locally without docker. It is worth a try but might fail.
'''
                   )
        user_input = click.prompt('Do you want to run your microservice locally without docker? (Y/n)', type=str, default='y')
        if user_input.lower() != 'y':
            exit(1)
        use_docker = False
    print('Run a jina flow locally')
    full_flow_path = create_flow_yaml(microservice_version_path, executor_name, use_docker, False)
    flow = Flow.load_config(full_flow_path)
    with flow:
        print(f'''
Your microservice started locally.
We now start the playground for you.
''')

        app_path = os.path.join(microservice_version_path, 'gateway', "app.py")

        # Run the Streamlit app in a separate thread
        streamlit_thread = threading.Thread(target=run_streamlit_app, args=(app_path,))
        streamlit_thread.start()

        # Open the Streamlit app in the user's default web browser
        open_streamlit_app(host='http://localhost:8081')

        flow.block()


def create_flow_yaml(dest_folder, executor_name, use_docker, use_custom_gateway):
    if use_docker:
        prefix = 'jinaai+docker'
    else:
        prefix = 'jinaai'
    flow = f'''jtype: Flow
with:
  port: 8080
  protocol: http
jcloud:
  version: 3.15.1.dev14
  labels:
    creator: microchain
  name: gptdeploy
gateway:
    {f"uses: {prefix}://{get_user_name(DEMO_TOKEN)}/Gateway{executor_name}:latest" if use_custom_gateway else ""}
    {"" if use_docker else "install-requirements: True"}
executors:
  - name: {executor_name.lower()}
    uses: {prefix}://{get_user_name(DEMO_TOKEN)}/{executor_name}:latest
    {"" if use_docker else "install-requirements: True"}
    env:
      OPENAI_API_KEY: {os.environ['OPENAI_API_KEY']}
    jcloud:
      resources:
        instance: C2
        capacity: spot
'''
    full_flow_path = os.path.join(dest_folder,
                                  'flow.yml')
    with open(full_flow_path, 'w', encoding='utf-8') as f:
        f.write(flow)
    return full_flow_path


def replace_client_line(file_content: str, replacement: str) -> str:
    lines = file_content.split('\n')
    for index, line in enumerate(lines):
        if 'Client(' in line:
            lines[index] = replacement
            break
    return '\n'.join(lines)


def update_client_line_in_file(file_path, host):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    replaced_content = replace_client_line(content, f"client = Client(host='{host}')")

    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(replaced_content)


def shorten_logs(relevant_lines):
    # handle duplicate error messages
    for index, line in enumerate(relevant_lines):
        if '--- Captured stderr call ----' in line:
            relevant_lines = relevant_lines[:index]
    # filter pip install logs
    relevant_lines = [line for line in relevant_lines if ' Requirement already satisfied: ' not in line]
    # filter version not found logs
    for index, line in enumerate(relevant_lines):
        if 'ERROR: Could not find a version that satisfies the requirement ' in line:
            start_and_end = line[:150] + '...' + line[-150:]
            relevant_lines[index] = start_and_end
    return relevant_lines


def clean_color_codes(response):
    response = re.sub(r'\x1b\[[0-9;]*m', '', response)
    return response

def process_error_message(error_message):
    lines = error_message.split('\n')

    relevant_lines = []

    pattern = re.compile(r"^#\d+ \[[ \d]+/[ \d]+\]")  # Pattern to match lines like "#11 [7/8]"
    last_matching_line_index = None

    for index, line in enumerate(lines):
        if pattern.match(line):
            last_matching_line_index = index

    if last_matching_line_index is not None:
        relevant_lines = lines[last_matching_line_index:]

    relevant_lines = shorten_logs(relevant_lines)

    response = '\n'.join(relevant_lines[-100:]).strip()

    response = clean_color_codes(response)

    # the following code tests the case that the docker file is corrupted and can not be parsed
    # the method above will not return a relevant error message in this case
    # but the last line of the error message will start with "error"

    last_line = lines[-1]
    if not response and last_line.startswith('error: '):
        return last_line
    return response
