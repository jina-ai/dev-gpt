FROM jinaai/jina:3.14.1-py39-standard
# update pip
RUN pip install --upgrade pip

RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg build-essential pkg-config libpoppler-cpp-dev {{apt_get_packages}} && apt-get clean && rm -rf /var/lib/apt/lists/*

## install requirements for the executor
COPY requirements.txt .
RUN pip -v install --compile -r requirements.txt

# setup the workspace
COPY . /workdir/
WORKDIR /workdir

RUN pytest test_microservice.py

ENTRYPOINT ["jina", "executor", "--uses", "config.yml"]