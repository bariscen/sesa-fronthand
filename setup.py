from setuptools import setup
from setuptools import find_packages

with open('requirements.txt') as f:
    content=f.readlines()
req = [x.strip() for x in content]


setup(name = 'sesa_str', install_requires = req,
      packages = find_packages())
