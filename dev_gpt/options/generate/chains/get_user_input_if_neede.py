from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.chains.prompt_factory import context_to_string
from dev_gpt.options.generate.parser import identity_parser


def get_user_input_if_needed(context, conditions, question_gen_prompt_part):
    if all([c(context) for c in conditions]):
        return ask_gpt(
            generate_question_for_file_input_prompt,
            identity_parser,
            context_string=context_to_string(context),
            question_gen_prompt_part=question_gen_prompt_part
        )
    return None

generate_question_for_file_input_prompt = '''\
{context_string}

{question_gen_prompt_part}
Note: you must only output the question.
'''