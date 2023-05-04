import os

from src.apis.jina_cloud import is_executor_in_hub
from src.apis.pypi import is_package_on_pypi, clean_requirements_txt
from src.options.generate.generator import Generator


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


def test_filter_packages_list():
    filtered_list = Generator.filter_packages_list([
        ["gpt_3_5_turbo", "requests", "base64", "gtts", "pydub"],
        ["requests", "base64", "gtts", "pydub"],
        ["gpt_3_5_turbo", "requests", "base64", "gtts"],
        ["gpt_3_5_turbo", "requests", "base64", "pydub"],
        ["requests", "base64", "gtts"]
    ])
    assert filtered_list == [
        ["gpt_3_5_turbo", "requests", "gtts", "pydub"],
        ["requests", "gtts", "pydub"],
        ["gpt_3_5_turbo", "requests", "gtts"],
        ["gpt_3_5_turbo", "requests", "pydub"],
        ["requests", "gtts"]
    ]


def test_precheck_requirements_txt(tmpdir):
    requirements_content = """\
# version does not exist but jina and docarray should not be verified
jina==111.222.333
docarray==111.222.333
# package that actually exists in that version
gtts~=2.2.3
# package with non-existing version
pydub~=123.123.123
# non-existing package with correct version
base64~=3.3.0
# not parsable version
pdfminer.six>=20201018,<20211018
# existing package without version
requests
# another existing package without version
streamlit
"""
    requirements_clean = """\
jina==111.222.333
docarray==111.222.333
gtts~=2.2.3
pydub~=0.25.1
pdfminer.six~=20201018
requests~=2.26.0
streamlit~=0.89.0"""
    requirements_txt_path = os.path.join(tmpdir, "requirements.txt")
    with open(requirements_txt_path, "w", encoding="utf-8") as f:
        f.write(requirements_content)

    clean_requirements_txt(tmpdir)

    with open(requirements_txt_path, "r", encoding="utf-8") as f:
        updated_requirements = f.read()

    assert updated_requirements == requirements_clean
