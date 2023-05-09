from dev_gpt.options.generate.chains.question_answering import answer_yes_no_question


def is_question_true(question):
    def fn(text):
        return answer_yes_no_question(text, question)
    return fn

def is_question_false(question):
    return lambda context: not is_question_true(question)(context)
