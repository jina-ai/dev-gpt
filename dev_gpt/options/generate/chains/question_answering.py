from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.parser import boolean_parser

def is_question_true(question):
    def fn(text):
        return answer_yes_no_question(text, question)
    return fn

def is_question_false(question):
    return lambda context: not is_question_true(question)(context)


def answer_yes_no_question(text, question):
    prompt = question_prompt.format(
        question=question,
        text=text
    )
    return ask_gpt(prompt, boolean_parser)

question_prompt = '''\
{text}
{question}
Note: You must answer "yes" or "no".
'''

