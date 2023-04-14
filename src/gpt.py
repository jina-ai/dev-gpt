import os
from time import sleep
from typing import List, Tuple

import openai
from openai.error import RateLimitError, Timeout

from src.constants import PRICING_GPT4_PROMPT, PRICING_GPT4_GENERATION, PRICING_GPT3_5_TURBO_PROMPT, \
    PRICING_GPT3_5_TURBO_GENERATION
from src.prompt_system import system_base_definition, executor_example, docarray_example, client_example
from src.utils.io import timeout_generator_wrapper, GenerationTimeoutError
from src.utils.string_tools import print_colored


class GPTSession:
    def __init__(self, model: str = 'gpt-4'):
        self.get_openai_api_key()
        if model == 'gpt-4' and self.is_gpt4_available():
            self.supported_model = 'gpt-4'
            self.pricing_prompt = PRICING_GPT4_PROMPT
            self.pricing_generation = PRICING_GPT4_GENERATION
        else:
            if model == 'gpt-4':
                print_colored('GPT-4 is not available. Using GPT-3.5-turbo instead.', 'yellow')
                model = 'gpt-3.5-turbo'
            self.supported_model = model
            self.pricing_prompt = PRICING_GPT3_5_TURBO_PROMPT
            self.pricing_generation = PRICING_GPT3_5_TURBO_GENERATION
        self.chars_prompt_so_far = 0
        self.chars_generation_so_far = 0

    def get_openai_api_key(self):
        if 'OPENAI_API_KEY' not in os.environ:
            raise Exception('''
You need to set OPENAI_API_KEY in your environment.
If you have updated it already, please restart your terminal.
'''
)
        openai.api_key = os.environ['OPENAI_API_KEY']

    def is_gpt4_available(self):
        try:
            for i in range(5):
                try:
                    openai.ChatCompletion.create(
                        model="gpt-4",
                        messages=[{
                            "role": 'system',
                            "content": 'you respond nothing'
                        }]
                    )
                    break
                except RateLimitError:
                    sleep(1)
                    continue
            return True
        except openai.error.InvalidRequestError:
            return False

    def cost_callback(self, chars_prompt, chars_generation):
        self.chars_prompt_so_far += chars_prompt
        self.chars_generation_so_far += chars_generation
        print('\n')
        money_prompt = round(self.chars_prompt_so_far / 3.4 * self.pricing_prompt / 1000, 3)
        money_generation = round(self.chars_generation_so_far / 3.4 * self.pricing_generation / 1000, 3)
        print('Estimated costs on openai.com:')
        # print('money prompt:', f'${money_prompt}')
        # print('money generation:', f'${money_generation}')
        print('total money spent so far:', f'${money_prompt + money_generation}')
        print('\n')

    def get_conversation(self, system_definition_examples: List[str] = ['executor', 'docarray', 'client']):
        return _GPTConversation(self.supported_model, self.cost_callback, system_definition_examples)


class _GPTConversation:
    def __init__(self, model: str, cost_callback, system_definition_examples: List[str] = ['executor', 'docarray', 'client']):
        self.model = model
        self.cost_callback = cost_callback
        self.prompt_list = [None]
        self.set_system_definition(system_definition_examples)
        print_colored('system', self.prompt_list[0][1], 'magenta')

    def query(self, prompt: str):
        print_colored('user', prompt, 'blue')
        self.prompt_list.append(('user', prompt))
        response = self.get_response(self.prompt_list)
        self.prompt_list.append(('assistant', response))
        return response

    def set_system_definition(self, system_definition_examples: List[str] = []):
        system_message = system_base_definition
        if 'executor' in system_definition_examples:
            system_message += f'\n{executor_example}'
        if 'docarray' in system_definition_examples:
            system_message += f'{docarray_example}'
        if 'client' in system_definition_examples:
            system_message += f'{client_example}'
        self.prompt_list[0] = ('system', system_message)

    def get_response_from_stream(self, response_generator):
        response_generator_with_timeout = timeout_generator_wrapper(response_generator, 10)
        complete_string = ''
        for chunk in response_generator_with_timeout:
            delta = chunk['choices'][0]['delta']
            if 'content' in delta:
                content = delta['content']
                print_colored('' if complete_string else 'assistant', content, 'green', end='')
                complete_string += content
        return complete_string

    def get_response(self, prompt_list: List[Tuple[str, str]]):
        for i in range(10):
            try:
                response_generator = openai.ChatCompletion.create(
                    temperature=0,
                    max_tokens=2_000 if self.model == 'gpt-4' else None,
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

                complete_string = self.get_response_from_stream(response_generator)

            except (RateLimitError, Timeout, ConnectionError, GenerationTimeoutError) as e:
                print(e)
                print('retrying, be aware that this might affect the cost calculation')
                sleep(3)
                continue
            chars_prompt = sum(len(prompt[1]) for prompt in prompt_list)
            chars_generation = len(complete_string)
            self.cost_callback(chars_prompt, chars_generation)
            return complete_string
        raise Exception('Failed to get response')

