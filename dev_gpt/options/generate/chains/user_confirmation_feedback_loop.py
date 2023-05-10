from dev_gpt.apis.gpt import ask_gpt
from dev_gpt.options.generate.parser import identity_parser


def user_feedback_loop(context, current_description):
    while (user_feedback := get_user_feedback(current_description)):
        context['user_feedback'] = user_feedback
        current_description = ask_gpt(
            add_feedback_prompt,
            identity_parser,
            **context
        )
        del context['user_feedback']
    return current_description

def get_user_feedback(microservice_description):
    while True:
        user_feedback = input(
            f'I suggest that we implement the following microservice:\n{microservice_description}\nDo you agree? [y/n]')
        if user_feedback.lower() in ['y', 'yes', 'yeah', 'yep', 'yup', 'sure', 'ok', 'okay']:
            print('Great! I will hand this over to the developers!')
            return None
        elif user_feedback.lower() in ['n', 'no', 'nope', 'nah', 'nay', 'not']:
            return input('What do you want to change?')


add_feedback_prompt = '''\
Microservice description:
```
{microservice_description}
```

User feedback:
```
{user_feedback}
```

Update the microservice description by incorporating the user feedback in a concise way without losing any information.'''