
# python setup.py --dry-run --verbose install

import os.path
from setuptools import setup, find_packages
from distutils.command.install_scripts import install_scripts
from distutils.core import setup


setup(
    name='lnetatmo',
    version='0.3.0.dev1', # Should be updated with new versions
    author='Philippe Larduinat',
    author_email='philippelt@users.sourceforge.net',
    packages=find_packages(),
    scripts=[ ],
    data_files=[ ],
    url='https://github.com/philippelt/netatmo-api-python',
    license='Open Source',
    description='Simple API to access Netatmo weather station data from any python script.',
    long_description=open('README.md').read()
)
