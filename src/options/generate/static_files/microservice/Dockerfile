FROM jinaai/jina:3.14.1-py39-standard

## install requirements for the executor
COPY requirements.txt .
RUN pip install --compile -r requirements.txt

# setup the workspace
COPY . /workdir/
WORKDIR /workdir

RUN pytest test_microservice.py

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]