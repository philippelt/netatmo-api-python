# python setup.py --dry-run --verbose install

from distutils.core import setup

setup(
    name='lnetatmo',
    version='2.1.0',
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
    download_url='https://github.com/philippelt/netatmo-api-python/tarball/v2.1.0.tar.gz',
    license='GPL V3',
    description='Simple API to access Netatmo weather station data from any python script.'
)
