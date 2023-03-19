from src.constants import FLOW_URL_PLACEHOLDER

executor_example = "Here is an example of how an executor can be defined. It always starts with a comment:"
'''

# this executor takes ... as input and returns ... as output
# it processes each document in the following way: ...
from jina import Executor, requests, DocumentArray, Document
class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__()

    @requests
    def foo(self, docs: DocumentArray, **kwargs) => DocumentArray:
        for d in docs:
            d.text = 'hello world'"
        return docs
'''
"An executor gets a DocumentArray as input and returns a DocumentArray as output. "

docarray_example = (
    "A DocumentArray is a python class that can be seen as a list of Documents. "
    "A Document is a python class that represents a single document. "
    "Here is the protobuf definition of a Document: "
'''

message DocumentProto {
  // A hexdigest that represents a unique document ID
  string id = 1;

  oneof content {
    // the raw binary content of this document, which often represents the original document when comes into jina
    bytes blob = 2;

    // the ndarray of the image/audio/video document
    NdArrayProto tensor = 3;

    // a text document
    string text = 4;
  }

  // a uri of the document is a remote url starts with http or https or data URI scheme
  string uri = 5;

  // list of the sub-documents of this document (recursive structure)
  repeated DocumentProto chunks = 6;

  // the matched documents on the same level (recursive structure)
  repeated DocumentProto matches = 7;

  // the embedding of this document
  NdArrayProto embedding = 8;

  // a structured data value, consisting of field which map to dynamically typed values.
  google.protobuf.Struct tags = 9;

}
'''
    "Here is an example of how a DocumentArray can be defined: "
'''

from jina import DocumentArray, Document

d1 = Document(text='hello')
d2 = Document(blob=b'\\x89PNG\\r\\n\\x1a\\n\\x00\\x00\\x00\\rIHDR\\x00\\x00\\x03L\\x00\\x00\\x01\\x18\\x08\\x06\\x00\\x00\\x00o...')
d3 = Document(tensor=numpy.array([1, 2, 3]), chunks=[Document(uri=/local/path/to/file)]
d4 = Document(
   uri='https://docs.docarray.org/img/logo.png',
   tags={'foo': 'bar'},
)
d5 = Document()
d5.tensor = np.ones((2,4))
d5.uri = 'https://audio.com/audio.mp3'
d6 = Document()
d6.blob = b'RIFF\\x00\\x00\\x00\\x00WAVEfmt \\x10\\x00...'
docs = DocumentArray([
   d1, d2, d3, d4
])
# the document has a helper function load_uri_to_blob:
# For instance, d4.load_uri_to_blob() downloads the file from d4.uri and stores it in d4.blob. 
# If d4.uri was something like 'https://website.web/img.jpg', then d4.blob would be something like  b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01... 
'''
)

client_example = (
"After the executor is deployed, it can be called via Jina Client. "
"Here is an example of a client file: "
f'''
from jina import Client, Document, DocumentArray
client = Client(host='{FLOW_URL_PLACEHOLDER}')
d = Document(uri='data/img.png')
d.load_uri_to_blob()
response = client.post('/process', inputs=DocumentArray([d]))
response[0].summary()
''')