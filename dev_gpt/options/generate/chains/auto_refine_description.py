import json

from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.parser import identity_parser
from dev_gpt.options.generate.prompt_factory import context_to_string
from dev_gpt.options.generate.tools.tools import get_available_tools


def auto_refine_description(context):
    context['microservice_description'] = ask_gpt(
        better_description_prompt,
        identity_parser,
        context_string=context_to_string(context)
    )
    context['request_schema'] = ask_gpt(
        generate_request_schema_prompt,
        identity_parser,
        context_string=context_to_string(context)
    )
    context['response_schema'] = ask_gpt(
        generate_output_schema_prompt,
        identity_parser,
        context_string=context_to_string(context)
    )
    context['microservice_description'] = ask_gpt(
        summarize_description_and_schemas_prompt,
        identity_parser,
        context_string=context_to_string(context)
    )
    # details = extract_information(context['microservice_description'], ['database connection details', 'URL', 'secret'])
    # if details:
    #     context['microservice_description'] += '\n\nAdditional information:' + json.dumps(details, indent=4)
    # del context['details']


better_description_prompt = f'''{{context_string}}
Update the description of the Microservice to make it more precise without adding or removing information.
Note: the output must be a list of tasks the Microservice has to perform.
Note: you can uses two tools if necessary:
{get_available_tools()}
Example for the description: "return an image representing the current weather for a given location."
1. get the current weather information from the https://openweathermap.org/ API
2. generate a Google search query to find the image matching the weather information and the location by using gpt-3.5-turbo
3. find the image by using the Google search API
4. return the image as a base64 encoded string'''

generate_request_schema_prompt = '''{context_string}
Generate the lean request json schema of the Microservice.
Note: If you are not sure about the details, then come up with the minimal number of parameters possible.'''

generate_output_schema_prompt = '''{context_string}
Generate the lean response json schema for the Microservice.
Note: If you are not sure about the details, then come up with the minimal number of parameters possible.
Note: If you can decide to return files as URLs or as base64 encoded strings, then choose the base64 encoded strings.'''

summarize_description_and_schemas_prompt = '''{context_string}
Write an updated microservice description by incorporating information about the request and response parameters in a concise way without losing any information.
Note: You must not mention any details about algorithms or the technical implementation.
Note: You must not mention that there is a request and response JSON schema
Note: You must not use any formatting like triple backticks.
Note: If an external API is mentioned in the description, then you must mention the API in the updated description as well.'''
