import json
import re


def identity_parser(x):
    return x

def boolean_parser(x):
    return 'yes' in x.lower()

def json_parser(x):
    if '```' in x:
        pattern = r'```(.+)```'
        x = re.findall(pattern, x, re.DOTALL)[-1]
    return json.loads(x)
