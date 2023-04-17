from src.constants import FLOW_URL_PLACEHOLDER

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
            d.text = json.dumps(modified_content)
        return docs
```

An Executor gets a DocumentArray as input and returns a DocumentArray as output. 
'''

docarray_example = f'''A DocumentArray is a python class that can be seen as a list of Documents.
A Document is a python class that represents a single document.
Here is the protobuf definition of a Document:
```
message DocumentProto {{
  // used to store json data the executor gets and returns
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
client = Client(host='{FLOW_URL_PLACEHOLDER}')
d = Document(uri='...')
d.load_uri_to_blob()
response = client.post('/', inputs=DocumentArray([d])) # the client must be called on '/'
print(response[0].text)
```'''


system_message_base = '''It is the year 2021. 
You are a principal engineer working at Jina - an open source company. 
You accurately satisfy all of the user's requirements.
Your goal is to build a microservice that: {description}'''