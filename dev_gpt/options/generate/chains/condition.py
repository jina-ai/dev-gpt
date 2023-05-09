from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.chains.prompt_factory import context_to_string
from dev_gpt.options.generate.parser import boolean_parser


def is_true(question):
    def fn(context):
        prompt = question_prompt.format(
            question=question,
            context_string=context_to_string(context)
        )
        return ask_gpt(prompt, boolean_parser)
    return fn

def is_false(question):
    return lambda context: not is_true(question)(context)

question_prompt = '''\
{context_string}
{question}
Note: You must answer "yes" or "no".
'''