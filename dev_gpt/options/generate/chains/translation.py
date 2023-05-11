from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.parser import identity_parser


def translation(from_format: str, to_format: str):
    def fn(text_to_translate):
        return translate(from_format, to_format, text_to_translate)

    return fn


def translate(from_format, to_format, text_to_translate):
    prompt = translation_prompt.format(
        from_format=from_format,
        to_format=to_format,
        text_to_translate=text_to_translate
    )
    return ask_gpt(prompt, identity_parser)


translation_prompt = '''\
Translate the following {from_format} to a {to_format}:
```
{text_to_translate}
```
Note: You must not output anything else - just the translation.
Note: You must not add any formatting.'''
