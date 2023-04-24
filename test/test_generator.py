import unittest.mock as mock
from src.options.generate.generator import Generator
from src.apis.gpt import GPTSession

def test_generator(tmpdir):
    # Define a mock response
    mock_response = {
        "choices": [
            {
                "delta": {
                    "content": "This is a mock response."
                }
            }
        ]
    }

    # Define a function to replace openai.ChatCompletion.create
    def mock_create(*args, **kwargs):
        return [mock_response] * kwargs.get("stream", 1)

    # Define a function to replace get_openai_api_key
    def mock_get_openai_api_key(*args, **kwargs):
        pass

    # Use mock.patch as a context manager to replace the original methods with the mocks
    with mock.patch("openai.ChatCompletion.create", side_effect=mock_create), \
            mock.patch.object(GPTSession, "configure_openai_api_key", side_effect=mock_get_openai_api_key):
        generator = Generator("my description", "my test")
        generator.generate(str(tmpdir))
