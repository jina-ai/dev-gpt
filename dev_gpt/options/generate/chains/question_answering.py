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
        pros_and_cons_prompt,
        question=question,
        text=text,
    )
    # count words "yes" and "no" in pros and cons
    yes_count = pros_and_cons.lower().count('yes')
    no_count = pros_and_cons.lower().count('no')
    return yes_count > no_count

    # return ask_gpt(
    #     question_prompt,
    #     boolean_parser,
    #     text=text,
    #     question=question,
    #     pros_and_cons=pros_and_cons,
    # )

pros_and_cons_prompt = '''\
# Context
{text}
# Question
{question}
Note: You must not answer the question. Instead, give up to 5 bullet points (10 words) arguing why the question should be answered with yes or no. \
Each bullet point ends with either "- yes" or "- no".'''

question_prompt = '''\
# Context
{text}

# Pros and Cons
{pros_and_cons}

# Question
Based on the pros and cons, answer the following question: {question}
Note: You must answer the question correctly by saying something like "since <explanagion>, the answer is yes" or "since <explanagion>, the answer is no".
'''
