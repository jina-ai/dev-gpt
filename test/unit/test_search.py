from dev_gpt.options.generate.static_files.microservice.search import search_web, search_images


def test_web_search():
    results = search_web("jina", 10)
    assert len(results) == 10
    assert "jina" in results[0]
    assert not results[0].startswith("http")

def test_image_search():
    results = search_images("jina", 10)
    assert len(results) == 10
    assert results[0].startswith("http")
