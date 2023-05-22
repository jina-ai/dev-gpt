from langchain import PromptTemplate

from dev_gpt.constants import IMPLEMENTATION_FILE_NAME

general_guidelines_string = '''The code you write is production ready. Every file starts with comments describing what the code is doing before the first import. Comments can only be written within code blocks.
Then all imports are listed.

Start from top-level and then fully implement all methods.'''


not_allowed_docker_string = '''Note that the Dockerfile only has access to the files: microservice.py, requirements.txt, config.yml, test_microservice.py.
Note that the Dockerfile runs the test_microservice.py during the build process.
The Dockerfile must not attach a virtual display when running test_microservice.py.'''


not_allowed_function_string = '''The implemented function and the test must not use the GPU.
The implemented function and the test must not access a database.
The implemented function and the test must not access a display.
The implemented function and the test must not access external apis unless it is explicitly mentioned.
The implemented function and the test must not be based on a large collection of hard-coded strings.
The implemented function and the test must not open files from the local file system unless it was created by the implemented function itself.
The implemented function and the test must not use a pre-trained model unless it is explicitly mentioned in the description.
The implemented function and the test must not train a model.
The implemented function and the test must not contain prototype or placeholder implementations.
The implemented function and the test must run in a docker container based on debian.
The implemented function and the test must not use libraries like Flask.
The implemented function and the test must not have a __main__ function.
The implemented function and the test must use gpt_3_5_turbo if the task requires the processing of language (e.g., understanding, generation, summarization, transformation, translation, modification or classification). Other language models are not allowed.
The implemented function must follow a clean and elegant coding style.'''


template_generate_microservice_name = PromptTemplate.from_template(
    '''Generate a name for the executor matching the description:
"{description}"
The executor name must fulfill the following criteria:
- camel case
- start with a capital letter
- only consists of lower and upper case characters
- end with Executor.

Your response must exactly match the following block code format (double asterisks for the file name and triple backticks for the file block):
**name.txt**
```
<name here>
```
Example for: "Get a png as input and return a vectorized version as svg.":
**name.txt**
```
PngToSvgExecutor
```'''
)

# todo split into multiple calls. One for brainstorming - one for the final answer
template_generate_possible_packages = PromptTemplate.from_template(
    '''Here is the task description of the problem you need to solve:
"{description}"
1. Write down up to 3 different strategies to solve the task. For each strategy write down how it solves the core problems.
Note that packages are preferred over external apis except if it is mentioned in the description.
2. For each strategy list up to 3 Python packages that are specifically designed or have functionalities to solve the complete core problems.
3. For each package think if it fulfills the following requirements:
a) specifically designed or have functionalities to solve the complete core problem.
b) has a stable api among different versions
c) does not have system requirements
d) can solve the task when running in a docker container
e) the implementation of the core problem using the package would obey the following rules:
''' + not_allowed_function_string + '''

When answering, just write "yes" or "no".

4. For each approach, list the required python package combinations as discibed in the following.
You must output the package combinations as json wrapped into triple backticks ``` and name it **strategies.json**. \
Note that you can also leave a list empty to indicate that one of the strategies does not require any package and can be done in plain python.
Write the output using double asterisks and triple backticks like this:
**strategies.json**
```
[
  ["package1", "package2", "package3"],
  ["package4", "package5"],
  ["package6", "package7", "package8", "package9"],
  [],
  ["package10"]
]
```''')


template_code_wrapping_string = '''The code will go into {file_name_purpose}.
Note that you must obey the double asterisk and triple backtick syntax from like this:
**{file_name}**
```{tag_name}
...code...
```
You must provide the complete {file_name} wrapped with the exact syntax shown above.'''


gpt_35_turbo_usage_string = """If you need to use gpt_3_5_turbo, then use it like shown in the following example:
```
from .gpt_3_5_turbo import GPT_3_5_Turbo

gpt_3_5_turbo = GPT_3_5_Turbo(
    system_string=\'\'\'
You are a tv-reporter who is specialized in C-list celebrities.
When you get asked something like 'Who was having a date with <X>?', then you answer with a string like "<y>, <z> were having a date with <x>"'. 
You must not answer something else - only the json.
\'\'\')

generated_string = gpt_3_5_turbo(prompt_string="example user prompt") # prompt_string is the only parameter
```
"""

