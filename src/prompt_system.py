from src.constants import FLOW_URL_PLACEHOLDER

executor_example = '''
Using the Jina framework, users can define executors. 
Here is an example of how an executor can be defined. It always starts with a comment:

**executor.py**
```python
# this executor binary files as input and returns the length of each binary file as output
from jina import Executor, requests, DocumentArray, Document
class MyInfoExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__()

    @requests() # each executor must have exactly this decorator without parameters
    def foo(self, docs: DocumentArray, **kwargs) => DocumentArray:
        for d in docs:
            d.load_uri_to_blob()
            d.blob = None
        return docs
```

An executor gets a DocumentArray as input and returns a DocumentArray as output. 
'''

docarray_example = f'''
A DocumentArray is a python class that can be seen as a list of Documents.
A Document is a python class that represents a single document.
Here is the protobuf definition of a Document:

message DocumentProto {{
  // A hexdigest that represents a unique document ID
  string id = 1;

  oneof content {{
    // the raw binary content of this document, which often represents the original document when comes into jina
    bytes blob = 2;

    // the ndarray of the image/audio/video document
    NdArrayProto tensor = 3;

    // a text document
    string text = 4;
  }}

  // a uri of the document is a remote url starts with http or https or data URI scheme
  string uri = 5;

  // list of the sub-documents of this document (recursive structure)
  repeated DocumentProto chunks = 6;

  // the matched documents on the same level (recursive structure)
  repeated DocumentProto matches = 7;

  // the embedding of this document
  NdArrayProto embedding = 8;
}}

Here is an example of how a DocumentArray can be defined:

from jina import DocumentArray, Document

d1 = Document(text='hello')

# you can load binary data into a document
url = 'https://...'
response = requests.get(url)
obj_data = response.content
d2 = Document(blob=obj_data) # blob is bytes like b'\\x89PNG\\r\\n\\x1a\\n...'

d3 = Document(tensor=numpy.array([1, 2, 3]), chunks=[Document(uri=/local/path/to/file)]
d4 = Document(
   uri='https://docs.docarray.org/img/logo.png',
)
d5 = Document()
d5.tensor = np.ones((2,4))
d5.uri = 'https://audio.com/audio.mp3'
d6 = Document()
d6.blob # like b'RIFF\\x00\\x00\\x00\\x00WAVEfmt \\x10\\x00...'
docs = DocumentArray([
   d1, d2, d3, d4
])
d7 = Document()
d7.text = 'test string'
d8 = Document()
d8.text = json.dumps([{{"id": "1", "text": ["hello", 'test']}}, {{"id": "2", "text": "world"}}])
# the document has a helper function load_uri_to_blob:
# For instance, d4.load_uri_to_blob() downloads the file from d4.uri and stores it in d4.blob. 
# If d4.uri was something like 'https://website.web/img.jpg', then d4.blob would be something like  b'\\xff\\xd8\\xff\\xe0\\x00\\x10JFIF\\x00\\x01\\x01... 
'''


client_example = f'''
After the executor is deployed, it can be called via Jina Client.
Here is an example of a client file:

**client.py**
```python
from jina import Client, Document, DocumentArray
client = Client(host='{FLOW_URL_PLACEHOLDER}')
d = Document(uri='...')
d.load_uri_to_blob()
response = client.post('/', inputs=DocumentArray([d])) # the client must be called on '/'
print(response[0].text)
```
'''


system_base_definition = f'''
You are a principal engineer working at Jina - an open source company."  
{executor_example}
{docarray_example}
{client_example}
'''