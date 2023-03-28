import hashlib
import json
import os
import subprocess
import re
from argparse import Namespace
from pathlib import Path

import hubble
from hubble.executor.helper import upload_file, archive_package, get_request_header
from jcloud.flow import CloudFlow
from jina import Flow



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
    flow = f'''
jtype: Flow
with:
  name: nowapi
  env:
    JINA_LOG_LEVEL: DEBUG
jcloud:
  version: 3.14.2.dev18
  labels:
    team: now
  name: mybelovedocrflow
executors:
  - name: {executor_name.lower()}
    uses: jinaai+docker://{get_user_name()}/{executor_name}:latest
    env:
      JINA_LOG_LEVEL: DEBUG
    jcloud:
      resources:
        instance: C4
        capacity: spot
'''
    full_flow_path = os.path.join(dest_folder,
                     'flow.yml')
    with open(full_flow_path, 'w') as f:
        f.write(flow)

    # print('try local execution')
    # flow = Flow.load_config(full_flow_path)
    # with flow:
    #     pass
    print('deploy flow on jcloud')
    return deploy_on_jcloud(flow_yaml=full_flow_path)


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

