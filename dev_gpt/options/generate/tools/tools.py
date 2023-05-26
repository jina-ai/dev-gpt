import os


def get_available_tools():
    tools = ['gpt_3_5_turbo (for any kind of text processing like summarization, paraphrasing, etc.)']
    if os.environ.get('GOOGLE_API_KEY') and os.environ.get('GOOGLE_CSE_ID'):
        tools.append('google_custom_search (for retrieving images or textual information from google')
    chars = 'abcdefghijklmnopqrstuvwxyz'
    return '\n'.join([f'{char}) {tool}' for tool, char in zip(tools, chars)])