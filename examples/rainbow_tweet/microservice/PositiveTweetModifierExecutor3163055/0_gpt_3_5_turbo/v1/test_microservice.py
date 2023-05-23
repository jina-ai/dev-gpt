# This test case checks if the output of the microservice is of type 'str' for the positive_tweet property.
# Since the output of the GPT-3.5 Turbo model is not deterministic, we cannot check for the exact output.
# Instead, we will test if the output is a valid JSON string and if the 'positive_tweet' property is a string.

from .microservice import func
import json

def test_positive_tweet_type():
    # Define the input JSON string
    input_json = json.dumps({
        "OPENAI_API_KEY": "",
        "tweet": "I can't believe you did that. It's so typical of you."
    })

    # Call the microservice function with the input JSON string
    output_json = func(input_json)

    # Parse the output JSON string
    output_data = json.loads(output_json)

    # Check if the 'positive_tweet' property is a string
    assert isinstance(output_data["positive_tweet"], str)