google_custom_search_usage_string = """If you need to use google_custom_search, then use it like shown in the following example:
a) when searching for text:
```
from .google_custom_search import search_web

# input: search term (str), top_n (int)
# output: list of strings
string_list = search_web('<search term>', top_n=10)
```
b) when searching for images:
```
from .google_custom_search import search_images

# input: search term (str), top_n (int)
# output: list of image urls
image_url_list = search_images('<search term>', top_n=10)
```
"""

linebreak = '\n'
def template_generate_function_constructor(is_using_gpt_3_5_turbo, is_using_google_custom_search):
    return PromptTemplate.from_template(
    general_guidelines_string + f'''

Write a python function which receives as \
input json dictionary string (that can be parsed with the python function json.loads) and \
outputs a json dictionary string (that can be parsed with the python function json.loads). \
The function is called 'func' and has the following signature:
def func(input_json_dict_string: str) -> str:
The function must fulfill the following description: '{{microservice_description}}'.
It will be tested with the following scenario: '{{test_description}}'.
For the implementation use the following package(s): '{{packages}}'.

The code must start with the following imports:
```{linebreak +'from .gpt_3_5_turbo import GPT_3_5_Turbo' if is_using_gpt_3_5_turbo else ""}{linebreak + 'from .google_custom_search import search_web, search_images' if is_using_google_custom_search else ""}
import json
import requests
```
Obey the following rules:
{not_allowed_function_string}

Your approach:
1. Identify the core challenge when implementing the function.
2. Think about solutions for these challenges.
3. Decide for one of the solutions.
4. Write the code for the function. Don't write code for the test.
{gpt_35_turbo_usage_string if is_using_gpt_3_5_turbo else ''}
{google_custom_search_usage_string if is_using_google_custom_search else ''}
{template_code_wrapping_string}'''
    )


template_generate_test = PromptTemplate.from_template(
    general_guidelines_string + '''

{code_files_wrapped}

Write a single pytest case that tests the following scenario: '{test_description}'. In case the test scenario is not precise enough, test a general case without any assumptions.
Start the test with an extensive comment about the test case. If gpt_3_5_turbo is used in the executor, then the test must not check the exact output of the executor as it is not deterministic. 

The test must start with the following imports:
```
from .microservice import func
import json
import requests
```
''' + not_allowed_function_string + '''
The test must not open local files.
The test must not mock a function of the executor.
The test must not use other data than the one provided in the test scenario.
The test must not set any environment variables which require a key.
''' + '\n' + template_code_wrapping_string
)


template_generate_requirements = PromptTemplate.from_template(
    general_guidelines_string + f'''

{{code_files_wrapped}}
    
Write the content of the requirements.txt file like this:
**requirements.txt**
```
...
```
Add any more packages that are needed to run the code.
You must not add gpt_3_5_turbo to the requirements.txt file. 

All versions are fixed using ~=, ==, <, >, <=, >=. The package versions must not have conflicts.

{template_code_wrapping_string} 
Note: you must only output the requirements.txt file - no other file.
''')


template_generate_apt_get_install = PromptTemplate.from_template(
    '''Given the following Dockerfile:

{docker_file_wrapped}

Name all packages which need to be installed via `apt-get install` in above Dockerfile (`{{APT_GET_PACKAGES}}`) for the following requirements.txt file:

{requirements_file_wrapped}

Note that you must not list apt-get packages that are already installed in the Dockerfile.
Note that openai does not require any apt-get packages.
Note that you are only allowed to list packages where you are highly confident that they are really needed.
Note that you can assume that the standard python packages are already installed.
Output the packages that need to me placed at {{APT_GET_PACKAGES}} as json in the following format:
**apt-get-packages.json**
```json
{{"packages": ["<package1>", "<package2>"]}}
```
Example for the following requirements.txt file:
**requirements.txt**
```
numpy==1.19.5
fitz
```
The output would be:
**apt-get-packages.json**
```json
{{"packages": []}}
```
'''
)


template_summarize_error = PromptTemplate.from_template(
    '''Your task is to condense an error encountered during the docker build process. The error message is as follows:
"{error}"
Your task is to summarize the error message as compact and informative as possible \
while maintaining all information necessary to debug the core issue (100 words).
It should also provide some additional context regarding the specific file and line number where the error occurred. \
Note that you must not suggest a solution to the error.
Warnings are not worth mentioning.'''
)


