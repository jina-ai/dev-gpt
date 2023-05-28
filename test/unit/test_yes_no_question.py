import os

from dev_gpt.apis.gpt import GPTSession
from dev_gpt.options.generate.chains.question_answering import answer_yes_no_question


def test_answer_yes_no_question(tmpdir):
    os.environ['VERBOSE'] = 'true'
    GPTSession(os.path.join(str(tmpdir), 'log.json'), model='gpt-3.5-turbo')
    assert answer_yes_no_question(
        '''\
Microservice description:
```
The microservice takes a stock symbol as input and returns a summary of the company's stock performance over the past 30 days, \
including the average closing price and the company name. \
The summary is returned as a string. \
The microservice uses the Yahoo Finance API to fetch the stock data and Python libraries to calculate the average closing price and generate the summary. \
The request parameter is "stock_symbol" and the response parameter is "summary".
```
''', 'Does the microservice send requests to an API beside the google_custom_search and gpt_3_5_turbo?'
    ) == True