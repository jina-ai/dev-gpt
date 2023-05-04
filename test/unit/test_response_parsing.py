import pytest

from src.options.generate.generator import Generator

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

