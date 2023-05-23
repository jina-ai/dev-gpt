from dev_gpt.apis.jina_cloud import clean_color_codes
from dev_gpt.utils.string_tools import clean_large_words


def test_clean_color_codes():
    color_start = f"\033[{31}m"
    reset = "\033[0m"
    bold_start = "\033[1m"
    color = f"{bold_start}{color_start}test{reset}"
    cleaned = clean_color_codes(color)
    print('with color codes:', color)
    print('without color codes:', cleaned)


def test_clean_large_words():
    assert clean_large_words(
        '''test 2VAzLpbBUDBInhtN5ToJZAXL8L6F4J+Xr/L/42vs2r+9Pb0E3Y1ZLy7E3GsYRzAqQ037iKABMHL9VDoAaBAuAGgQLgBoEC4AaBAuAGgQLgB\
oEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAG\
gQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4Aa\
BAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBoEC4AaBAuAGgQLgBo test'''
    ) == 'test 2VAzLpbBUDBInhtN5ToJ...LgBoEC4AaBAuAGgQLgBo test'

    assert clean_large_words('2VAzLpbBUDBInhtN5ToJZAXL8L6F4J+Xr/L/4') == '2VAzLpbBUDBInhtN5ToJZAXL8L6F4J+Xr/L/4'
