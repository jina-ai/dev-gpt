import os
import openai


openai.api_key = os.getenv("OPENAI_API_KEY")


class GPT_3_5_Turbo:
    def __init__(self, system: str = ''):
        self.system = system

    def __call__(self, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": 'system',
                "content": self.system
            }, {
                "role": 'user',
                "content": prompt
            }]
        )
        return response.choices[0]['message']['content']



import os
from typing import Optional

import requests


def google_search(search_term, search_type, top_n):
    google_api_key: Optional[str] = os.environ['GOOGLE_API_KEY']
    google_cse_id: Optional[str] = os.environ['GOOGLE_CSE_ID']
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'q': search_term,
        'key': google_api_key,
        'cx': google_cse_id,
        'searchType': search_type,
        'num': top_n
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def search_images(search_term, top_n):
    response = google_search(search_term, search_type="image", top_n=top_n)
    return [item["link"] for item in response["items"]]

def search_web(search_term, top_n):
    response = google_search(search_term, search_type="web", top_n=top_n)
    return [item["snippet"] for item in response["items"]]

