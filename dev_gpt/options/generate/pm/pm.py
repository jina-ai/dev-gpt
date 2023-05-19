from dev_gpt.apis import gpt
from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.chains.auto_refine_description import auto_refine_description
from dev_gpt.options.generate.chains.question_answering import is_question_true
from dev_gpt.options.generate.chains.translation import translation
from dev_gpt.options.generate.chains.user_confirmation_feedback_loop import user_feedback_loop
from dev_gpt.options.generate.chains.get_user_input_if_needed import get_user_input_if_needed
from dev_gpt.options.generate.parser import identity_parser, json_parser
from dev_gpt.options.generate.pm.task_tree_schema import TaskTree
from dev_gpt.options.generate.prompt_factory import make_prompt_friendly
from dev_gpt.options.generate.ui import get_random_employee


class PM:
    def refine_specification(self, microservice_description):
        pm = get_random_employee('pm')
        print(f'{pm.emoji}👋 Hi, I\'m {pm.name}, a PM at Jina AI. Gathering the requirements for our engineers.')
        original_task = microservice_description
        if not original_task:
            microservice_description = self.get_user_input(pm, 'What should your microservice do?')
        microservice_description, test_description = self.refine(microservice_description)
        print(f'''
{pm.emoji} 👍 Great, I will handover the following requirements to our engineers:
Description of the microservice:
{microservice_description}
''')
        return microservice_description, test_description

    @staticmethod
    def get_user_input(employee, prompt_to_user):
        val = input(f'{employee.emoji}❓ {prompt_to_user}\nyou: ')
        print()
        while not val:
            val = input('you: ')
        return val

    def refine(self, microservice_description):
        microservice_description, test_description = self.refine_description(microservice_description)
        # sub_task_tree = construct_sub_task_tree(microservice_description)
        # return sub_task_tree
        return microservice_description, test_description

    def refine_description(self, microservice_description):
        context = {'microservice_description': microservice_description}
        auto_refine_description(context)
        microservice_description = user_feedback_loop(context, context['microservice_description'])

        test_description = ask_gpt(
            generate_test_assertion_prompt,
            identity_parser,
            **context
        )

        test_description += self.user_input_extension_if_needed(
            context,
            microservice_description,
            condition_question='Does the request schema provided include a property that represents a file?',
            question_gen='Generate a question that requests for an example file url.',
            extension_name='Input Example',
        )
        microservice_description += self.user_input_extension_if_needed(
            context,
            microservice_description,
            condition_question='''\
Does the microservice send requests to an API beside the Google Custom Search API and gpt-3.5-turbo?''',
            question_gen='Generate a question that asks for the endpoint of the external API and an example of a request and response when interacting with the external API.',
            extension_name='Example of API usage',
            post_transformation_fn=translation(from_format='api instruction', to_format='python code snippet raw without formatting')
        )
        return microservice_description, test_description

    def user_input_extension_if_needed(
            self,
            context,
            microservice_description,
            condition_question,
            question_gen,
            extension_name,
            post_transformation_fn=None
    ):
        user_answer = get_user_input_if_needed(
            context={
                'Microservice description': microservice_description,
                'Request schema': context['request_schema'],
                'Response schema': context['response_schema'],
            },
            conditions=[
                is_question_true(condition_question),
            ],
            question_gen_prompt_part=question_gen,
        )
        if user_answer:
            if post_transformation_fn:
                user_answer = make_prompt_friendly(user_answer)
                user_answer = post_transformation_fn(user_answer)
            return f'\n{extension_name}: {user_answer}'
        else:
            return ''


client_description = '''\
Microservice description:
```
{microservice_description}
```'''



generate_test_assertion_prompt = client_description + '''
Request json schema:
```
{request_schema}
```
Response json schema:
```
{response_schema}
```
Generate the description of the weak test assertion for the microservice. The weak assertion only checks if the output of func is of the correct type (e.g. str, int, bool, etc.). Nothing else.
Note: you must only output the test description - nothing else.
Note: you must not use any formatting like triple backticks.
Note: the generated description must be less than 30 words long.
Example:
"Input for func is a base64 encoded image. The test asserts that the output of func is of type 'str'".'''

