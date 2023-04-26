from src.apis.jina_cloud import is_executor_in_hub


def test_is_microservice_in_hub():
    assert is_executor_in_hub('reoihoflsnvoiawejeruhvflsfk') is False
    assert is_executor_in_hub('CLIPImageEncoder') is True
