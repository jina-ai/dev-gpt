import traceback



def fix_based_on_error_chain(context_string, content_type, original_content, parser):
    from dev_gpt.apis.gpt import ask_gpt
    current_content = original_content
    for i in range(3):
        try:
            return parser(current_content)
        except Exception:
            error_message = traceback.format_exc()
            current_content = ask_gpt(fix_based_on_error_prompt, context_string=context_string, content_type=content_type, current_content=current_content, error_message=error_message)
    raise Exception(f'Could not fix the content:\n{original_content}')


fix_based_on_error_prompt = '''\
Context:
{context_string}

Original {content_type}:
{current_content}

Error message:
{error_message}

Your task:
You must return the fixed {content_type}.
Most importantly, you are not allowed to return something else - only the fixed {content_type}.

Positive example:
**solution.json**
```json
{
    "key1": "value1",
    "key2": "value2"
}
Negative example:
{
    "key1": "value1",
    "key2": "value2"
} 
'''



