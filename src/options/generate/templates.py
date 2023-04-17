from langchain import PromptTemplate

template_generate_microservice_name = PromptTemplate.from_template(
    '''Generate a name for the executor matching the description:
"{description}"
The executor name must fulfill the following criteria:
- camel case
- start with a capital letter
- only consists of lower and upper case characters
- end with Executor.

The output is a the raw string wrapped into ``` and starting with **name.txt** like this:
**name.txt**
```
PDFParserExecutor
```'''
)


template_generate_possible_packages = PromptTemplate.from_template(
    '''Here is the task description of the problem you need to solve:
"{description}"
1. Write down all the non-trivial subtasks you need to solve.
2. Find out what is the core problem to solve.
3. List up to 15 Python packages that are specifically designed or have functionalities to solve the complete core problem.
4. For each of the 15 package think if it fulfills the following requirements:
a) specifically designed or have functionalities to solve the complete core problem.
b) has a stable api among different versions
c) does not have system requirements
d) can solve the task when running in a docker container
e) the implementation of the core problem using the package would obey the following rules:
{not_allowed_executor}
When answering, just write "yes" or "no".

5. Output the most suitable 5 python packages starting with the best one. 
If the package is mentioned in the description, then it is automatically the best one.

The output must be a list of lists wrapped into ``` and starting with **packages.csv** like this:
**packages.csv**
```
package1
package2
package3
package4
package5
...
```
''')


template_solve_code_issue = PromptTemplate.from_template(
    '''General rules: {not_allowed_executor}
Here is the description of the task the executor must solve:
{description}

Here is the test scenario the executor must pass:\n{test}
Here are all the files I use:
{all_files_string}


This is the error I encounter currently during the docker build process:
{error}

Look at the stack trace of the current error. First, think about what kind of error is this? 
Then think about possible reasons which might have caused it. Then suggest how to 
solve it. Output all the files that need change. 
Don't output files that don't need change. If you output a file, then write the 
complete file. Use the exact same syntax to wrap the code:
**...**
```...
...code...
```
'''
)


template_solve_dependency_issue = PromptTemplate.from_template(
    '''Your task is to provide guidance on how to solve an error that occurred during the Docker build process. 
The error message is:
**microservice.log**
```
{error}
```
To solve this error, you should:
1. Identify the type of error by examining the stack trace. 
2. Suggest how to solve it. 
3. Your suggestion must include the files that need to be changed, but not files that don't need to be changed. 
For files that need to be changed, you must provide the complete file with the exact same syntax to wrap the code.
Obey the following rules: {not_allowed_docker}

You are given the following files:

{all_files_string}
'''
)


template_is_dependency_issue = PromptTemplate.from_template(
    '''Your task is to assist in identifying the root cause of a Docker build error for a python application.
The error message is as follows:

{error}

The docker file is as follows:

{docker_file}

Is this a dependency installation failure? Answer with "yes" or "no".'''
)


template_generate_playground = PromptTemplate.from_template(
    '''{general_guidelines}

{code_files_wrapped}

Create a playground for the executor {microservice_name} using streamlit.
The playground must look like it was made by a professional designer.
All the ui elements are well thought out to make them visually appealing and easy to use.
This is an example how you can connect to the executor assuming the document (d) is already defined:
```
from jina import Client, Document, DocumentArray
client = Client(host=host)
response = client.post('/', inputs=DocumentArray([d])) # always use '/'
print(response[0].text) # can also be blob in case of image/audio..., this should be visualized in the streamlit app
```
Note that the response will always be in response[0].text
You must provide the complete file with the exact same syntax to wrap the code.
The playground (app.py) must read the host from sys.argv because it will be started with a custom host: streamlit run app.py -- --host grpc://...
The playground (app.py) must not let the user configure the host on the ui.
'''
)
