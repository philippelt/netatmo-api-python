# python setup.py --dry-run --verbose install

from distutils.core import setup

setup(
    name='lnetatmo',
    version='4.0.1',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3'
        ],
    author='Philippe Larduinat',
    author_email='ph.larduinat@wanadoo.fr',
    py_modules=['lnetatmo'],
    scripts=[],
    data_files=[],
    url='https://github.com/philippelt/netatmo-api-python',
    download_url='https://github.com/philippelt/netatmo-api-python/archive/v4.0.1.tar.gz',
    license='GPL V3',
    description='Simple API to access Netatmo weather station data from any python script.'
)
