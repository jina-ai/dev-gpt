import os

from dev_gpt.options.generate.tools.tools import get_available_tools


def test_all_tools():
    tool_lines = get_available_tools().split('\n')
    assert len(tool_lines) == 2

def test_no_search():
    os.environ['GOOGLE_API_KEY'] = ''
    tool_lines = get_available_tools().split('\n')
    assert len(tool_lines) == 1