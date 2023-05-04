FROM jinaai/gpt-dev:latest
# update pip
RUN pip install --upgrade pip

RUN apt-get install --no-install-recommends -y {{apt_get_packages}}

## install requirements for the executor
COPY requirements.txt .
RUN pip -v install --compile -r requirements.txt

# setup the workspace
COPY . /workdir/
WORKDIR /workdir

RUN pytest test_microservice.py

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]