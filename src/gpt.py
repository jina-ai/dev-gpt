import os

import openai

from src.utils.string import print_colored

openai.api_key = os.environ['OPENAI_API_KEY']

def get_response(system_definition, user_query):
    print_colored('system_definition', system_definition, 'magenta')
    print_colored('user_query', user_query, 'blue')
    response = openai.ChatCompletion.create(
        temperature=0,
        model="gpt-4",
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
    content = response['choices'][0]['message']['content']
    print_colored('agent response', content, 'green')
    return content