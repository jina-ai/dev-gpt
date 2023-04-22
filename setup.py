from setuptools import setup, find_packages

def read_requirements():
    with open('requirements.txt', 'r', encoding='utf-8') as f:
        return [line.strip() for line in f.readlines() if not line.startswith('#')]


setup(
    name='gptdeploy',
    version='0.18.24',
    description='Use natural language interface to generate, deploy and update your microservice infrastructure.',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Florian Hönicke',
    author_email='florian.hoenicke@jina.ai',
    url='https://github.com/jina-ai/gptdeploy',
    packages=find_packages(),
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
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)
