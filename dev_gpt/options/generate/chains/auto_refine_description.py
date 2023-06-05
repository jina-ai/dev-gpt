import json

from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.constants import TOOL_TO_ALIASES
from dev_gpt.options.generate.parser import identity_parser, optional_tripple_back_tick_parser
from dev_gpt.options.generate.prompt_factory import context_to_string
from dev_gpt.options.generate.tools.tools import get_available_tools


def enhance_description(context):
    enhanced_description = ask_gpt(
        better_description_prompt,
        identity_parser,
        context_string=context_to_string(context)
    )
    for tool_name, aliases in TOOL_TO_ALIASES.items():
        for alias in aliases:
            enhanced_description = enhanced_description.replace(alias, tool_name)
    return enhanced_description


def auto_refine_description(context):
    context['microservice_description'] = enhance_description(context)
    context['request_schema'] = ask_gpt(
        generate_request_schema_prompt,
        optional_tripple_back_tick_parser,
        context_string=context_to_string(context)
    )
    context['response_schema'] = ask_gpt(
        generate_output_schema_prompt,
        optional_tripple_back_tick_parser,
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
Based on this description, update the tasks for the Microservice to be more precise. This update should neither add nor remove information.

Constraints:

- The output must be a list of tasks that the Microservice has to perform.
- The updated description must be unambiguous, using precise language and direct instructions.
- Use of non-specific formulations, such as 'like', 'such as', is strictly not allowed.
- The tools that can be used in the updated description:
{get_available_tools()}
- Note: You are not required to use all tools for every task. Use them only when necessary.
Example for the description: "return an image representing the current weather for a given location." \
when the tools gpt_3_5_turbo and google_custom_search are available:
1. get the current weather information from the https://openweathermap.org/ API
2. generate a Google search query to find the image matching the weather information and the location by using gpt_3_5_turbo (a)
3. find the image by using the google_custom_search (b)
4. return the image as a base64 encoded string'''

generate_request_schema_prompt = '''{context_string}
Generate the lean request json schema of the Microservice.
Note: If you are not sure about the details, then come up with the minimal number of parameters possible (could be even no parameters).
Note: If you can decide to receive files as URLs or as base64 encoded strings, then choose the base64 encoded strings.'''

generate_output_schema_prompt = '''{context_string}
Generate the lean response json schema for the Microservice.
Note: If you are not sure about the details, then come up with the minimal number of parameters possible.
Note: If you can decide to return files as URLs or as base64 encoded strings, then choose the base64 encoded strings.'''

summarize_description_and_schemas_prompt = '''{context_string}
Please write an updated microservice description by incorporating information about the request and response parameters in a concise manner, ensuring all information from the existing description is maintained.

Constraints:

- Do not mention any details about algorithms or the technical implementation.
- Refrain from indicating there is a request and response JSON schema.
- Avoid using any special formatting such as triple backticks.
- If a specific tool or API (e.g. google_custom_search, gpt_3_5_turbo) is referred to in the original description, \
include it in the updated description using the exact name given. \
For instance, if the original description mentions 'gpt_3_5_turbo', \
the updated description should also specify 'gpt_3_5_turbo'.'''