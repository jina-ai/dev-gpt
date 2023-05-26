import json
import re

from dev_gpt.options.generate.chains.fix_based_on_error import fix_based_on_error_chain


def identity_parser(x):
    return x

def optional_tripple_back_tick_parser(x):
    if '```' in x:
        pattern = r'```(.+)```'
        x = re.findall(pattern, x, re.DOTALL)[-1]
    return x.strip()

def boolean_parser(x):
    return 'yes' in x.lower()

def json_parser(x):
    if '```' in x:
        pattern = r'```(json)?(.+)```'
        x = re.findall(pattern, x, re.DOTALL)[-1][-1]
    return json.loads(x)

def self_healing_json_parser(original_json_string):
    return fix_based_on_error_chain('I want to load my JSON string using json.loads(x) but get the following error:', 'JSON',
                                    original_json_string, parser=json_parser)
