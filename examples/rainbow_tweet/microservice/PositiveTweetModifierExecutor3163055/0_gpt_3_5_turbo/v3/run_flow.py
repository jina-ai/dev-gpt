from jina import Flow

flow = Flow.load_config('flow.yml')
with flow:
    flow.block()