from src.apis.jina_cloud import deploy_on_jcloud
from src.options import validate_folder_is_correct, get_executor_name, get_latest_version_path


class Deployer:
    def deploy(self, microservice_path):
        validate_folder_is_correct(microservice_path)
        executor_name = get_executor_name(microservice_path)
        latest_version_path = get_latest_version_path(microservice_path)
        deploy_on_jcloud(executor_name, latest_version_path)