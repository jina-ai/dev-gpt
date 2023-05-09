from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.parser import boolean_parser


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