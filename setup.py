
# python setup.py --dry-run --verbose install

from distutils.core import setup


setup(
    name='lnetatmo',
    version='0.9.2.1',  # Should be updated with new versions
    author='Philippe Larduinat',
    author_email='philippelt@users.sourceforge.net',
    py_modules=['lnetatmo'],
    packages=['smart_home'],
    package_dir={'smart_home': 'smart_home'},
    scripts=[],
    data_files=[],
    url='https://github.com/philippelt/netatmo-api-python',
    license='Open Source',
    description='Simple API to access Netatmo weather station data from any python script.',
    long_description=open('README.md').read()
)
