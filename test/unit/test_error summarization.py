import os

from dev_gpt.options.generate.generator import Generator


def test_error_summarization(tmpdir):
    os.environ['VERBOSE'] = 'true'
    generator = Generator('', os.path.join(tmpdir), 'gpt-3.5-turbo', self_healing=False)
    error_message = '''\
#17 [7/7] RUN pytest test_microservice.py
#17 1.699 ============================= test session starts ==============================
#17 1.699 platform linux -- Python 3.9.16, pytest-7.3.1, pluggy-1.0.0
#17 1.699 rootdir: /workdir
#17 1.699 plugins: anyio-3.6.2
#17 1.699 collected 1 item
#17 1.699 
#17 1.699 test_microservice.py F                                                   [100%]
#17 2.063 
#17 2.063 =================================== FAILURES ===================================
#17 2.063 _______________________________ test_output_type _______________________________
#17 2.063 
#17 2.063     def test_output_type():
#17 2.063         """
#17 2.063         The test asserts that the output of the microservice is of type 'str'.
#17 2.063         Input Example: https://www.africau.edu/images/default/sample.pdf
#17 2.063         """
#17 2.063         input_dict = {'file_url': 'https://www.africau.edu/images/default/sample.pdf'}
#17 2.063         input_json_dict_string = json.dumps(input_dict)
#17 2.063 >       output_json_dict_string = func(input_json_dict_string)
#17 2.063 
#17 2.063 test_microservice.py:12: 
#17 2.063 _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
#17 2.063 microservice.py:50: in func
#17 2.063     text = extract_text_from_pdf(pdf_file)
#17 2.063 _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
#17 2.063 
#17 2.063 file_path = <_io.BytesIO object at 0x7f702784dae0>
#17 2.063 
#17 2.063     def extract_text_from_pdf(file_path: str) -> str:
#17 2.063 >       with open(file_path, 'rb') as pdf_file:
#17 2.063 E       TypeError: expected str, bytes or os.PathLike object, not BytesIO
#17 2.063 
#17 2.063 microservice.py:10: TypeError
#17 2.063 =========================== short test summary info ============================
#17 2.063 FAILED test_microservice.py::test_output_type - TypeError: expected str, byte...
#17 2.063 ============================== 1 failed in 1.28s ==============================='''
    summarized_error = generator.summarize_error(error_message)
    assert 'def test_output_type():' in summarized_error
    assert 'output_json_dict_string = func(input_json_dict_string)' in summarized_error
    assert 'microservice.py:10: TypeError' in summarized_error
    assert 'def extract_text_from_pdf(file_path: str) -> str:' in summarized_error
    assert 'with open(file_path, \'rb\') as pdf_file:' in summarized_error
    assert 'TypeError: expected str, bytes or os.PathLike object, not BytesIO' in summarized_error
