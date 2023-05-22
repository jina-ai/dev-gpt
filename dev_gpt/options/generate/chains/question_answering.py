from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.parser import boolean_parser, identity_parser


def is_question_true(question):
    def fn(text):
        return answer_yes_no_question(text, question)

    return fn


def is_question_false(question):
    return lambda context: not is_question_true(question)(context)


def answer_yes_no_question(text, question):
    pros_and_cons = ask_gpt(
        pros_and_cons_prompt.format(
            question=question,
            text=text,
        ),
        identity_parser,
    )

    return ask_gpt(
        question_prompt.format(
            text=text,
            question=question,
            pros_and_cons=pros_and_cons,
        ),
        boolean_parser)

pros_and_cons_prompt = '''\
# Context
{text}
# Question
{question}
Note: You must not answer the question. Instead, give up to 5 bullet points (10 words) arguing why the question should be answered with true or false.'''

question_prompt = '''\
# Context
{text}
# Question
{question}
Note: You must answer "yes" or "no".
'''
