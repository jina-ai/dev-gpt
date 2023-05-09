import os

from dev_gpt.apis import gpt
from dev_gpt.options.generate.pm.pm import PM

def test_construct_sub_task_tree():
    os.environ['VERBOSE'] = 'true'
    gpt_session = gpt.GPTSession('test', model='gpt-3.5-turbo')
    pm = PM(gpt_session)
    microservice_description = 'This microservice receives an image as input and generates a joke based on what is depicted on the image. The input must be a binary string of the image. The output is an image with the generated joke overlaid on it.'
    sub_task_tree = pm.construct_sub_task_tree(microservice_description)