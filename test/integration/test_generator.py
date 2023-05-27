import os

import pytest

from dev_gpt.options.generate.generator import Generator


# The cognitive difficulty level is determined by the number of requirements the microservice has.

@pytest.mark.parametrize('mock_input_sequence', [['y']], indirect=True)
def test_generation_level_0(microservice_dir, mock_input_sequence):
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
        microservice_dir,
        'gpt-3.5-turbo',
        self_healing=False,
    )
    assert generator.generate() == 0


@pytest.mark.parametrize('mock_input_sequence', [['y']], indirect=True)
def test_generation_level_1(microservice_dir, mock_input_sequence):
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
        '''Input is a tweet that contains passive aggressive language. The output is the positive version of that tweet.''',
        str(microservice_dir),
        'gpt-3.5-turbo',
        # self_healing=False,
    )
    assert generator.generate() == 0


@pytest.mark.parametrize('mock_input_sequence', [['y', 'https://www.africau.edu/images/default/sample.pdf']],
                         indirect=True)
def test_generation_level_2(microservice_dir, mock_input_sequence):
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
        "The input is a PDF and the output the summarized text.",
        str(microservice_dir),
        'gpt-3.5-turbo',
        # self_healing=False,
    )
    assert generator.generate() == 0


@pytest.mark.parametrize('mock_input_sequence', [
    ['y', 'https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png']], indirect=True)
def test_generation_level_2_svg(microservice_dir, mock_input_sequence):
    """
    Requirements:
    coding challenge: ✅
    pip packages: ✅
    environment: ❌
    GPT-3.5-turbo: ❌
    APIs: ❌
    Databases: ❌
    """
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        "Get a png as input and return a vectorized version as svg.",
        str(microservice_dir),
        'gpt-3.5-turbo',
        # self_healing=False,
    )
    assert generator.generate() == 0


@pytest.mark.parametrize('mock_input_sequence', [['y', 'yfinance.Ticker("MSFT").info']], indirect=True)
def test_generation_level_3(microservice_dir, mock_input_sequence):
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
        str(microservice_dir),
        'gpt-3.5-turbo',
        # self_healing=False,
    )
    assert generator.generate() == 0


@pytest.mark.parametrize(
    'mock_input_sequence', [
        [
            'y',
            'https://www2.cs.uic.edu/~i101/SoundFiles/taunt.wav',
            f'''\
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
print('This is the text from the audio file:', response.text)'''
            #             f'''\
            # import openai
            # audio_file= open("/path/to/file/audio.mp3", "rb")
            # transcript = openai.Audio.transcribe("whisper-1", audio_file)'''
        ]
    ],
    indirect=True
)
def test_generation_level_4(microservice_dir, mock_input_sequence):
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
2. Summarize the text while still maintaining the key facts.
3. Create an audio file of the summarized text using a tts library.
4. Return the the audio file as base64 encoded binary.
''',
        str(microservice_dir),
        # 'gpt-3.5-turbo',
        'gpt-4',
        # self_healing=False,
    )
    assert generator.generate() == 0


@pytest.mark.parametrize('mock_input_sequence', [['y']], indirect=True)
def test_generation_level_5_company_logos(microservice_dir, mock_input_sequence):
    os.environ['VERBOSE'] = 'true'
    generator = Generator(
        f'''\
Given a list of email addresses, get all unique company names from them.
For all companies, get the company logo.
All logos need to be arranged on a square.
The square is returned as png.''',
        str(microservice_dir),
        'gpt-3.5-turbo',
        # self_healing=False,
    )
    assert generator.generate() == 0


@pytest.mark.parametrize('mock_input_sequence', [['y',
                                                  'https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/PNG_transparency_demonstration_1.png/560px-PNG_transparency_demonstration_1.png']],
                         indirect=True)
def test_generation_level_5(microservice_dir, mock_input_sequence):
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
    generator = Generator(
        f'''
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
''',
        str(microservice_dir),
        'gpt-3.5-turbo',
        # self_healing=False,
    )
    assert generator.generate() == 0

# @pytest.fixture
# def microservice_dir():
#     return 'microservice'


# # further ideas:
# # Create a wrapper around google called Joogle. It modifies the page summary preview text of the search results to insert the word Jina as much as possible.
#
# import pytest
#
# # This is your fixture which can accept parameters
# @pytest.fixture
# def my_fixture(microservice_dir, request,):
#     return request.param  # request.param will contain the parameter value
#
# # Here you parameterize the fixture for the test
# @pytest.mark.parametrize('my_fixture', ['param1', 'param2', 'param3'], indirect=True)
# def test_my_function(my_fixture, microservice_dir):
#     # 'my_fixture' now contains the value 'param1', 'param2', or 'param3'
#     # depending on the iteration
#     # Here you can write your test
#     ...
