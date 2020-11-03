import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "redis_client",
    version = "1.0.0",
    author = "Josh-2",
    author_email = "",
    description = ("Redis client"),
    long_description=read('README.md'),
    packages=['redis_client'],
    install_requires=[
        'redis'
    ],
)
