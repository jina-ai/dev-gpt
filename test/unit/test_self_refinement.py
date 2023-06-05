import os

from dev_gpt.apis.gpt import GPTSession
from dev_gpt.options.generate.chains.auto_refine_description import enhance_description


def test_better_description(tmpdir):
    os.environ['VERBOSE'] = 'true'
    GPTSession(os.path.join(str(tmpdir), 'log.json'), model='gpt-3.5-turbo')

    better_description = enhance_description({
        'microservice_description': 'Input is a tweet that contains passive aggressive language. The output is the positive version of that tweet.'
    })
    assert 'gpt_3_5_turbo' in better_description
