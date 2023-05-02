import os

import pytest

from src.options.generate.generator import Generator


# The cognitive difficulty level is determined by the number of requirements the microservice has.

def test_generation_level_0(tmpdir):
    """
    Requirements:
    coding challenge: ❌
    pip packages: ❌
    environment: ❌
    GPT-3.5-turbo: ❌
    APIs: ❌
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        "The microservice is very simple, it does not take anything as input and only outputs the word 'test'",
        str(tmpdir),
        'gpt-3.5-turbo'
    )
    assert generator.generate() == 0




def test_generation_level_1(tmpdir):
    """
    Requirements:
    coding challenge: ❌
    pip packages: ❌
    environment: ❌
    GPT-3.5-turbo: ✅ (for summarizing the text)
    APIs: ❌
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        '''Input is a tweet that might contain passive aggressive language. The output is the positive version of that tweet.
Example tweet: 
\'When your coworker microwaves fish in the break room... AGAIN. 🐟🤢 
But hey, at least SOMEONE's enjoying their lunch. #officelife\'''',
        str(tmpdir),
        'gpt-3.5-turbo'
    )
    assert generator.generate() == 0


def test_generation_level_2(tmpdir):
    """
    Requirements:
    coding challenge: ❌
    pip packages: ✅ (pdf parser)
    environment: ❌
    GPT-3.5-turbo: ✅ (for summarizing the text)
    APIs: ❌
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        "The input is a PDF like https://www.africau.edu/images/default/sample.pdf and the output the summarized text (50 words).",
        str(tmpdir),
        'gpt-3.5-turbo'
    )
    assert generator.generate() == 0

def test_generation_level_3(tmpdir):
    """
    Requirements:
    coding challenge: ✅ (calculate the average closing price)
    pip packages: ❌
    environment: ❌
    GPT-3.5-turbo: ✅ (for processing the text)
    APIs: ✅ (financial data API)
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        f'''The input is a stock symbol (e.g., AAPL for Apple Inc.). 
1. Fetch stock data (open, high, low, close, volume) for the past 30 days using a financial data API Yahoo Finance.
2. Calculate the average closing price over the 30 days.
3. Generate a brief summary of the company's stock performance over the past 30 days, including the average closing price and the company name.
4. Return the summary as a string.
Example input: 'AAPL'
''',
        str(tmpdir),
        'gpt-3.5-turbo'
    )
    assert generator.generate() == 0

def test_generation_level_4(tmpdir):
    """
    Requirements:
    coding challenge: ❌
    pip packages: ✅ (text to speech)
    environment: ✅ (tts library)
    GPT-3.5-turbo: ✅ (summarizing the text)
    APIs: ✅ (whisper for speech to text)
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        f'''Given an audio file (1min wav) of speech, 
1. convert it to text using the Whisper API.
Here is the documentation on how to use the API:
import requests
url = "https://transcribe.whisperapi.com"
headers = {{
'Authorization': 'Bearer {os.environ['WHISPER_API_KEY']}'
}}
data = {{
  "url": "URL_OF_STORED_AUDIO_FILE"
}}
response = requests.post(url, headers=headers, data=data)
assert response.status_code == 200
print('This is the text from the audio file:', response.json()['text'])
2. Summarize the text (~50 words) while still maintaining the key facts.
3. Create an audio file of the summarized text using a tts library.
4. Return the the audio file as base64 encoded binary.
Example input file: https://www.signalogic.com/melp/EngSamples/Orig/ENG_M.wav
''',
        str(tmpdir),
        'gpt-4'
    )
    assert generator.generate() == 0


def test_generation_level_5(tmpdir):
    """
    Requirements:
    coding challenge: ✅ (putting text on the image)
    pip packages: ✅ (Pillow for image processing)
    environment: ✅ (image library)
    GPT-3.5-turbo: ✅ (for writing the joke)
    APIs: ✅ (scenex for image description)
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(f'''
The input is an image.
Use the following api to get the description of the image:
Request:
curl "https://us-central1-causal-diffusion.cloudfunctions.net/describe" \\
  -H "x-api-key: token {os.environ['SCENEX_API_KEY']}" \\
  -H "content-type: application/json" \\
  --data '{{"data":[
  {{"image": "<image url here>", "features": []}}
  ]}}'
Result format:
{{
    "result": [
    {{
    "text": "<image description>"
    }}
  ]
}}
The description is then used to generate a joke.
The joke is the put on the image.
The output is the image with the joke on it.
Example input image: https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/560px-PNG_transparency_demonstration_1.png
''',
                          str(tmpdir),
                          'gpt-3.5-turbo'
                          )
    assert generator.generate() == 0

@pytest.fixture
def tmpdir():
    return 'microservice'


# further ideas:
# Create a wrapper around google called Joogle. It modifies the page summary preview text of the search results to insert the word Jina as much as possible.