template_is_dependency_issue = PromptTemplate.from_template(
    '''Your task is to assist in identifying the root cause of a Docker build error for a python application.
The error message is as follows:

{summarized_error}

You are given the following files:

{all_files_string}

Is this error happening because a PACKAGE_MANAGER package is missing or failed to install? 
1. Write down one bullet point on why the error might happen because a PACKAGE_MANAGER package is missing or failed to install.
2. Write down one bullet point on why it is unlikely that the error happens because a PACKAGE_MANAGER package is missing or failed to install.
3. Write down your final answer.
4. Write down your final answer as json in the following format:
**response.json**
```json
{{"dependency_installation_failure": "<yes/no>"}}
```
Note that you must obey the double asterisk and triple backtick syntax from above.
'''
)


template_solve_pip_dependency_issue = PromptTemplate.from_template(
    '''Your task is to provide guidance on how to solve an error that occurred during the Docker build process. 
Here is the summary of the error that occurred:
{summarized_error}

To solve this error, you should:
1. Suggest 3 to 5 possible solutions on how to solve it. You have no access to the documentation of the package.
2. Decide for the best solution and explain it in detail.
3. Write down how requirements.txt should look like to solve the error. 
For files that need to be changed, you must provide the complete file with the exact same syntax to wrap the code.

You are given the following files:

{all_files_string}

Output how the requirements.txt file should look like to solve the error.
If you output a file, then write the complete file. Use the exact following syntax to wrap the code:

**requirements.txt**
```
...packages...
```

Example:

**requirements.txt**
```
jina==2.0.0
```
'''
)


template_solve_apt_get_dependency_issue = PromptTemplate.from_template(
    '''Your task is to provide guidance on how to solve an error that occurred during the Docker build process.
You are given the following files:

{all_files_string}

Here is the summary of the error that occurred:
{summarized_error}

To solve this error, you should determine the list of packages that need to be installed via `apt-get install` in the Dockerfile.
Output the apt-get packages that need to be placed at {{APT_GET_PACKAGES}} as json in the following format:
**apt-get-packages.json**
```json
{{"packages": ["<package1>", "<package2>"]}}
```
Example:
Error is about missing package `libgl1-mesa-glx`.
The output is:
**apt-get-packages.json**
```json
{{"packages": [libgl1-mesa-glx]}}
```
Only output content of the apt-get-packages.json file. Ensure the response can be parsed by Python json.loads
Note: you must not output the content of any other. Especially don't output the Dockerfile or requirements.txt. 
Note: the first line you output must be: **apt-get-packages.json**
'''
)


response_format_suggest_solutions = '''**solutions.json**
```json
{{
    "1": "<best solution>",
    "2": "<2nd best solution>"
}}
```'''


template_suggest_solutions_code_issue = PromptTemplate.from_template(
    '''General rules:
''' + not_allowed_function_string + '''

Here is the description of the task the function must solve:
{task_description}

Here is the test scenario the function must pass:
{test_description}
Here are all the files I use:
{all_files_string}


Here is the summary of the error that occurred:
{summarized_error}

You should suggest 3 to 5 possible solution approaches on how to solve it.
Obey the following rules:
Do not implement the solution.
You have no access to the documentation of the package.
You must not change the Dockerfile.
Note that any changes needed to make the test pass must be written under the constraint that ''' + IMPLEMENTATION_FILE_NAME +  ''' will be used in a different file as well.
''' + f'{not_allowed_function_string}\n{not_allowed_docker_string}\n{gpt_35_turbo_usage_string}' + '''


After thinking about the possible solutions, output them as JSON ranked from best to worst.
You must use the following format:
''' + response_format_suggest_solutions + '''
Ensure the response starts with **solutions.json** and can be parsed by Python json.loads'''
)


response_format_was_error_seen_before = '''**was_error_seen_before.json**
```json
{{"was_error_seen_before": "<yes/no>"}}
```'''


template_was_error_seen_before = PromptTemplate.from_template(
    '''Previously encountered error messages:
{previous_errors}

Now encountered error message: "{summarized_error}"
Was this error message encountered before?

Write down your final answer as json in the following format:
''' + response_format_was_error_seen_before + '''
Note that you must obey the double asterisk and triple backtick syntax from above. Ensure the response can be parsed by Python json.loads
'''
)


response_format_was_solution_tried_before = '''**will_lead_to_different_actions.json**
```json
{{"will_lead_to_different_actions": "<yes/no>"}}
```'''


template_was_solution_tried_before = PromptTemplate.from_template(
    '''Previously tried solutions:
{tried_solutions}

Suggested solution: "{suggested_solution}"

Will the suggested solution lead to different actions than the previously tried solutions?

Write down your final answer as json in the following format:
''' + response_format_was_solution_tried_before + '''
Note that you must obey the double asterisk and triple backtick syntax from above. Ensure the response can be parsed by Python json.loads'''
)


