import json

def make_prompt_friendly(text):
    return text.replace('{', '{{').replace('}', '}}')

def context_to_string(context):
    context_strings = []
    for k, v in context.items():
        if isinstance(v, dict):
            v = json.dumps(v, indent=4)
        v = make_prompt_friendly(v)
        context_strings.append(f'''\
{k}:
```
{v}
```
'''
                               )
    return '\n'.join(context_strings)
