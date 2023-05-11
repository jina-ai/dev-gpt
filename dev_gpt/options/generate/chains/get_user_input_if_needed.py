from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.prompt_factory import context_to_string
from dev_gpt.options.generate.parser import identity_parser


def get_user_input_if_needed(context, conditions, question_gen_prompt_part):
    if all([c(context_to_string(context)) for c in conditions]):
        question_to_user = ask_gpt(
            generate_question_for_file_input_prompt,
            identity_parser,
            context_string=context_to_string(context),
            question_gen_prompt_part=question_gen_prompt_part
        )
        return input(question_to_user)
    return None

generate_question_for_file_input_prompt = '''\
{context_string}

{question_gen_prompt_part}
Note: you must only output the question.
'''