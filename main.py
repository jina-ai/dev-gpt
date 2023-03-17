import os

import openai
from docarray import DocumentArray, Document
from jcloud.flow import CloudFlow
from jina import Client

openai.api_key = os.environ['OPENAI_API_KEY']

executor_description = "Write an executor that takes image bytes as input (document.blob within a DocumentArray) and use BytesIO to convert it to PIL and detects ocr " \
                       "and returns the texts as output (as DocumentArray). "

test_description = 'The test downloads the image ' \
                   'https://double-rhyme.com/logo_en_white2.png ' \
                   ' loads it as bytes, takes it as input to the executor and asserts that the output is "Double Rhyme".'

response = openai.ChatCompletion.create(
    temperature=0,
    model="gpt-3.5-turbo",
    messages=[
        {
            "role": "system",
            "content": "You are a principal engineer working at Jina - an open source company."
                       "Using the Jina framework, users can define executors."
                       "Here is an example of how an executor can be defined:"
                       '''
                       class MyExecutor(Executor):
                           def __init__(self, **kwargs):
                               super().__init__()
                               
                           @requests
                           def foo(self, docs: DocumentArray, **kwargs) => DocumentArray:
                               for d in docs:
                                   d.text = 'hello world'"
                               return docs
                       '''
                       "these imports are needed:"
                       '''
                       from jina import Executor, requests, DocumentArray, Document, Deployment
                       '''
                       "An executor gets a DocumentArray as input and returns a DocumentArray as output."
                       "Here is an example of how a DocumentArray can be defined:"
                       '''
                       d1 = Document(text='hello')
                       d2 = Document(blob=b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x03L\x00\x00\x01\x18\x08\x06\x00\x00\x00o...')
                       d3 = Document(tensor=numpy.array([1, 2, 3]), chunks=[Document(uri=/local/path/to/file)]
                       d4 = Document(
                           uri='https://docs.docarray.org',
                           tags={'foo': 'bar'},
                       )
                       
                       docs = DocumentArray([
                           d1, d2, d3, d4
                       ])
                       '''
                       "these imports are needed:"
                       '''
                       from jina import DocumentArray, Document
                       '''

        },
        {
            "role": "user",
            "content":
                executor_description
                + "The code you write is production ready. Every file starts with a 5 sentence comment of what the code is doing before the first import. Start from top-level and then fully implement all methods."
                  "First, write the executor name. (wrap the code in the string $$$start_executor_name$$$ ... $$$end_executor_name$$$)"
                  "Then, write the executor code. (wrap the code in the string $$$start_executor$$$ ... $$$end_executor$$$)"
                  "In addition write the content of the requirements.txt file. Make sure to include pytest.  (wrap the code in the string $$$start_requirements$$$ ... $$$end_requirements$$$)"
                  "Then write a small unit test for the executor. (wrap the code in the string $$$start_test_executor$$$ ... $$$end_test_executor$$$)"
                # "the snipped should take the local file wolf.obj as input and save the output as png files. "
                + test_description
                + "Finally write the Dockerfile that defines the environment with all necessary dependencies which the executor uses. "
                  "It is important to make sure that all libs are installed that are required by the python packages. "
                  "The base image of the Dockerfile is jinaai/jina:3.14.2-dev18-py310-standard. "
                  "The Dockerfile runs the test during the build process (wrap the code in the string $$$start_dockerfile$$$ ... $$$end_dockerfile$$$)"
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

executor_name = find_between(plain_text, f'$$$start_executor_name$$$', f'$$$end_executor_name$$$').strip()

for tag, file_name in [['executor', f'{executor_name}py'], ['requirements', 'requirements.txt'], ['test_executor', 'test_executor.py'], ['ockerfile', 'Dockerfile']]:
    content = find_between(plain_text, f'$$$start_{tag}$$$', f'$$$end_{tag}$$$')
    clean = clean_content(content)
    folder = 'executor'
    full_path = os.path.join(folder, file_name)
    os.makedirs(folder, exist_ok=True)
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

d = Document(uri='https://double-rhyme.com/logo_en_white2.png')
d.load_uri_to_blob()
response = client.post('/index', inputs=DocumentArray([d]))
response[0].summary()

# "Write an executor using open3d that takes 3d models in obj format (within a DocumentArray) as input and returns 3 2d renderings for each 3d model from unique random angles as output (as DocumentArray). Each document of the output DocumentArray has 3 chunks. Each chunk is one of the 2d renderings as png.  "

