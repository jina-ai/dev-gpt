import os
from copy import deepcopy
from time import sleep

from typing import List, Any

import openai
from langchain import PromptTemplate
from langchain.callbacks import CallbackManager
from langchain.chat_models import ChatOpenAI
from openai.error import RateLimitError
from langchain.schema import HumanMessage, SystemMessage, BaseMessage, AIMessage
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from requests.exceptions import ConnectionError, ChunkedEncodingError
from urllib3.exceptions import InvalidChunkLength

from src.constants import PRICING_GPT4_PROMPT, PRICING_GPT4_GENERATION, PRICING_GPT3_5_TURBO_PROMPT, \
    PRICING_GPT3_5_TURBO_GENERATION, CHARS_PER_TOKEN
from src.options.generate.templates_system import template_system_message_base
from src.utils.string_tools import print_colored


def configure_openai_api_key():
    if 'OPENAI_API_KEY' not in os.environ:
        print_colored('You need to set OPENAI_API_KEY in your environment.', '''
Run:
gptdeploy configure --key <your_openai_api_key>

If you have updated it already, please restart your terminal.
''', 'red')
        exit(1)
    openai.api_key = os.environ['OPENAI_API_KEY']

class GPTSession:
    def __init__(self, task_description, model: str = 'gpt-4', ):
        self.task_description = task_description
        if model == 'gpt-4' and self.is_gpt4_available():
            self.pricing_prompt = PRICING_GPT4_PROMPT
            self.pricing_generation = PRICING_GPT4_GENERATION
        else:
            if model == 'gpt-4':
                print_colored('GPT version info', 'GPT-4 is not available. Using GPT-3.5-turbo instead.', 'yellow')
            model = 'gpt-3.5-turbo'
            self.pricing_prompt = PRICING_GPT3_5_TURBO_PROMPT
            self.pricing_generation = PRICING_GPT3_5_TURBO_GENERATION
        self.model_name = model
        self.chars_prompt_so_far = 0
        self.chars_generation_so_far = 0

    def get_conversation(self, messages: List[BaseMessage] = [], print_stream: bool = True, print_costs: bool = True):
        messages = deepcopy(messages)
        return _GPTConversation(
            self.model_name, self.cost_callback, messages, print_stream, print_costs
        )


    @staticmethod
    def is_gpt4_available():
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

    def cost_callback(self, chars_prompt, chars_generation, print_costs: bool = True):
        self.chars_prompt_so_far += chars_prompt
        self.chars_generation_so_far += chars_generation
        if print_costs:
            print('\n')
            money_prompt = self._calculate_money_spent(self.chars_prompt_so_far, self.pricing_prompt)
            money_generation = self._calculate_money_spent(self.chars_generation_so_far, self.pricing_generation)
            print('Total money spent so far on openai.com:', f'${money_prompt + money_generation:.3f}')
            print('\n')

    @staticmethod
    def _calculate_money_spent(num_chars, price):
        return round(num_chars / CHARS_PER_TOKEN * price / 1000, 3)


class AssistantStreamingStdOutCallbackHandler(StreamingStdOutCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs: Any) -> None:
        """Run on new LLM token. Only available when streaming is enabled."""
        print_colored('', token, 'green', end='')


class _GPTConversation:
    def __init__(self, model: str, cost_callback, messages: List[BaseMessage], print_stream, print_costs):
        self._chat = ChatOpenAI(
            model_name=model,
            streaming=True,
            callback_manager=CallbackManager([AssistantStreamingStdOutCallbackHandler()] if print_stream else []),
            verbose=True,
            temperature=0,
        )
        self.cost_callback = cost_callback
        self.messages = messages
        self.print_stream = print_stream
        self.print_costs = print_costs


    def print_messages(self, messages):
        for i, message in enumerate(messages):
            if os.environ['VERBOSE'].lower() == 'true':
                if isinstance(message, SystemMessage):
                    print_colored(f'({i}) system - prompt', message.content, 'magenta')
                elif isinstance(message, HumanMessage):
                    print_colored(f'({i}) user - prompt', message.content, 'blue')
                elif isinstance(message, AIMessage):
                    print_colored(f'({i}) assistant - prompt', message.content, 'green')

    def chat(self, prompt: str, role: str = 'user'):
        MassageClass = HumanMessage if role == 'user' else SystemMessage
        chat_message = MassageClass(content=prompt)
        self.messages.append(chat_message)
        self.print_messages(self.messages)
        if self.print_stream:
            print_colored('assistant', '', 'green', end='')
        print('thinking...')
        for i in range(10):
            try:
                response = self._chat(self.messages)
                break
            except (ConnectionError, InvalidChunkLength, ChunkedEncodingError) as e:
                print('There was a connection error. Retrying...')
                if i == 9:
                    raise e
                sleep(10)

        if os.environ['VERBOSE'].lower() == 'true':
            print()
        self.cost_callback(sum([len(m.content) for m in self.messages]), len(response.content), self.print_costs)
        self.messages.append(response)
        return response.content

    @staticmethod
    def _create_system_message(task_description, test_description, system_definition_examples: List[str] = []) -> SystemMessage:
        if system_definition_examples is None:
            return None

        system_message = PromptTemplate.from_template(template_system_message_base).format(
            task_description=task_description,
            test_description=test_description,
        )
        return SystemMessage(content=system_message)
