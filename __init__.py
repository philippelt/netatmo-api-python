"""Simple API to access Netatmo weather station data from any python script.

"""

import sys
if sys.hexversion < 0x20703f0 :
    sys.stderr.write("You need python 2.7 or later to run this script\n")

__revision__  = "$Id: 20141001 $"
__version__   = '0.3'
__author__    = 'Philippe Larduinat <philippelt@users.sourceforge.net>'
__copyright__ = "Copyright (C) 2014 Philippe Larduinat"
__license__   = "Open Source"


import lnetatmo

__import__('pkg_resources').declare_namespace(__name__)

__all__ = ['ClientAuth', 'User', 'DeviceList']

if __name__ == "__main__":
    import __main__
    print(__main__.__file___)
    print("lnetatmo.__init__")
    print("syntax ok")
    exit(0)
