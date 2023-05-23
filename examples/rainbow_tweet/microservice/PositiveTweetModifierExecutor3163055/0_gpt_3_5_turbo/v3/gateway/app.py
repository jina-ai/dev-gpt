import json
import os
import streamlit as st
from jina import Client, Document, DocumentArray

# Set the favicon and title
st.set_page_config(
    page_title="Positive Tweet Modifier",
    page_icon=":smiley:",
    layout="wide",
)

# Define the input dictionary
INPUT_DICTIONARY = {
    "OPENAI_API_KEY": "<your api key>",
    "tweet": "I can't believe you did that. It's so typical of you.",
}

# Define the function to send a request to the microservice
def send_request(input_dict):
    client = Client(host='http://localhost:8080')
    d = Document(text=json.dumps(input_dict))
    response = client.post('/', inputs=DocumentArray([d]))
    return response[0].text

# Create the UI
st.title("Positive Tweet Modifier :speech_balloon:")
st.write("Transform negative tweets into positive ones using GPT-3.5 Turbo! :sunglasses:")

# Input form
st.subheader("Input")
tweet = st.text_area("Enter a negative tweet:", value=INPUT_DICTIONARY["tweet"], height=100)
api_key = st.text_input("Enter your OPENAI_API_KEY:", value=INPUT_DICTIONARY["OPENAI_API_KEY"])

# Send request button
if st.button("Transform Tweet"):
    INPUT_DICTIONARY["tweet"] = tweet
    INPUT_DICTIONARY["OPENAI_API_KEY"] = api_key
    response_text = send_request(INPUT_DICTIONARY)
    response_data = json.loads(response_text)

    # Display the result
    st.subheader("Result")
    st.write(f"Positive Tweet: {response_data['positive_tweet']} :thumbsup:")

# Deploy your own microservice
st.markdown(
    "Want to deploy your own microservice? [Click here!](https://github.com/jina-ai/dev-gpt)"
)

# Display the curl command
deployment_id = os.environ.get("K8S_NAMESPACE_NAME", "")
host = f'https://dev-gpt-{deployment_id.split("-")[1]}.wolf.jina.ai/post' if deployment_id else "http://localhost:8080/post"
with st.expander("See curl command"):
    st.code(
        f'curl -X \'POST\' \'{host}\' -H \'accept: application/json\' -H \'Content-Type: application/json\' -d \'{{"data": [{{"text": "hello, world!"}}]}}\'',
        language='bash'
    )