import json
import os

import streamlit as st
from jina import Client, Document, DocumentArray
import io

st.set_page_config(
    page_title="<page title here>",
    page_icon="<page icon here>",
    layout="centered",
    initial_sidebar_state="auto",
)

st.title("<thematic emoji here> <header title here>")
st.markdown(
    "<10 word description here>"
    "To generate and deploy your own microservice, click [here](https://github.com/jina-ai/dev-gpt)."
)
st.subheader("<a unique thematic emoji here> <sub header title here>")  # only if input parameters are needed
with st.form(key="input_form"):
    # <input parameter definition here>
    input_json_dict = {} #

    input_json_dict_string = json.dumps(input_json_dict)
    submitted = st.form_submit_button("<submit button text>")

# Process input and call microservice
if submitted:
    with st.spinner("<spinner text here>..."):
        client = Client(host="http://localhost:8080")
        d = Document(text=input_json_dict_string)
        response = client.post("/", inputs=DocumentArray([d]))

        output_data = json.loads(response[0].text)
        # <visualization of results here>

# Display curl command
deployment_id = os.environ.get("K8S_NAMESPACE_NAME", "")
api_endpoint = (
    f"https://dev-gpt-{deployment_id.split('-')[1]}.wolf.jina.ai/post"
    if deployment_id
    else "http://localhost:8080/post"
)

with st.expander("See curl command"):
    st.markdown("You can use the following curl command to send a request to the microservice from the command line:")
    escaped_input_json_dict_string = input_json_dict_string.replace('"', '\\"')

    st.code(
        f'curl -X "POST" "{api_endpoint}" -H "accept: application/json" -H "Content-Type: application/json" -d \'{{"data": [{{"text": "{escaped_input_json_dict_string}"}}]}}\'',
        language="bash",
    )
