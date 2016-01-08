
# python setup.py --dry-run --verbose install

import os.path
from setuptools import setup, find_packages
from distutils.command.install_scripts import install_scripts

from distutils.core import setup

class install_scripts_and_symlinks(install_scripts):
    '''Like install_scripts, but also replicating nonexistent symlinks'''
    def run(self):
      print ("=============install_scripts_and_symlinks run")
      install_scripts.run(self)
      # Replicate symlinks if they don't exist
      print (self)
      print ("data_files = ",  dir( self.distribution.data_files))
      print (type(self.distribution.data_files))
      print (self.distribution.data_files)
      for script in self.distribution.scripts:
        print  ("\n---script = ",script)
        if os.path.islink(script):
          target  = os.readlink(script)
          newlink = os.path.join(self.install_dir, os.path.basename(script))
          if not os.path.exists(newlink):
            print ("++++++++++", target, " -> ", newlink)
            os.symlink(target, newlink)


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
    long_description=open('README.md').read(),
    cmdclass = { 'install_scripts': install_scripts_and_symlinks }
)
