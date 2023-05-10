# from typing import Dict
#
# from dev_gpt.apis.gpt import ask_gpt
# from dev_gpt.options.generate.chains.question_answering import answer_yes_no_question
# from dev_gpt.options.generate.parser import identity_parser, boolean_parser
#
#
# def extract_information(text, info_keys) -> Dict[str, str]:
#     extracted_infos = {}
#     for info_key in info_keys:
#         is_information_in_text = answer_yes_no_question(text, f'Is a {info_key} mentioned above?')
#         if is_information_in_text:
#             extracted_info = ask_gpt(
#                 extract_information_prompt,
#                 identity_parser,
#                 text=text,
#                 info_key=info_key
#             )
#             extracted_infos[info_key] = extracted_info
#     return extracted_infos
#
#
# extract_information_prompt = '''\
# {text}
#
# Your task:
# Return all {info_key}s from above.'
# Note: you must only output your answer.
# '''