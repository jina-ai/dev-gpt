from src.apis.jina_cloud import run_locally
from src.options import validate_folder_is_correct, get_executor_name, get_latest_version_path


class Runner():
    def run(self, microservice_path):
        validate_folder_is_correct(microservice_path)
        executor_name = get_executor_name(microservice_path)
        latest_version_path = get_latest_version_path(microservice_path)
        run_locally(executor_name, latest_version_path)

