import os
from setuptools import setup

def read(file_name):
    return open(os.path.join(os.path.dirname(__file__), file_name)).read()

setup(
    name = "redis_client",
    version = "1.0.3",
    author = "Josh-2",
    author_email = "",
    description = ("Redis client"),
    long_description=read('README.md'),
    packages=['redis_client'],
    install_requires=[
        'redis'
    ],
)