template_implement_solution_code_issue = PromptTemplate.from_template(
    '''Here is the description of the task the function must solve:
{task_description}

Here is the test scenario the function must pass:
{test_description}
Here are all the files I use:
{all_files_string}

Implemented the suggested solution: {suggested_solution}

Output all the files that need change. You must not change the Dockerfile. 
Don't output files that don't need change. If you output a file, then write the complete file.
Use the exact following syntax to wrap the code:

**...**
```...
...code...
```

Example:
**implementation.py**
```python
import json

def func(input_json_dict_string: str) -> str:
    return json.dumps('output_param1': input_json_dict_string['img_base64'])
```'''
)


template_generate_playground = PromptTemplate.from_template(
    general_guidelines_string + '''👨‍💻

{code_files_wrapped}

1. Write down the json request model required by microservice.py.
2. Generate a playground for the microservice {microservice_name} using the following streamlit template by replacing all the placeholders (<...>) with the correct values:
**app_template.py**
```python
{playground_template}
```
Note: Don't mention the word Playground in the title.
Most importantly: You must generate the complete app.py file using the following syntax to wrap the code:
**app.py**
```python
...
```'''
)


template_chain_of_thought = PromptTemplate.from_template(
    '''\
1. write down an extensive list (5 words per item) of obvious and non-obvious observations about {file_name_purpose} that could need an adjustment. 
2. Explain why. (5 words per item)
3. Think if all the changes are required
4. decide for the changes you want to make, but you are not allowed disregard the instructions in the previous message.
5. Write the whole content of {file_name_purpose} - even if you decided to change only a small thing or even nothing.
Note: Be very hesitant to change the code. Only make a change if you are sure that it is necessary.
Note: Output only {file_name_purpose}
''' + '\n' + template_code_wrapping_string + '''

Remember: 
The playground (app.py) must always use the host on http://localhost:8080 and must not let the user configure the host on the UI.
The playground (app.py) must not import the executor.
'''
)

template_pm_task_iteration = PromptTemplate.from_template(
    '''{micro_service_initial_description}
1.Quickly go through the checklist (input/output well defined? api or db access needed?)  and think about if you should ask something to the client or if you should write the final description.
2.Either write the prompt.json or the final.json file.
Either ask for clarification like this:
**prompt.json**
```json
{{
    "question": "<prompt to the client here (must be only one question)>"
}}
```

Or write the detailed microservice description all mentioned code samples, documentation info and credentials like this:
**final.json**
```json
{{
    "description": "<microservice description here>",
    "example_input": "<example input file or string here if mentioned before otherwise n/a>",
    "code_samples": "<code samples from the client here>",
    "documentation_info": "<documentation info here>",
    "credentials: "<credentials here>"
}}
``` 
Note that your response must be either prompt.json or final.json. You must not write both.
Note that you must obey the double asterisk and triple backtick syntax from above.
Note that the last sequence of characters in your response must be ``` (triple backtick).
Note that prompt.json must not only contain one question.
Note that if urls, secrets, database names, etc. are mentioned, they must be part of the summary.
{custom_suffix}
'''
)

template_pm_test_iteration = PromptTemplate.from_template(
    '''{micro_service_initial_description}
1. write down if the microservice requires input.
2. if it requires input, then write down if the original description or the refined description contain an example input for the microservice.
3. write down either prompt.json or final.json.
If the example input for the microservice is mentioned in the refined description or the original description, then output final.json.
Otherwise, output prompt.json where you ask for the example input file as URL or the example string.
Except for urls, you should come up with your own example input that makes sense for the microservice description.

Example for the case where an example input file is required and was not mentioned before:
**prompt.json**
```json
{{
    "question": "Can you please provide an example input file as URL?"
}}
```

Example for the case where the example input string is required and was not mentioned before:
**prompt.json**
```json
{{
    "question": "Can you please provide an example input string?"
}}
```
Note that you must not ask for an example input in case the example input is already mentioned in the refined description or the original description.
Note that you must not ask for an example input in case the microservice does not require input.

Example for the case where the example is already mentioned in the refined description or the original description:
**final.json**
```json
{{
    "input": "<input here>",
    "assertion": "the output contains the result that is of type <type here>"
}}
```
Note that your response must be either prompt.json or final.json. You must not write both.
Note that you must obey the double asterisk and triple backtick syntax from above.
Note that the last sequence of characters in your response must be ``` (triple backtick).
Note that your response must start with the character sequence ** (double asterisk).
Note that prompt.json must only contain one question.
{custom_suffix}
'''
)
