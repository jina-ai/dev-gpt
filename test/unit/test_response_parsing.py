import os

import pytest

from dev_gpt.apis.gpt import GPTSession
from dev_gpt.options.generate.generator import Generator
from dev_gpt.options.generate.parser import self_healing_json_parser


def create_code_block(with_backticks, asterisks, with_highlight_info, file_name, start_inline, content):
    code_block = f'''
{{
    "content": "{content}",
}}
'''
    if with_highlight_info:
        high_light_info = 'json'
    else:
        high_light_info = ''
    if with_backticks:
        code_block = f'```{high_light_info}\n{code_block}\n```'
    if file_name:
        code_block = f'{asterisks}{file_name}{asterisks}\n{code_block}'
    if start_inline:
        code_block = f'This is your file: {code_block}'
    return code_block


@pytest.mark.parametrize(
    'plain_text, expected1, expected2',
    [
        (
                f"""{create_code_block(True, '', False, 'test1.json', True, 'content1')}\n{create_code_block(True, '', True, '', False, 'content2')}""",
                f'{create_code_block(False, "", False, "", False, content="content1")}'.strip(),
                ''
        ),
        (
                f"""{create_code_block(True, '', True, '', False, 'content2')}""",
                '',
                f'{create_code_block(False, "", False, "", False, content="content2")}'.strip()
        )
    ]
)
def test_extract_content_from_result(plain_text, expected1, expected2):
    parsed_result1 = Generator.extract_content_from_result(plain_text, 'test1.json', False, True)
    assert parsed_result1 == expected1
    parsed_result2 = Generator.extract_content_from_result(plain_text, 'test100.json', True, False)
    assert parsed_result2 == expected2


def test_self_healing_json_parser(init_gpt):
    json_response = '''\
```json
{
    "1": "Change line 7 of microservice.py to 'pdf_file = input_dict['pdf_file'].encode('latin-1')' to convert the bytes object to a string before passing it to PyPDF2.",
    "2": "Change line 7 of microservice.py to 'pdf_file = input_dict['pdf_file'].decode('utf-8')' to decode the bytes object to a string before passing it to PyPDF2.",
    "3": "Change line 13 of test_microservice.py to 'input_dict = {"pdf_file": 'Sample PDF file content'.encode('latin-1')}' to encode the string to a bytes object before passing it to func.",
    "4": "Change line 13 of test_microservice.py to 'input_dict = {"pdf_file": 'Sample PDF file content'.decode('utf-8')}' to decode the string to a bytes object before passing it to func."
}
```'''
    parsed_json = self_healing_json_parser(json_response)
    for key in ['1', '2', '3', '4']:
        assert key in parsed_json
        assert 'Change' in parsed_json[key]