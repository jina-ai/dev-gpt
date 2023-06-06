import os

from dev_gpt.apis.gpt import GPTSession
from dev_gpt.options.generate.pm.pm import PM
from dev_gpt.options.generate.tools.tools import get_available_tools


def test_all_tools():
    tool_lines = get_available_tools().split('\n')
    assert len(tool_lines) == 2

def test_no_search():
    os.environ['GOOGLE_API_KEY'] = ''
    tool_lines = get_available_tools().split('\n')
    assert len(tool_lines) == 1

def test_get_used_apis(init_gpt):
    used_apis = PM.get_used_apis('''\
This microservice listens for incoming requests and generates a fixed output of "test" upon receiving a request. \
The response sent back to the requester includes the output as a string parameter. \
No specific request parameters are required, and the response always follows a fixed schema with a single "output" parameter.'''
                                  )
    assert used_apis == []

def test_get_used_apis_2(init_gpt):
    description = '''\
This microservice accepts a 1-minute WAV audio file of speech, encoded as a base64 binary string, and performs the following tasks:

1. Converts the audio file to text using the Whisper API.
2. Summarizes the text while preserving key facts using gpt_3_5_turbo.
3. Generates an audio file of the summarized text using a text-to-speech (TTS) library.
4. Encodes the resulting audio file as a base64 binary string.

The microservice returns the summarized text converted to audio and encoded as a base64 binary string.'''
    used_apis = PM.get_used_apis(description)
    assert used_apis == ['Whisper API', 'gpt_3_5_turbo', 'text-to-speech (TTS) library']

def test_get_used_apis_3(init_gpt):
    description = '''\
This microservice takes a PDF file as input and returns a summarized text output. \
It uses PDF parsing and natural language processing tools to generate the summary, \
and applies post-processing techniques to improve its quality. \
The input parameter is the PDF file, \
and the output parameter is the summarized text.'''
    used_apis = PM.get_used_apis(description)
    assert used_apis == []

def test_get_used_apis_4(init_gpt):
    description = '''\
This microservice receives a tweet as input \
and identifies passive aggressive language using natural language processing techniques. \
It then generates a positive version of the tweet using a text processing tool such as GPT-3. \
The positive version of the tweet is returned as output. \
The input tweet should be provided as a base64 encoded string \
and the output positive tweet will also be returned as a base64 encoded string.'''
    used_apis = PM.get_used_apis(description)
    assert used_apis == ['GPT-3']

