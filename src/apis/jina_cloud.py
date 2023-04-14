import hashlib
import json
import os
import re
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

import click
import hubble
import requests
from hubble.executor.helper import upload_file, archive_package, get_request_header
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


def open_streamlit_app():
    url = "http://localhost:8081/playground"
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
        'md5sum': md5_digest,
    }
    with suppress_stdout():
        headers = get_request_header()
        headers['Authorization'] = f'token {DEMO_TOKEN}'

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


def get_user_name(token=None):
    client = hubble.Client(max_retries=None, jsonify=True, token=token)
    response = client.get_user_info()
    return response['data']['name']


def _deploy_on_jcloud(flow_yaml):
    cloud_flow = CloudFlow(path=flow_yaml)
    return cloud_flow.__enter__().endpoints['gateway']


def deploy_on_jcloud(executor_name, microservice_path):
    print('Deploy a jina flow')
    full_flow_path = create_flow_yaml(microservice_path, executor_name, use_docker=True)

    for i in range(3):
        try:
            host = _deploy_on_jcloud(flow_yaml=full_flow_path)
            break
        except Exception as e:
            print(f'Could not deploy on Jina Cloud. Trying again in 5 seconds. Error: {e}')
            time.sleep(5)
        except SystemExit as e:
            raise SystemExit(f'''
Looks like your free credits ran out. 
Please add payment information to your account and try again.
Visit https://cloud.jina.ai/
            ''') from e
    if i == 2:
        raise Exception('''
Could not deploy on Jina Cloud. 
This can happen when the microservice is buggy, if it requires too much memory or if the Jina Cloud is overloaded. 
Please try again later.
'''
                        )

    print(f'''
Your Microservice is deployed.
Run the following command to start the playground:

streamlit run {os.path.join(microservice_path, "app.py")} --server.port 8081 --server.address 0.0.0.0 -- --host {host}
'''
          )
    return host


def run_streamlit_app(app_path):
    subprocess.run(['streamlit', 'run', app_path, 'server.address', '0.0.0.0', '--server.port', '8081', '--', '--host',
                    'grpc://localhost:8080'])


def run_locally(executor_name, microservice_version_path):
    if is_docker_running():
        use_docker = True
    else:
        click.echo('Docker daemon doesn\'t seem to be running. Trying to start it without docker')
        use_docker = False
    print('Run a jina flow locally')
    full_flow_path = create_flow_yaml(microservice_version_path, executor_name, use_docker)
    flow = Flow.load_config(full_flow_path)
    with flow:
        print(f'''
Your microservice started locally.
We now start the playground for you.
''')

        app_path = os.path.join(microservice_version_path, "app.py")

        # Run the Streamlit app in a separate thread
        streamlit_thread = threading.Thread(target=run_streamlit_app, args=(app_path,))
        streamlit_thread.start()

        # Open the Streamlit app in the user's default web browser
        open_streamlit_app()

        flow.block()


def create_flow_yaml(dest_folder, executor_name, use_docker):
    if use_docker:
        prefix = 'jinaai+docker'
    else:
        prefix = 'jinaai'
    flow = f'''
jtype: Flow
with:
  name: nowapi
  port: 8080
jcloud:
  version: 3.14.2.dev18
  labels:
    creator: microchain
  name: gptdeploy

executors:
  - name: {executor_name.lower()}
    uses: {prefix}://{get_user_name(DEMO_TOKEN)}/{executor_name}:latest
    {"" if use_docker else "install-requirements: True"}
    jcloud:
      resources:
        instance: C2
        capacity: spot
'''
    full_flow_path = os.path.join(dest_folder,
                                  'flow.yml')
    with open(full_flow_path, 'w') as f:
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
    with open(file_path, 'r') as file:
        content = file.read()

    replaced_content = replace_client_line(content, f"client = Client(host='{host}')")

    with open(file_path, 'w') as file:
        file.write(replaced_content)


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

    return '\n'.join(relevant_lines[-25:])


def build_docker(path):
    # The command to build the Docker image
    cmd = f"docker build -t micromagic {path}"

    # Run the command and capture the output
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    stdout, stderr = process.communicate()

    # Check if there was an error
    if process.returncode != 0:
        error_message = stderr.decode("utf-8")
        relevant_error_message = process_error_message(error_message)
        return relevant_error_message
    else:
        print("Docker build completed successfully.")
        return ''
