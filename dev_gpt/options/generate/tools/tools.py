import os


def get_available_tools():
    tools = ['gpt-3.5-turbo (for any kind of text processing like summarization, paraphrasing, etc.)']
    if os.environ.get('GOOGLE_API_KEY') and os.environ.get('GOOGLE_CSE_ID'):
        tools.append('Google Custom Search API')
    chars = 'abcdefghijklmnopqrstuvwxyz'
    return '\n'.join([f'{char}) {tool}' for tool, char in zip(tools, chars)])