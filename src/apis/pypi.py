import requests

def is_package_on_pypi(package_name, version=None):
    optional_version = f"/{version}" if version else ""
    url = f"https://pypi.org/pypi/{package_name}{optional_version}/json"
    response = requests.get(url)
    if response.status_code == 200:
        return True
    elif response.status_code == 404:
        return False
    else:
        return None