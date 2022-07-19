from . import vcheck, instances, boinc_commands

"""
Constants used in Fyi.about(); program_name used throughout.
Program exits here if Python interpreter is not minimum required version.
Confirm that the boinccmd path exists; option to modify if not.
"""

__author__ = 'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2021-2022 C.S. Echt'
__license__ = 'GNU General Public License'
__credits__ = 'Inspired by rickslab-gpu-utils'
__version__ = '0.11.2'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 2 - Beta'

program_name = instances.program_name()

vcheck.minversion('3.6')

boinc_commands.set_boincpath()
