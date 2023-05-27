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
        **({'searchType': search_type} if search_type == 'image' else {}),
        'num': top_n
    }
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()

def search_images(search_term, top_n):
    """
    Returns only images that have a 200 response code.
    """
    response = google_search(search_term, search_type="image", top_n=10)
    image_urls = []
    for item in response["items"]:
        if len(image_urls) >= top_n:
            break
        try:
            response = requests.head(item["link"], timeout=2)
            if response.status_code == 200:
                image_urls.append(
                    item["link"]
                )
        except requests.exceptions.RequestException:
            pass
    return image_urls

def search_web(search_term, top_n):
    response = google_search(search_term, search_type="web", top_n=top_n)
    return [item["snippet"] for item in response["items"]]
