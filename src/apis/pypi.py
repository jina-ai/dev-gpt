import os
import re
from datetime import datetime

import requests
from packaging import version


def is_package_on_pypi(package_name, version=None):
    """
    Returns True if the package is on PyPI, False if it is not, and None if the status code is not 200 or 404.
    """
    optional_version = f"/{version}" if version else ""
    url = f"https://pypi.org/pypi/{package_name}{optional_version}/json"
    response = requests.get(url)
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    else:
        return None


def get_latest_package_version(package_name):
    """
    Returns the latest version of a package that is not older than 2021.
    """
    url = f'https://pypi.org/pypi/{package_name}/json'
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    releases = data['releases']

    # Get package versions not older than 2021
    valid_versions = []
    for v, release_info in releases.items():
        if not release_info:
            continue
        upload_time = datetime.strptime(release_info[0]['upload_time'], '%Y-%m-%dT%H:%M:%S')
        if upload_time.year <= 2020 or (upload_time.year == 2021 and upload_time.month <= 9):  # knowledge cutoff 2021-09 (including september)
            valid_versions.append(v)

    v = max(valid_versions, key=version.parse) if valid_versions else None
    return v


def clean_requirements_txt(previous_microservice_path):
    """
    It can happen that the generated requirements.txt contains packages that are not on PyPI (like base64).
    In this case, we remove the requirement from requirements.txt.
    In case the package is on PyPI, but the version is not, we update the version to the latest version that is still not older than 2021.
    """
    requirements_txt_path = os.path.join(previous_microservice_path, 'requirements.txt')
    with open(requirements_txt_path, 'r', encoding='utf-8') as f:
        requirements_txt = f.read()

    updated_requirements = []

    for line in requirements_txt.split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        split = re.split(r'==|>=|<=|>|<|~=', line)
        if len(split) == 1 or len(split) > 2:
            version = None
            package_name = split[0]
        else:
            package_name, version = split


        # Keep lines with jina, docarray, openai, pytest unchanged
        if package_name in {'jina', 'docarray', 'openai', 'pytest'}:
            updated_requirements.append(line)
            continue
        if is_package_on_pypi(package_name):
            if version is None or not is_package_on_pypi(package_name, version):
                latest_version = get_latest_package_version(package_name)
                if latest_version is None:
                    continue
                updated_requirements.append(f'{package_name}~={latest_version}')
            else:
                updated_requirements.append(line)

    with open(requirements_txt_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(updated_requirements))
