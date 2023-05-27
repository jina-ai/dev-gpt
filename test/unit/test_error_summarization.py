from dev_gpt.options.generate.generator import Generator
import os


def test_error_summarization(tmpdir):
    os.environ['VERBOSE'] = 'true'
    generator = Generator('', str(tmpdir), 'gpt-3.5-turbo')
    summary = generator.summarize_error('''\
#15 [7/7] RUN pytest test_microservice.py
#15 3.142 ============================= test session starts ==============================
#15 3.142 platform linux -- Python 3.9.16, pytest-7.3.1, pluggy-1.0.0
#15 3.142 rootdir: /workdir
#15 3.142 plugins: anyio-3.6.2
#15 3.142 collected 1 item
#15 3.142 
#15 3.142 test_microservice.py F                                                   [100%]
#15 4.780 
#15 4.780 =================================== FAILURES ===================================
#15 4.780 ____________________________ test_func_output_type _____________________________
#15 4.780 
#15 4.780     def test_func_output_type():
#15 4.780         """
#15 4.780         The test asserts that the output of func is of type 'object'.
#15 4.780         """
#15 4.780         input_dict = {'stock_symbol': 'AAPL'}
#15 4.780         input_json_dict_string = json.dumps(input_dict)
#15 4.780 >       output_json_dict_string = func(input_json_dict_string)
#15 4.780 
#15 4.780 test_microservice.py:11: 
#15 4.780 _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
#15 4.780 
#15 4.780 input_json_dict_string = '{"stock_symbol": "AAPL"}'
#15 4.780 
#15 4.780     def func(input_json_dict_string: str) -> str:
#15 4.780         """
#15 4.780         The microservice accepts a stock symbol as input and returns a summary of the company's stock performance over the past 30 days, including the company name and the average closing price. The input parameter is a string representing the stock symbol, and the output is a JSON object containing the company name and the average closing price. The microservice fetches stock data from an external API, calculates the average closing price, and generates a brief summary of the company's stock performance.
#15 4.780         """
#15 4.780         input_dict = json.loads(input_json_dict_string)
#15 4.780         stock_symbol = input_dict['stock_symbol']
#15 4.780         stock_data = yf.download(stock_symbol, period='30d')
#15 4.780         if stock_data.empty:
#15 4.780             return json.dumps({'error': 'Invalid stock symbol'})
#15 4.780 >       company_name = yf.Ticker(stock_symbol).info['longName']
#15 4.780 E       KeyError: 'longName'
#15 4.780 
#15 4.780 microservice.py:16: KeyError
#15 4.780 ----------------------------- Captured stdout call -----------------------------
#15 4.780 
[*********************100%***********************]  1 of 1 completed
#15 4.780 =========================== short test summary info ============================
#15 4.780 FAILED test_microservice.py::test_func_output_type - KeyError: 'longName'
#15 4.780 ============================== 1 failed in 3.31s ===============================''')
    assert 'longName' in summary
    assert 'yf.Ticker(stock_symbol).info' in summary
    assert 'KeyError' in summary
    assert 'microservice.py' in summary

