import json


def context_to_string(context):
    context_strings = []
    for k, v in context.items():
        if isinstance(v, dict):
            v = json.dumps(v, indent=4)
        v = v.replace('{', '{{').replace('}', '}}')
        context_strings.append(f'''\
{k}:
```
{v}
```
'''
                               )
    return '\n'.join(context_strings)
