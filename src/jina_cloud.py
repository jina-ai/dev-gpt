import os
from multiprocessing.connection import Client

import hubble
from jcloud.flow import CloudFlow
from jina import Flow

from src.constants import FLOW_URL_PLACEHOLDER


def push_executor(dir_path):
    cmd = f'jina hub push {dir_path}/. --verbose --replay'
    os.system(cmd)

def get_user_name():
    client = hubble.Client(max_retries=None, jsonify=True)
    response = client.get_user_info()
    return response['data']['name']


def deploy_on_jcloud(flow_yaml):
    cloud_flow = CloudFlow(path=flow_yaml)
    return cloud_flow.__enter__().endpoints['gateway']



def deploy_flow(executor_name, do_validation, dest_folder):
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

    if do_validation:
        print('try local execution')
        flow = Flow.load_config(full_flow_path)
        with flow:
            pass
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


