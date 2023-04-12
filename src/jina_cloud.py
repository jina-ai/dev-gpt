import hashlib
import json
import os
import re
import subprocess
import webbrowser
from pathlib import Path

import hubble
from hubble.executor.helper import upload_file, archive_package, get_request_header
from jcloud.flow import CloudFlow

from src.utils.io import suppress_stdout
from src.utils.string_tools import print_colored


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
        req_header = get_request_header()

    resp = upload_file(
        'https://api.hubble.jina.ai/v2/rpc/executor.push',
        'filename',
        content,
        dict_data=form_data,
        headers=req_header,
        stream=False,
        method='post',
    )
    json_lines_str = resp.content.decode('utf-8')
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


def get_user_name():
    client = hubble.Client(max_retries=None, jsonify=True)
    response = client.get_user_info()
    return response['data']['name']


def deploy_on_jcloud(flow_yaml):
    cloud_flow = CloudFlow(path=flow_yaml)
    return cloud_flow.__enter__().endpoints['gateway']


def deploy_flow(executor_name, dest_folder):
    print('Deploy a jina flow')
    flow = f'''
jtype: Flow
with:
  name: nowapi
  env:
    JINA_LOG_LEVEL: DEBUG
jcloud:
  version: 3.14.2.dev18
  labels:
    creator: microchain
  name: gptdeploy
executors:
  - name: {executor_name.lower()}
    uses: jinaai+docker://{get_user_name()}/{executor_name}:latest
    env:
      JINA_LOG_LEVEL: DEBUG
    jcloud:
      resources:
        instance: C2
        capacity: spot
'''
    full_flow_path = os.path.join(dest_folder,
                                  'flow.yml')
    with open(full_flow_path, 'w') as f:
        f.write(flow)

    for i in range(3):
        try:
            host = deploy_on_jcloud(flow_yaml=full_flow_path)
            break
        except Exception as e:
            raise e

    print(f'Flow is deployed create the playground for {host}')
    return host


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
