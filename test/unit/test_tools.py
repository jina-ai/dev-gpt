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
    used_tools = PM.get_used_tools('''\
This microservice listens for incoming requests and generates a fixed output of "test" upon receiving a request. \
The response sent back to the requester includes the output as a string parameter. \
No specific request parameters are required, and the response always follows a fixed schema with a single "output" parameter.'''
                      )
    assert used_tools == []