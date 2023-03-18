import os

import openai

openai.api_key = os.environ['OPENAI_API_KEY']

def get_response(system_definition, user_query):
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
    print(content)
    return content