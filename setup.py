from os import path

from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines() if not line.startswith('#')]


try:
    libinfo_py = path.join('src', '__init__.py')
    libinfo_content = open(libinfo_py, 'r', encoding='utf8').readlines()
    version_line = [l.strip() for l in libinfo_content if l.startswith('__version__')][
        0
    ]
    exec(version_line)  # gives __version__
except FileNotFoundError:
    __version__ = '0.0.0'


setup(
    name='dev-gpt',
    version=__version__,
    description='Use natural language interface to generate, deploy and update your microservice infrastructure.',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Florian Hönicke',
    author_email='florian.hoenicke@jina.ai',
    url='https://github.com/jina-ai/gptdeploy',
    packages=find_packages(),
    include_package_data=True,
    install_requires=read_requirements(),
    scripts=['gptdeploy.py'],
    entry_points={
        'console_scripts': [
            'gptdeploy = src:main',
        ],
    },

    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
