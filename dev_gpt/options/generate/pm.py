import json
import os
import re

from dev_gpt.apis import gpt


class PM:
    def __init__(self, gpt_session):
        self.gpt_session = gpt_session

    def refine(self, microservice_description):
        microservice_description = self.refine_description(microservice_description)
        sub_task_tree = self.construct_sub_task_tree(microservice_description)

    def construct_sub_task_tree(self, microservice_description):
        """
        takes a microservice description an recursively constructs a tree of sub-tasks that need to be done to implement the microservice
        Example1:
        Input: "I want to implement a microservice that takes a list of numbers and returns the sum of the numbers"
        Output:
        [
            {
            "task": "I want to implement a microservice that takes a list of numbers and returns the sum of the numbers",
            "request_json_schema": {
                "type": "array",
                "items": {
                    "type": "number"
                }
            },
            "response_json_schema": {
                "type": "number"
            },
            "sub_tasks": [
                {
                "task": "Calculate the sum of the numbers",
                "python_fn_signature": "def calculate_sum(numbers: List[float]) -> float:",
                "python_fn_docstring": "Calculates the sum of the numbers\n\nArgs:\n    numbers: a list of numbers\n\nReturns:\n    the sum of the numbers",",
                "sub_tasks": []
                },
            ]
            }
        ]
        Example2: "Input is a list of emails. For all the companies from the emails belonging to, it gets the company's logo. All logos are arranged in a collage and returned."
        [
            {
            "task": "Extract company domains from the list of emails",
            "sub_tasks": []
            },
            {
            "task": "Retrieve company logos for the extracted domains",
            "sub_tasks": [
              {
                "task": "Find logo URL for each company domain",
                "sub_tasks": []
              },
              {
                "task": "Download company logos from the URLs",
                "sub_tasks": []
              }
            ]
            },
            {
            "task": "Create a collage of company logos",
            "sub_tasks": [
              {
                "task": "Determine collage layout and dimensions",
                "sub_tasks": []
              },
              {
                "task": "Position and resize logos in the collage",
                "sub_tasks": []
              },
              {
                "task": "Combine logos into a single image",
                "sub_tasks": []
              }
            ]
            },
            {
            "task": "Return the collage of company logos",
            "sub_tasks": []
            }
            ]
        """
        sub_task_tree = self.ask_gpt(construct_sub_task_tree_prompt, json_parser, microservice_description=microservice_description)
        return sub_task_tree

    def refine_description(self, microservice_description):
        request_schema = self.ask_gpt(generate_request_schema_prompt, identity_parser,
                                      microservice_description=microservice_description)
        response_schema = self.ask_gpt(generate_output_schema_prompt, identity_parser,
                                       microservice_description=microservice_description, request_schema=request_schema)
        microservice_description = self.ask_gpt(summarize_description_and_schemas_prompt, identity_parser,
                                                microservice_description=microservice_description,
                                                request_schema=request_schema, response_schema=response_schema)

        while (user_feedback := self.get_user_feedback(microservice_description)):
            microservice_description = self.ask_gpt(add_feedback_prompt, identity_parser,
                                                    microservice_description=microservice_description,
                                                    user_feedback=user_feedback)
        return microservice_description

    def get_user_feedback(self, microservice_description):
        while True:
            user_feedback = input(f'I suggest that we implement the following microservice:\n{microservice_description}\nDo you agree? [y/n]')
            if user_feedback.lower() in ['y', 'yes', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay']:
                print('Great! I will hand this over to the developers!')
                return None
            elif user_feedback.lower() in ['n', 'no', 'nope', 'nah', 'nay', 'not']:
                return input('What do you want to change?')
                # return self.refine_user_feedback(microservice_description)

    # Prompting
    def ask_gpt(self, prompt_template, parser, **kwargs):
        prompt = prompt_template.format(**kwargs)
        conversation = self.gpt_session.get_conversation(
            [],
            print_stream=os.environ['VERBOSE'].lower() == 'true',
            print_costs=False
        )
        agent_response_raw = conversation.chat(prompt, role='user')
        agent_response = parser(agent_response_raw)
        return agent_response

    # def refine_user_feedback(self, microservice_description):
    #     while True:
    #         user_feedback = input('What do you want to change?')
    #         if self.ask_gpt(is_feedback_valuable_prompt, boolean_parser, user_feedback=user_feedback,
    #                         microservice_description=microservice_description):
    #             return user_feedback
    #         else:
    #             print('Sorry, I can not handle this feedback. Please formulate it more precisely.')




def identity_parser(x):
    return x

def boolean_parser(x):
    return 'yes' in x.lower()

def json_parser(x):
    if '```' in x:
        pattern = r'```(.+)```'
        x = re.findall(pattern, x, re.DOTALL)[-1]
    return json.loads(x)

client_description = '''\
Microservice description:
```
{microservice_description}
```'''

generate_request_schema_prompt = client_description + '''
Generate the lean request json schema of the Microservice.
Note: If you are not sure about the details, the come up with the minimal number of parameters possible.'''

generate_output_schema_prompt = client_description + '''
request json schema:
```
{request_schema}
```
Generate the lean response json schema for the Microservice.
Note: If you are not sure about the details, the come up with the minimal number of parameters possible.'''

# If we want to activate this back, then it first needs to work. Currently, it outputs "no" for too many cases.
# is_feedback_valuable_prompt = client_description + '''
# User feedback:
# ```
# {user_feedback}
# ```
# Can this feedback be used to update the microservice description?
# Note: You must either answer "yes" or "no".
# Note: If the user does not want to provide feedback, then you must answer "no".'''


summarize_description_and_schemas_prompt = client_description + '''
request json schema:
```
{request_schema}
```
response json schema:
```
{response_schema}
```
Update the microservice description by incorporating information about the request and response parameters in a concise way without losing any information.
Note: You must not mention any details about algorithms or the technical implementation.'''

add_feedback_prompt = client_description + '''
User feedback:
```
{user_feedback}
```
Update the microservice description by incorporating the user feedback in a concise way without losing any information.'''

summarize_description_prompt = client_description + '''
Make the description more concise without losing any information.
Note: You must not mention any details about algorithms or the technical implementation.
Note: You must ignore facts that are not specified.
Note: You must ignore facts that are not relevant.
Note: You must ignore facts that are unknown.
Note: You must ignore facts that are unclear.'''


construct_sub_task_tree_prompt = client_description + '''\
Recursively constructs a tree of sub-tasks that need to be done to implement the microservice
Example1:
Input: "I want to implement a microservice that takes a list of numbers and returns the sum of the numbers"
Output:
[
    {{
        "task": "I want to implement a microservice that takes a list of numbers and returns the sum of the numbers",
        "request_json_schema": {{
            "type": "array",
            "items": {{
                "type": "number"
            }}
        }},
        "response_json_schema": {{
            "type": "number"
        }},
        "sub_tasks": [
            {{
                "task": "Calculate the sum of the numbers",
                "python_fn_signature": "def calculate_sum(numbers: List[float]) -> float:",
                "python_fn_docstring": "Calculates the sum of the numbers\\n\\nArgs:\\n    numbers: a list of numbers\\n\\nReturns:\\n    the sum of the numbers",
                "sub_tasks": []
            }}
        ]
    }}
]
Note: you must only output the json string - nothing else.
Note: you must pretty print the json string.'''

if __name__ == '__main__':
    gpt_session = gpt.GPTSession(None, 'GPT-3.5-turbo')
    first_question = 'Please specify your microservice.'
    initial_description = 'mission generator'
    # initial_description = 'convert png to svg'
    initial_description = "Input is a list of emails. For all the companies from the emails belonging to, it gets the company's logo. All logos are arranged in a collage and returned."
    initial_description = "Given an image, write a joke on it that is relevant to the image."
    PM(gpt_session).refine(initial_description)
    # PM(gpt_session).construct_sub_task_tree(initial_description)#.refine(initial_description)
