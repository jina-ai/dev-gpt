import os

from jcloud.flow import CloudFlow


def push_executor():
    cmd = 'jina hub push executor/. --verbose'
    os.system(cmd)


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
        team: now
    gateway:
      jcloud:
        expose: true
    executors:
      - name: {executor_name.lower()}
        uses: jinaai+docker://team-now-prod/{executor_name}
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

    return CloudFlow(path=full_flow_path).__enter__().endpoints['gateway']