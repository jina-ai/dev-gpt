import json
from typing import List

from langchain.schema import BaseMessage


class ConversationLogger:
    def __init__(self, log_file_path):
        self.log_file_path = log_file_path
        self.log_file = []

    def log(self, prompt_message_list: List[BaseMessage], response: str):
        prompt_list_json = [
            {
                'role': f'{message.type}',
                'content': f'{message.content}'
            }
            for message in prompt_message_list
        ]
        self.log_file.append({
            'prompt': prompt_list_json,
            'response': f'{response}'
        })
        with open(self.log_file_path, 'w') as f:
            f.write(json.dumps(self.log_file, indent=2))


import datetime

class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Timer(metaclass=Singleton):
    def __init__(self):
        if not hasattr(self, "start_time"):
            self.start_time = datetime.datetime.now()

    def get_time_since_start(self):
        now = datetime.datetime.now()
        time_diff = now - self.start_time
        minutes, seconds = divmod(time_diff.seconds, 60)

        if minutes > 0:
            return f"{minutes}m, {seconds}s"
        else:
            return f"{seconds}s"
