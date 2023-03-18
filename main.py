import os
import shutil

import openai
from docarray import DocumentArray, Document
from jcloud.flow import CloudFlow
from jina import Client

from prompt_examples import executor_example, docarray_example

openai.api_key = os.environ['OPENAI_API_KEY']

input_executor_description = "Write an executor that takes image bytes as input (document.blob within a DocumentArray) and use BytesIO to convert it to PIL and detects ocr " \
                       "and returns the texts as output (as DocumentArray). "

input_test_description = 'The test downloads the image ' \
                   'https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Onlineocr.png/640px-Onlineocr.png ' \
                   ' loads it as bytes, takes it as input to the executor and asserts that the output is "Double Rhyme".'

response = openai.ChatCompletion.create(
    temperature=0,
    model="gpt-4",
    messages=[
        {
            "role": "system",
            "content": "You are a principal engineer working at Jina - an open source company."
                       "Using the Jina framework, users can define executors."
                       + executor_example
                       + docarray_example

        },
        {
            "role": "user",
            "content":
                input_executor_description
                + "The code you write is production ready. Every file starts with a 5 sentence comment of what the code is doing before the first import. Start from top-level and then fully implement all methods."
                  "First, write the executor name. (wrap the code in the string $$$start_executor_name$$$...$$$end_executor_name$$$) "
                  "The executor name only consists of lower case and upper case letters. "
                  "Then, write the executor code. (executor.py) (wrap the code in the string $$$start_executor$$$ ... $$$end_executor$$$)"
                  "In addition write the content of the requirements.txt file. Make sure to include pytest.  (wrap the code in the string $$$start_requirements$$$ ... $$$end_requirements$$$)"
                  "Then write a small unit test for the executor (test_executor.py). Start the test with an extensive comment about the test case. "
                  "Never do relative imports."
                  "(wrap the code in the string $$$start_test_executor$$$ ... $$$end_test_executor$$$)"
                  "Comments can only be written between tags."
                # "the snipped should take the local file wolf.obj as input and save the output as png files. "
                + input_test_description
                + "Finally write the Dockerfile that defines the environment with all necessary dependencies that the executor uses. "
                  'First start with comments that give an executor-specific description the Dockerfile. '
                  "It is important to make sure that all libs are installed that are required by the python packages. "
                  "The base image of the Dockerfile is FROM jinaai/jina:3.14.2-dev18-py310-standard. "
                  'The entrypoint is ENTRYPOINT ["jina", "executor", "--uses", "config.yml"] '
                  
                  "The Dockerfile runs the test during the build process. "
                  "(wrap the code in the string $$$start_dockerfile$$$ ... $$$end_dockerfile$$$)"
        },

    ]
)
plain_text = response['choices'][0]['message']['content']
print(plain_text)


def find_between(input_string, start, end):
    try:
        start_index = input_string.index(start) + len(start)
        end_index = input_string.index(end, start_index)
        return input_string[start_index:end_index]
    except ValueError:
        raise ValueError(f'Could not find {start} and {end} in {input_string}')


def clean_content(content):
    return content.replace('```', '').strip()

executor_name = find_between(plain_text, f'$$$start_executor_name$$$', f'$$$end_executor_name$$$').replace('#', '').strip()


# delete folder and recreate it

def recreate_folder(folder_path):
    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Delete the folder if it exists
        shutil.rmtree(folder_path)

    # Create the folder
    os.makedirs(folder_path)

folder = 'executor'
recreate_folder(folder)

for tag, file_name in [['executor', f'executor.py'], ['requirements', 'requirements.txt'], ['test_executor', 'test_executor.py'], ['dockerfile', 'Dockerfile']]:
    content = find_between(plain_text, f'$$$start_{tag}$$$', f'$$$end_{tag}$$$')
    clean = clean_content(content)
    full_path = os.path.join(folder, file_name)
    with open(full_path, 'w') as f:
        f.write(clean)

config_content = f'''
jtype: {executor_name}
py_modules:
  - executor.py
metas:
  name: {executor_name}
'''
with open('executor/config.yml', 'w') as f:
    f.write(config_content)

cmd = 'jina hub push executor/. --verbose'
os.system(cmd)

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

cloud_flow = CloudFlow(path=full_flow_path).__enter__()
host = cloud_flow.endpoints['gateway']
client = Client(host=host)

d = Document(uri='data/txt.png')
d.load_uri_to_blob()
response = client.post('/index', inputs=DocumentArray([d]))
response[0].summary()

# "Write an executor using open3d that takes 3d models in obj format (within a DocumentArray) as input and returns 3 2d renderings for each 3d model from unique random angles as output (as DocumentArray). Each document of the output DocumentArray has 3 chunks. Each chunk is one of the 2d renderings as png.  "

