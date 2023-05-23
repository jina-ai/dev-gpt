# This microservice receives an API key for OpenAI (OPENAI_API_KEY) and a tweet containing potentially passive aggressive language as input.
# It analyzes the input tweet using the OpenAI API to identify passive aggressive language and modifies the language to make it more positive without changing the meaning.
# The microservice then returns the updated, positive version of the tweet as output.

from .apis import GPT_3_5_Turbo
import json


def func(input_json: str) -> str:
    # Parse the input JSON string
    input_data = json.loads(input_json)

    # Extract the OpenAI API key and tweet from the input data
    openai_api_key = input_data["OPENAI_API_KEY"]
    tweet = input_data["tweet"]

    # Initialize the GPT-3.5 Turbo API
    gpt_3_5_turbo = GPT_3_5_Turbo(
        system=f'''
You are an AI language model that can modify tweets to make them more positive without changing their meaning.
When you receive a tweet, you will return a JSON object containing the updated, positive version of the tweet.
Example:
Input tweet: "I can't believe you did that. It's so typical of you."
Output JSON: {{"positive_tweet": "I'm surprised you did that. It's just like you!"}}
''')

    # Generate the prompt for the GPT-3.5 Turbo API
    prompt = f"Input tweet: {tweet}"

    # Call the GPT-3.5 Turbo API with the prompt
    generated_string = gpt_3_5_turbo(prompt)

    # Parse the generated JSON string
    output_data = json.loads(generated_string)

    # Return the output JSON string
    return json.dumps(output_data)