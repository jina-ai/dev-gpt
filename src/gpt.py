import os
from time import sleep
from typing import List, Tuple

import openai
from openai.error import RateLimitError, Timeout

from src.prompt_system import system_base_definition
from src.utils.io import timeout_generator_wrapper, GenerationTimeoutError
from src.utils.string_tools import print_colored

PRICING_GPT4_PROMPT = 0.03
PRICING_GPT4_GENERATION = 0.06
PRICING_GPT3_5_TURBO_PROMPT = 0.002
PRICING_GPT3_5_TURBO_GENERATION = 0.002

if 'OPENAI_API_KEY' not in os.environ:
    raise Exception('You need to set OPENAI_API_KEY in your environment')
openai.api_key = os.environ['OPENAI_API_KEY']


try:
    openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{
            "role": 'system',
            "content": 'test'
        }]
    )
    supported_model = 'gpt-4'
    pricing_prompt = PRICING_GPT4_PROMPT
    pricing_generation = PRICING_GPT4_GENERATION
except openai.error.InvalidRequestError:
    supported_model = 'gpt-3.5-turbo'
    pricing_prompt = PRICING_GPT3_5_TURBO_PROMPT
    pricing_generation = PRICING_GPT3_5_TURBO_GENERATION

total_chars_prompt = 0
total_chars_generation = 0


class Conversation:
    def __init__(self, prompt_list: List[Tuple[str, str]] = None, model=supported_model):
        self.model = model
        if prompt_list is None:
            prompt_list = [('system', system_base_definition)]
        self.prompt_list = prompt_list
        print_colored('system', system_base_definition, 'magenta')

    def query(self, prompt: str):
        print_colored('user', prompt, 'blue')
        self.prompt_list.append(('user', prompt))
        response = self.get_response(self.prompt_list)
        self.prompt_list.append(('assistant', response))
        return response

    def get_response(self, prompt_list: List[Tuple[str, str]]):
        global total_chars_prompt, total_chars_generation
        for i in range(10):
            try:
                response_generator = openai.ChatCompletion.create(
                    temperature=0,
                    max_tokens=2_000,
                    model=self.model,
                    stream=True,
                    messages=[
                        {
                            "role": prompt[0],
                            "content": prompt[1]
                        }
                        for prompt in prompt_list
                    ]
                )
                response_generator_with_timeout = timeout_generator_wrapper(response_generator, 10)
                total_chars_prompt += sum(len(prompt[1]) for prompt in prompt_list)
                complete_string = ''
                for chunk in response_generator_with_timeout:
                    delta = chunk['choices'][0]['delta']
                    if 'content' in delta:
                        content = delta['content']
                        print_colored('' if complete_string else 'assistent', content, 'green', end='')
                        complete_string += content
                        total_chars_generation += len(content)
                print('\n')
                money_prompt = round(total_chars_prompt / 3.4 * pricing_prompt / 1000, 2)
                money_generation = round(total_chars_generation / 3.4 * pricing_generation / 1000, 2)
                print('money prompt:', f'${money_prompt}')
                print('money generation:', f'${money_generation}')
                print('total money:', f'${money_prompt + money_generation}')
                print('\n')
                return complete_string
            except (RateLimitError, Timeout, ConnectionError, GenerationTimeoutError) as e:
                print(e)
                print('retrying')
                sleep(3)
                continue
        raise Exception('Failed to get response')
