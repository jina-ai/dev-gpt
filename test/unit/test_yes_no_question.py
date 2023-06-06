import os

from dev_gpt.apis.gpt import GPTSession
from dev_gpt.options.generate.chains.question_answering import answer_yes_no_question


def test_answer_yes_no_question(init_gpt):
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
''', 'Based on the microservice description, does the microservice interface with APIs?'
    )

def test_answer_yes_no_question_2(init_gpt):
    assert not answer_yes_no_question(
        '''\
Microservice description:
```
This microservice takes a list of email addresses as input and returns a grid pattern PNG image of company logos corresponding to the unique domain names extracted from the email addresses. The logos are obtained by searching for them using the Google Custom Search API and then resizing them to a square shape. The microservice returns the PNG image as a base64 encoded string. The input JSON must contain an array of email addresses under the key "emails". The output JSON contains a base64 encoded string of the logo grid image under the key "logo_grid".
```

Request schema:
```
{
  "type": "object",
  "properties": {
    "emails": {
      "type": "array",
      "items": {
        "type": "string",
        "format": "email"
      }
    }
  },
  "required": ["emails"]
}
```

Response schema:
```
{
  "type": "object",
  "properties": {
    "logo_grid": {
      "type": "string",
      "format": "base64"
    }
  },
  "required": ["logo_grid"]
}
```''', 'Does the request schema provided include a property that represents a file?')