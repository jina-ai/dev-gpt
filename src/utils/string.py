def find_between(input_string, start, end):
    try:
        start_index = input_string.index(start) + len(start)
        end_index = input_string.index(end, start_index)
        return input_string[start_index:end_index]
    except ValueError:
        raise ValueError(f'Could not find {start} and {end} in {input_string}')


def clean_content(content):
    return content.replace('```', '').strip()

def print_colored(headline, text, color_code):
    if color_code == 'black':
        color_code = '30'
    elif color_code == 'red':
        color_code = '31'
    elif color_code == 'green':
        color_code = '32'
    elif color_code == 'yellow':
        color_code = '33'
    elif color_code == 'blue':
        color_code = '34'
    elif color_code == 'magenta':
        color_code = '35'
    elif color_code == 'cyan':
        color_code = '36'
    elif color_code == 'white':
        color_code = '37'
    color_start = f"\033[{color_code}m"
    reset = "\033[0m"
    bold_start = "\033[1m"
    print(f"{bold_start}{color_start}{headline}{reset}")
    print(f"{color_start}{text}{reset}")
