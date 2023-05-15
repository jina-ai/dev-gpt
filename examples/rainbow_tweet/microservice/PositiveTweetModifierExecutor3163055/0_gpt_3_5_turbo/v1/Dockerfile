FROM jinaai/dev-gpt:0.0.6



RUN apt-get install --no-install-recommends -y 



## install requirements for the executor

COPY requirements.txt .

RUN pip -v install --compile -r requirements.txt



# setup the workspace

COPY . /workdir/

WORKDIR /workdir



RUN pytest test_microservice.py



ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]