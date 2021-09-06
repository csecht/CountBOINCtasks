import os
import py2exe 
from distutils.core import setup


"""
Usage: python setup.py py2exe
"""

# The data_files takes a tuple 1) the location to store the data and
#   2) the location to copy the data from.

DATA_FILES = []
for files in os.listdir('C:/Users/Craig/Desktop/count_tasks_dev/COUNTmodules/'):
    f1 = './COUNTmodules/' + files
    if os.path.isfile(f1): # skip directories
        f2 = 'CountModules', [f1]
        DATA_FILES.append(f2)
        
setup(
        windows=['gcount-tasks.py',],
        data_files=DATA_FILES,
        name='CountBOINCtasks',
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
        # options={"py2exe":{"unbuffered": True, "optimize": 2}} 
)
 
