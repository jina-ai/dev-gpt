import os

import hubble
from jcloud.flow import CloudFlow
from jina import Flow


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
  monitoring: true
  env:
    JINA_LOG_LEVEL: DEBUG
jcloud:
  version: '3.14.2.dev18'
  labels:
    team: microchain
gateway:
  jcloud:
    expose: true
executors:
  - name: {executor_name.lower()}
    uses: jinaai+docker://{get_user_name()}/{executor_name}:latest
    env:
      JINA_LOG_LEVEL: DEBUG
    jcloud:
      expose: true
      resources:
        instance: C4
        capacity: spot
      replicas: 1
    '''
    full_flow_path = os.path.join('executor', 'flow.yml')
    with open(full_flow_path, 'w') as f:
        f.write(flow)

    # try local first
    flow = Flow.load_config(full_flow_path)
    with flow:
        pass

    return CloudFlow(path=full_flow_path).__enter__().endpoints['gateway']