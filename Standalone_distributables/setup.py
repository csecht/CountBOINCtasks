"""
The standalone executables included in this distribution can be created
using a version of this script customized for your file path of DATA_FILES.

USAGE: Place this setup.py file in the CountBOINCtasks-master folder and run it
from a Terminal.
MacOS command:
    python3 setup.py py2app
Windows command:
    python setup.py py2exe

For all systems, the COUNTmodules folder and the gcount-tasks file from the
CountBOINCtasks repository must be in the parent folder where this is executed.

You will also need to install one of these programs:
py2app installation: https://pypi.org/project/py2app/
py2exe installation: https://pypi.org/project/py2exe/

Additional information: https://pythonhosted.org/an_example_pypi_project/setuptools.html
"""

import os
from setuptools import setup  # comment out for Windows, uncomment for MacOS

# uncomment below for Windows
# import py2exe
# from distutils.core import setup

# NOTE: The DATA_FILES list takes a tuple 1) f1: the location to store the data and
#   2) f2: location to copy the data from.

DATA_FILES = []
# Mac path example:
for files in os.listdir('/Users/Craig/Applications/counttasks_dev_py2app/'):
    # Windows path example:
    # for files in os.listdir('C:/Users/$USER/Desktop/CountBOINCtasks-master/COUNTmodules/'):
    f1 = './COUNTmodules/' + files
    if os.path.isfile(f1):  # skip directories
        f2 = 'CountModules', [f1]
        DATA_FILES.append(f2)

setup(
    app=['gcount-tasks'],  # comment for Windows
    # windows=['gcount-tasks',],    # uncomment for Windows
    data_files=DATA_FILES,
    name='GcountTasks',
    author='C.S. Echt',
    description='A utility to mot monitor BOINC task status and metrics',
    license='GNU General Public License',
    keywords="BOINC 'BOINC Manager'",
    url='https://github.com/csecht/CountBOINCtasks',
    classifiers=[
        'Development Status ::  - Beta',
        'Topic :: Utilities',
        'License :: GNU License',
        'Programming Language :: Python :: 3.8'
    ],
    # options={'py2app':{}}
    # options={"py2exe":{"unbuffered": True, "optimize": 2}}
)
