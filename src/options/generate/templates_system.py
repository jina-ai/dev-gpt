from src.constants import FLOW_URL_PLACEHOLDER
from src.options.generate.templates_user import not_allowed_docker_string, not_allowed_executor_string

gpt_example = '''
# gpt_3_5_turbo is a language model that can be used to generate text.
you can use it to generate text given a system definition and a user prompt.
The system definition defines the agent the user is talking to.
The user prompt is precise question and the expected answer format.
Example:
# in the executor init:
gpt = GPT_3_5_Turbo_API(
    system=\'\'\'
You are a tv-reporter who is specialized in C-list celebrities.
When you get asked something like 'Who was having a date with <X>?', then you answer with a json like '{"dates": ["<Y>", "<Z>"]}'. 
You must not answer something else - only the json.
\'\'\')

# in the executor endpoint function:
response_string = gpt(prompt)
response = json.loads(response_string) # response is a string

'''

executor_example = '''Using the Jina framework, users can define executors. 
Here is an example of how an executor can be defined. It always starts with a comment:

**microservice.py**
```python
from jina import Executor, requests, DocumentArray, Document
import json
class MyInfoExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__()

    @requests() # each Executor must have exactly this decorator without parameters
    def foo(self, docs: DocumentArray, **kwargs) => DocumentArray:
        for d in docs:
            content = json.loads(d.text)
            ...
            d.text = json.dumps(modified_content) # serialized json
        return docs
```

An Executor gets a DocumentArray as input and returns a DocumentArray as output. 
'''

docarray_example = f'''A DocumentArray is a python class that can be seen as a list of Documents.
A Document is a python class that represents a single document.
Here is the protobuf definition of a Document:
```
message DocumentProto {{
  // used to store serialized json data the executor gets and returns
  string text = 1;
}}
```

Here are examples of how a DocumentArray can be defined:

```
from jina import DocumentArray, Document
import json

d1 = Document(text=json.dumps({{'he_says': 'hello'}}))

# you can load binary data into a document
url = 'https://...'
response = requests.get(url)
obj_data = response.content
base64_data = base64.b64encode(png_data).decode('utf-8')
d2 = Document(text=json.dumps({{'image': base64_data}}))

array = numpy.array([1, 2, 3])
array_list = array.tolist()
d3 = Document(text=json.dumps(array_list))
d4 = Document()
d4.text = '{{"uri": "https://.../logo.png"}}'
```
'''


client_example = f'''After the executor is deployed, it can be called via Jina Client.
Here is an example of a client file:

**client.py**
```python
from jina import Client, Document, DocumentArray
client = Client(host='{FLOW_URL_PLACEHOLDER}', protocol='http')
d = Document(uri='...')
d.load_uri_to_blob()
response = client.post('/', inputs=DocumentArray([d])) # the client must be called on '/'
print(response[0].text)
```'''


template_system_message_base = f'''It is the year 2021. 
You are a principal engineer working at Jina - an open source company.
You accurately satisfy all of the user's requirements.
To be more specific, you help the user to build a microservice with the following requirements:
```
{{task_description}}
```
and the following test scenario:
```
{{test_description}}
```

You must obey the following rules:
{not_allowed_executor_string}
{not_allowed_docker_string}'''
