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

def test_get_used_tools(tmpdir):
    os.environ['VERBOSE'] = 'true'
    GPTSession(os.path.join(str(tmpdir), 'log.json'), model='gpt-3.5-turbo')
    used_tools = PM.get_used_apis('''\
This microservice listens for incoming requests and generates a fixed output of "test" upon receiving a request. \
The response sent back to the requester includes the output as a string parameter. \
No specific request parameters are required, and the response always follows a fixed schema with a single "output" parameter.'''
                                  )
    assert used_tools == []

def test_get_used_tools_2(tmpdir):
    os.environ['VERBOSE'] = 'true'
    GPTSession(os.path.join(str(tmpdir), 'log.json'), model='gpt-3.5-turbo')
    description = '''\
This microservice accepts a 1-minute WAV audio file of speech, encoded as a base64 binary string, and performs the following tasks:

1. Converts the audio file to text using the Whisper API.
2. Summarizes the text while preserving key facts using gpt_3_5_turbo.
3. Generates an audio file of the summarized text using a text-to-speech (TTS) library.
4. Encodes the resulting audio file as a base64 binary string.

The microservice returns the summarized text converted to audio and encoded as a base64 binary string.'''
    used_tools = PM.get_used_apis(description)
    assert used_tools == ['Whisper API', 'gpt_3_5_turbo', 'text-to-speech (TTS) library']
