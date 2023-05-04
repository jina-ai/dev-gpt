DOCKER_BASE_IMAGE_VERSION = '0.0.4'

EXECUTOR_FILE_NAME = '__init__.py'
IMPLEMENTATION_FILE_NAME = 'microservice.py'
TEST_EXECUTOR_FILE_NAME = 'test_microservice.py'
REQUIREMENTS_FILE_NAME = 'requirements.txt'
DOCKER_FILE_NAME = 'Dockerfile'
CLIENT_FILE_NAME = 'client.py'
STREAMLIT_FILE_NAME = 'streamlit.py'

EXECUTOR_FILE_TAG = 'python'
IMPLEMENTATION_FILE_TAG = 'python'
TEST_EXECUTOR_FILE_TAG = 'python'
REQUIREMENTS_FILE_TAG = ''
DOCKER_FILE_TAG = 'dockerfile'
CLIENT_FILE_TAG = 'python'
STREAMLIT_FILE_TAG = 'python'

FILE_AND_TAG_PAIRS = [
    (EXECUTOR_FILE_NAME, EXECUTOR_FILE_TAG),
    (IMPLEMENTATION_FILE_NAME, IMPLEMENTATION_FILE_TAG),
    (TEST_EXECUTOR_FILE_NAME, TEST_EXECUTOR_FILE_TAG),
    (REQUIREMENTS_FILE_NAME, REQUIREMENTS_FILE_TAG),
    (DOCKER_FILE_NAME, DOCKER_FILE_TAG),
    (CLIENT_FILE_NAME, CLIENT_FILE_TAG),
    (STREAMLIT_FILE_NAME, STREAMLIT_FILE_TAG)
]

FLOW_URL_PLACEHOLDER = 'jcloud.jina.ai'

PRICING_GPT4_PROMPT = 0.03
PRICING_GPT4_GENERATION = 0.06
PRICING_GPT3_5_TURBO_PROMPT = 0.002
PRICING_GPT3_5_TURBO_GENERATION = 0.002

CHARS_PER_TOKEN = 3.4

NUM_IMPLEMENTATION_STRATEGIES = 5
MAX_DEBUGGING_ITERATIONS = 10

DEMO_TOKEN = '45372338e04f5a41af949024db929d46'

BLACKLISTED_PACKAGES = [
    'moderngl', 'pyopengl', 'pyglet', 'pythreejs', 'panda3d',  # because they need a screen,
    'tika',  # because it needs java
]
UNNECESSARY_PACKAGES = [
    'fastapi', 'uvicorn', 'starlette'  # because the wrappers are used instead
]

LANGUAGE_PACKAGES = [
    'allennlp', 'bertopic', 'fasttext', 'flair', 'gensim', 'nltk',
    'pattern', 'polyglot', 'pytorch-transformers', 'rasa', 'sentence-transformers',
    'spacy', 'stanza', 'summarizer', 'sumy', 'textblob', 'textstat', 'transformers'
]

