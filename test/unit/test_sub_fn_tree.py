# insights sub fn refinement
# tools can be used in each node
## example:
import json
import os

from dev_gpt.apis.gpt import ask_gpt, GPTSession
from dev_gpt.options.generate.parser import identity_parser

example_fn_description = 'given an image, summarize the descriptions of 4 random crops of that image'
example_sub_fn_tree = {
    'description': 'given an image, summarize the descriptions of 4 random crops of that image',
    'signature': 'def summarize_image_description(image: Image) -> str:',
    'sub_fns': [
        {
            'description': 'given an image, return a list of 4 random crops of that image',
            'signature': 'def get_random_crops(image: Image) -> List[Image]:',
            'sub_fns': [
                {
                    'description': 'given an image, return a random crops of that image',
                    'signature': 'def get_random_crop(image: Image) -> Image:',
                    'sub_fns': [],
                    'external_tools': []
                }
            ],
            'external_tools': []
        },
        {
            'description': 'given a list of images, return a list of descriptions of those images',
            'signature': 'def get_image_descriptions(images: List[Image]) -> List[str]:',
            'sub_fns': [
                {
                    'description': 'given an image, return a description of that image',
                    'signature': 'def get_image_description(image: Image) -> str:',
                    'sub_fns': [],
                    'external_tools': ['whisper_api']
                }
            ],
            'external_tools': []
        },
        {
            'description': 'given a list of strings, return a string that summarizes those strings',
            'signature': 'def summarize_strings(strings: List[str]) -> str:',
            'sub_fns': [],
            'external_tools': ['gpt_3_5_turbo']
        }
    ],
    'external_tools': []
}
# constructive self-criticism can be given
# every sub task needs to be


template_generate_sub_fn_tree = f'''\
Given the task description: "{{fn_description}}",
Please write a sub-function tree that would be needed to complete this task. Consider how the task could be decomposed into smaller steps, and for each step, propose a potential function that could be used to implement that step.

Your output should include:
1. The description of each sub-function.
2. The signature of each sub-function including its inputs and outputs.
3. Any necessary sub-functions required to execute the current sub-function. If no sub-functions are required, return an empty list.
4. Any external tools that would be needed for each sub-function. If no external tools are required, return an empty list.

Your output should be a nested dictionary with the following structure.
Example for the task description "{example_fn_description}":
{json.dumps(example_sub_fn_tree).replace('{', '{{').replace('}', '}}')}'''


def test_generate_sub_fn_tree(init_gpt):
    resp = ask_gpt(template_generate_sub_fn_tree, parser=identity_parser, fn_description='''\
Given a list of email addresses, get all unique company names from them.
For all companies, get the company logo.
All logos need to be arranged on a square.
The square is returned as png.''')
