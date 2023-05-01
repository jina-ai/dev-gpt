from src.apis.jina_cloud import is_executor_in_hub
from src.apis.pypi import is_package_on_pypi


def test_is_microservice_in_hub():
    assert is_executor_in_hub('reoihoflsnvoiawejeruhvflsfk') is False
    assert is_executor_in_hub('CLIPImageEncoder') is True

def test_is_package_on_pypi():
    assert is_package_on_pypi('jina') is True
    assert is_package_on_pypi('jina', '0.9.25') is True
    assert is_package_on_pypi('jina', '10.10.10') is False
    assert is_package_on_pypi('jina-jina-jina') is False
    assert is_package_on_pypi('jina-jina-jina', '0.9.25') is False
    assert is_package_on_pypi('jina-jina-jina', '10.10.10') is False
