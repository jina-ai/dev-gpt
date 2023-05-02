from src.apis.jina_cloud import clean_color_codes


def test_clean_color_codes():
    color_start = f"\033[{31}m"
    reset = "\033[0m"
    bold_start = "\033[1m"
    color = f"{bold_start}{color_start}test{reset}"
    cleaned = clean_color_codes(color)
    print('with color codes:', color)
    print('without color codes:', cleaned)