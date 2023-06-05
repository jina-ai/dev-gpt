from dev_gpt.options.generate.chains.auto_refine_description import better_description_prompt

prompt_template = better_description_prompt

d = {
    'microservice_description': 'Input is a tweet that contains passive aggressive language. The output is the positive version of that tweet.'
}

task = '''\
The main issue with GPT-3's output is that it violated the given prompt instructions. It used a non-specific formulation "such as GPT-3" to suggest a tool for natural language processing, which is explicitly prohibited in the prompt.

How can I change the prompt template to make this more clear to GPT-3?'''

generated_output = '''\
Microservice Description:

This microservice takes a tweet as input that contains passive aggressive language and returns the positive version of that tweet as output. The microservice performs the following tasks:

1. Use a natural language processing (NLP) tool such as GPT-3 to analyze the input tweet and identify the passive aggressive language.
2. Generate a list of positive words and phrases that can be used to replace the passive aggressive language in the tweet.
3. Replace the passive aggressive language in the tweet with positive words and phrases.
4. Return the positive version of the tweet as output.'''




value_explanations = [
    'This is the value of {k}: "{v}"' for k, v in d.items()
]

value_explanations_string = '\n'.join(value_explanations)


fix_template = f'''\
Here is the prompt template I used for GPT-3:
# start of prompt

{prompt_template}

# end of prompt

{value_explanations_string}


Here is the generated output by GPT-3:
# generated output start

{generated_output}

# generated output end


###### your task #####
{task}
'''