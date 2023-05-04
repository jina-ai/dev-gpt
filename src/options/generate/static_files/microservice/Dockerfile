FROM jinaai/gpt-dev:{{DOCKER_BASE_IMAGE_VERSION}}

RUN apt-get install --no-install-recommends -y {{APT_GET_PACKAGES}}

## install requirements for the executor
COPY requirements.txt .
RUN pip -v install --compile -r requirements.txt

# setup the workspace
COPY . /workdir/
WORKDIR /workdir

RUN pytest test_microservice.py

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]