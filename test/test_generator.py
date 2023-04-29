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
        str(tmpdir) + 'microservice',
        'gpt-3.5-turbo'
    )
    generator.generate()


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
        '''
Input is a tweet that might contain passive aggressive language like: 
'When your coworker microwaves fish in the break room... AGAIN. 🐟🤢 
But hey, at least SOMEONE's enjoying their lunch. #officelife'
The output is a tweet that is not passive aggressive like:
'Hi coworker, 
I hope you're having an amazing day! 
Just a quick note: sometimes microwaving fish can create an interesting aroma in the break room. 😜
If you're up for trying different lunch options, that could be a fun way to mix things up. 
Enjoy your day! #variety'
''',
        str(tmpdir) + 'microservice',
        'gpt-3.5-turbo'
    )
    generator.generate()


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
        "The input is a PDF like https://www.africau.edu/images/default/sample.pdf and the output the summarized text.",
        str(tmpdir) + 'microservice',
        'gpt-3.5-turbo'
    )
    generator.generate()

@pytest.mark.skip(reason="not possible")
def test_generation_level_3(tmpdir):
    """
    Requirements:
    coding challenge: ❌
    pip packages: ✅ (text to speech)
    environment: ❌
    GPT-3.5-turbo: ✅ (summarizing the text)
    APIs: ✅ (whisper for speech to text)
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        f'''Given an audio file of speech like https://www.signalogic.com/melp/EngSamples/Orig/ENG_M.wav, 
get convert it to text using the following api:
import requests
url = "https://transcribe.whisperapi.com"
headers = {{
'Authorization': 'Bearer {os.environ['WHISPER_API_KEY']}'
}}
data = {{
  "url": "URL_OF_STORED_AUDIO_FILE"
}}
response = requests.post(url, headers=headers, files=file, data=data)
print(response.text)
Summarize the text.
Create an audio file of the summarized text.
''',
        str(tmpdir) + 'microservice',
        'gpt-3.5-turbo'
    )
    generator.generate()

@pytest.mark.skip(reason="not possible")
def test_generation_level_4(tmpdir):
    """
    Requirements:
    coding challenge: ✅ (putting text on the image)
    pip packages: ✅ (Pillow for image processing)
    environment: ❌
    GPT-3.5-turbo: ✅ (for writing the joke)
    APIs: ✅ (scenex for image description)
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(f'''
The input is an image like this: https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/560px-PNG_transparency_demonstration_1.png.
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
The output is the image with the joke on it.''',
                          str(tmpdir) + 'microservice',
                          'gpt-3.5-turbo'
                          )
    generator.generate()
