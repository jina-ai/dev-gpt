import os
from time import sleep

import openai
from openai.error import RateLimitError, Timeout

from src.utils.io import timeout_generator_wrapper
from src.utils.string_tools import print_colored

openai.api_key = os.environ['OPENAI_API_KEY']

def get_response(system_definition, user_query):
    print_colored('system_definition', system_definition, 'magenta')
    print_colored('user_query', user_query, 'blue')
    for i in range(10):
        try:
            response_generator = openai.ChatCompletion.create(
                temperature=0,
                max_tokens=5_000,
                model="gpt-4",
                stream=True,
                messages=[
                    {
                        "role": "system",
                        "content": system_definition

                    },
                    {
                        "role": "user",
                        "content":
                            user_query
                    },

                ]
            )
            response_generator_with_timeout = timeout_generator_wrapper(response_generator, 5)

            complete_string = ''
            for chunk in response_generator_with_timeout:
                delta = chunk['choices'][0]['delta']
                if 'content' in delta:
                    content = delta['content']
                    print_colored('' if complete_string else 'Agent response:', content, 'green', end='')
                    complete_string += content
            return complete_string
        except (RateLimitError, Timeout, ConnectionError) as e:
            print(e)
            print('retrying')
            sleep(3)
            continue
    raise Exception('Failed to get response')