# def get_nlp_fns(self, microservice_description):
#     return ask_gpt(
#         get_nlp_fns_prompt,
#         json_parser,
#         microservice_description=microservice_description
#     )
#
def construct_sub_task_tree(self, microservice_description):
    """
    takes a microservice description and recursively constructs a tree of sub-tasks that need to be done to implement the microservice
    """
    #
    # nlp_fns = self.get_nlp_fns(
    #     microservice_description
    # )

    sub_task_tree_dict = ask_gpt(
        construct_sub_task_tree_prompt, json_parser,
        microservice_description=microservice_description,
        # nlp_fns=nlp_fns
    )
    reflections = ask_gpt(
        sub_task_tree_reflections_prompt, identity_parser,
        microservice_description=microservice_description,
        # nlp_fns=nlp_fns,
        sub_task_tree=sub_task_tree_dict,
    )
    solutions = ask_gpt(
        sub_task_tree_solutions_prompt, identity_parser,
        # nlp_fns=nlp_fns,
        microservice_description=microservice_description, sub_task_tree=sub_task_tree_dict,
        reflections=reflections,
    )
    sub_task_tree_updated = ask_gpt(
        sub_task_tree_update_prompt,
        json_parser,
        microservice_description=microservice_description,
        # nlp_fns=nlp_fns,
        sub_task_tree=sub_task_tree_dict, solutions=solutions
    )
    # for task_dict in self.iterate_over_sub_tasks(sub_task_tree_updated):
    #     task_dict.update(self.get_additional_task_info(task_dict['task']))

    sub_task_tree = TaskTree.parse_obj(sub_task_tree_updated)
    return sub_task_tree

# def get_additional_task_info(self, sub_task_description):
#     additional_info_dict = self.get_additional_infos(
#         description=sub_task_description,
#         parameter={
#             'display_name': 'Task description',
#             'text': sub_task_description,
#         },
#         potentially_required_information_list=[
#             {
#                 'field_name': 'api_key',
#                 'display_name': 'valid API key',
#             }, {
#                 'field_name': 'database_access',
#                 'display_name': 'database access',
#             }, {
#                 'field_name': 'documentation',
#                 'display_name': 'documentation',
#             }, {
#                 'field_name': 'example_api_call',
#                 'display_name': 'curl command or sample code for api call',
#             },
#         ],
#
#     )
#     return additional_info_dict

# def get_additional_infos(self, description, parameter, potentially_required_information_list):
#     additional_info_dict = {}
#     for potentially_required_information in potentially_required_information_list:
#         is_task_requiring_information = ask_gpt(
#             is_task_requiring_information_template,
#             boolean_parser,
#             description=description,
#             description_title=parameter['display_name'],
#             description_text=parameter['text'],
#             potentially_required_information=potentially_required_information
#         )
#         if is_task_requiring_information:
#             generated_question = ask_gpt(
#                 generate_question_for_required_information_template,
#                 identity_parser,
#                 description=description,
#                 description_title=parameter['display_name'],
#                 description_text=parameter['text'],
#                 potentially_required_information=potentially_required_information
#             )
#             user_answer = input(generated_question)
#             additional_info_dict[potentially_required_information] = user_answer
#     return additional_info_dict

# def iterate_over_sub_tasks(self, sub_task_tree_updated):
#     sub_tasks = sub_task_tree_updated['sub_tasks'] if 'sub_tasks' in sub_task_tree_updated else []
#     for sub_task in sub_tasks:
#         yield sub_task
#         yield from self.iterate_over_sub_tasks(sub_task)
#
# def iterate_over_sub_tasks_pydantic(self, sub_task_tree: TaskTree) -> Generator[TaskTree, None, None]:
#     sub_tasks = sub_task_tree.sub_fns
#     for sub_task in sub_tasks:
#         yield sub_task
#         yield from self.iterate_over_sub_tasks_pydantic(sub_task)

# def add_additional_specifications(self, microservice_description, request_schema, response_schema):
#     questions = ask_gpt(
#         ask_questions_prompt, identity_parser,
#         microservice_description=microservice_description,
#         request_schema=request_schema, response_schema=response_schema)
#     additional_specifications = ask_gpt(
#         answer_questions_prompt,
#         identity_parser,
#         microservice_description=microservice_description,
#         request_schema=request_schema,
#         response_schema=response_schema,
#         questions=questions
#     )
#     return additional_specifications


# return self.refine_user_feedback(microservice_description)

# def refine_user_feedback(self, microservice_description):
#     while True:
#         user_feedback = input('What do you want to change?')
#         if ask_gpt(is_feedback_valuable_prompt, boolean_parser, user_feedback=user_feedback,
#                         microservice_description=microservice_description):
#             return user_feedback
#         else:
#             print('Sorry, I can not handle this feedback. Please formulate it more precisely.')



# better_description_prompt = client_description + '''
# Update the description of the Microservice to make it more precise without adding or removing information.'''


