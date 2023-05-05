FROM jinaai/jina:3.15.1-dev14-py39-standard

# update pip
RUN pip install --upgrade pip

# install media dependencies
RUN apt-get update && apt-get install --no-install-recommends -y ffmpeg build-essential pkg-config libpoppler-cpp-dev