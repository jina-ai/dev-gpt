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