# If we want to activate this back, then it first needs to work. Currently, it outputs "no" for too many cases.
# is_feedback_valuable_prompt = client_description + '''
# User feedback:
# ```
# {user_feedback}
# ```
# Can this feedback be used to update the microservice description?
# Note: You must either answer "yes" or "no".
# Note: If the user does not want to provide feedback, then you must answer "no".'''


# summarize_description_prompt = client_description + '''
# Make the description more concise without losing any information.
# Note: You must not mention any details about algorithms or the technical implementation.
# Note: You must ignore facts that are not specified.
# Note: You must ignore facts that are not relevant.
# Note: You must ignore facts that are unknown.
# Note: You must ignore facts that are unclear.'''

construct_sub_task_tree_prompt = client_description + '''
Recursively constructs a tree of functions that need to be implemented for the endpoint_function that retrieves a json string and returns a json string.
Example:
Input: "Input: list of integers, Output: Audio file of short story where each number is mentioned exactly once."
Output:
{{
    "description": "Create an audio file containing a short story in which each integer from the provided list is seamlessly incorporated, ensuring that every integer is mentioned exactly once.",
    "python_fn_signature": "def generate_integer_story_audio(numbers: List[int]) -> str:",
    "sub_fns": [
        {{
            "description": "Generate sentence from integer.",
            "python_fn_signature": "def generate_sentence_from_integer(number: int) -> int:",
            "sub_fns": []
        }},
        {{
            "description": "Convert the story into an audio file.",
            "python_fn_signature": "def convert_story_to_audio(story: str) -> bytes:",
            "sub_fns": []
        }}
    ]
}}

Note: you must only output the json string - nothing else.
Note: you must pretty print the json string.'''

sub_task_tree_reflections_prompt = client_description + '''
Sub task tree:
```
{sub_task_tree}
```
Write down 3 arguments why the sub task tree might not perfectly represents the information mentioned in the microservice description. (5 words per argument)'''

sub_task_tree_solutions_prompt = client_description + '''
Sub task tree:
```
{sub_task_tree}
```
Reflections:
```
{reflections}
```
For each constructive criticism, write a solution (5 words) that address the criticism.'''

sub_task_tree_update_prompt = client_description + '''
Sub task tree:
```
{sub_task_tree}
```
Solutions:
```
{solutions}
```
Update the sub task tree by applying the solutions. (pretty print the json string)'''

ask_questions_prompt = client_description + '''
Request json schema:
```
{request_schema}
```
Response json schema:
```
{response_schema}
```
Ask the user up to 5 unique detailed questions (5 words) about the microservice description that are not yet answered.
'''

# answer_questions_prompt = client_description + '''
# Request json schema:
# ```
# {request_schema}
# ```
# Response json schema:
# ```
# {response_schema}
# ```
# Questions:
# ```
# {questions}
# ```
# Answer all questions where you can think of a plausible answer.
# Note: You must not answer questions with something like "...is not specified", "I don't know" or "Unknown".
# '''

# is_task_requiring_information_template = '''\
# {description_title}
# ```
# {description_text}
# ```
# Does the implementation of the {description_title} require information about "{potentially_required_information}"?
# Note: You must either answer "yes" or "no".'''

# generate_question_for_required_information_template = '''\
# {description_title}
# ```
# {description_text}
# ```
# Generate a question that asks for the information "{potentially_required_information}" regarding "{description_title}".
# Note: you must only output the question - nothing else.'''

# get_nlp_fns_prompt = client_description + '''
# Respond with all code parts that could be accomplished by GPT 3.
# Example for "Take a video and/or a pdf as input, extract the subtitles from the video and the text from the pdf, \
# summarize the extracted text and translate it to German":
# ```
# [
#     "summarize the text",
#     "translate the text to German"
# ]
# ```
# Note: only list code parts that could be expressed as a function that takes a string as input and returns a string as output.
# Note: the output must be parsable by the python function json.loads.'''

if __name__ == '__main__':
    gpt_session = gpt.GPTSession('GPT-3.5-turbo')
    first_question = 'Please specify your microservice.'
    initial_description = 'mission generator'
    # initial_description = 'convert png to svg'
    # initial_description = "Input is a list of emails. For all the companies from the emails belonging to, it gets the company's logo. All logos are arranged in a collage and returned."
    # initial_description = "Given an image, write a joke on it that is relevant to the image."
    # initial_description = "This microservice receives an image as input and generates a joke based on its content and context. The input must be a binary string of the image. The output is an image with the generated joke overlaid on it."
    initial_description = 'Build me a serch system for lottiefiles animations'
    PM().refine(initial_description)
    # PM(gpt_session).construct_sub_task_tree(initial_description)#.refine(initial_description)
