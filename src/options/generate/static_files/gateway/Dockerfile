FROM jinaai/jina:3.15.1-dev14-py39-standard


RUN apt-get update && apt-get install --no-install-recommends -y git pip nginx && rm -rf /var/lib/apt/lists/*

## install requirements for the executor
COPY requirements.txt .
RUN pip install --compile -r requirements.txt

# setup the workspace
COPY . /workdir/
WORKDIR /workdir

ENTRYPOINT ["jina", "gateway", "--uses", "config.yml"]