import json
import os

import streamlit as st
from jina import Client, Document, DocumentArray
# <additional imports here>

def main():
    set_page_config()
    st.title("<thematic emoji here> <header title here>")
    st.markdown(
        "<10 word description here>"
        "To generate and deploy your own microservice, click [here](https://github.com/jina-ai/dev-gpt)."
    )
    st.subheader("<a unique thematic emoji here> <sub header title here>")  # only if input parameters are needed
    is_submitted, input_json_dict = get_input_parameters()

    input_json_dict_string = json.dumps(input_json_dict)
    # call microservice
    if is_submitted:
        output_data = make_api_call(input_json_dict_string)
        # <visualization of results here>

    display_curl_command(input_json_dict_string)

def make_api_call(input_json_dict_string):
    with st.spinner("<spinner text here>..."):
        client = Client(host="http://localhost:8080")
        d = Document(text=input_json_dict_string)
        response = client.post("/", inputs=DocumentArray([d]))

        output_data = json.loads(response[0].text)
    return output_data

def display_curl_command(input_json_dict_string):
    # Display curl command
    deployment_id = os.environ.get("K8S_NAMESPACE_NAME", "")
    api_endpoint = (
        f"https://dev-gpt-{deployment_id.split('-')[1]}.wolf.jina.ai/post"
        if deployment_id
        else "http://localhost:8080/post"
    )

    with st.expander("See curl command"):
        st.markdown(
            "You can use the following curl command to send a request to the microservice from the command line:")
        escaped_input_json_dict_string = input_json_dict_string.replace('"', '\\"')

        st.code(
            f'curl -X "POST" "{api_endpoint}" -H "accept: application/json" -H "Content-Type: application/json" -d \'{{"data": [{{"text": "{escaped_input_json_dict_string}"}}]}}\'',
            language="bash",
        )

def get_input_parameters():
    with st.form(key="input_form"):
        # <input parameter definition here>
        input_json_dict = {}  # <input parameter dictionary here>
        is_submitted = st.form_submit_button("<submit button text>")
    return is_submitted, input_json_dict


def set_page_config():
    st.set_page_config(
        page_title="<page title here>",
        page_icon="<page icon here>",
        layout="centered",
        initial_sidebar_state="auto",
    )

if __name__ == "__main__":
    main()