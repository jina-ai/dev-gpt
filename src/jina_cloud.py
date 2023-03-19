import os
from multiprocessing.connection import Client

import hubble
from jcloud.flow import CloudFlow
from jina import Flow

from src.constants import FLOW_URL_PLACEHOLDER


def push_executor():
    cmd = 'jina hub push executor/. --verbose'
    os.system(cmd)

def get_user_name():
    client = hubble.Client(max_retries=None, jsonify=True)
    response = client.get_user_info()
    return response['data']['name']


def deploy_flow(executor_name):
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
    full_flow_path = os.path.join('executor', 'flow.yml')
    with open(full_flow_path, 'w') as f:
        f.write(flow)

    # try local first
    flow = Flow.load_config(full_flow_path)
    with flow:
        pass

    return CloudFlow(path=full_flow_path).__enter__().endpoints['gateway']

def replace_client_line(file_content: str, replacement: str) -> str:
    lines = file_content.split('\n')
    for index, line in enumerate(lines):
        if 'Client(' in line:
            lines[index] = replacement
            break
    return '\n'.join(lines)

def run_client_file(file_path, host):
    with open(file_path, 'r') as file:
        content = file.read()

    replaced_content = replace_client_line(content, f"client = Client(host='{host}')")


    with open(file_path, 'w') as file:
        file.write(replaced_content)

    import executor.client  # runs the client script for validation
