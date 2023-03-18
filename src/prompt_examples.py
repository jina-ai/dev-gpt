executor_example = "Here is an example of how an executor can be defined. It always starts with a comment:"
'''
# this executor takes ... as input and returns ... as output
# it processes each document in the following way: ...
from jina import Executor, requests, DocumentArray, Document, Deployment
class MyExecutor(Executor):
    def __init__(self, **kwargs):
        super().__init__()

    @requests
    def foo(self, docs: DocumentArray, **kwargs) => DocumentArray:
        for d in docs:
            d.text = 'hello world'"
        return docs
'''
"An executor gets a DocumentArray as input and returns a DocumentArray as output."

docarray_example = "Here is an example of how a DocumentArray can be defined:"
'''
from jina import DocumentArray, Document

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