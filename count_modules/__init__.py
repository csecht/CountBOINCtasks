"""
Constants used in --about calls and other modules; program_name is used
throughout the main script.

Program exits here if Python interpreter is not minimum required version.
Confirm that the boinccmd path exists; option to modify path if not.
"""

from . import vcheck, instances, boinc_commands, platform_check

__author__ = 'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2021-2022 C.S. Echt'
__license__ = 'GNU General Public License'
__credits__ =   ['Inspired by rickslab-gpu-utils',
                 'Keith Myers - count-tasks: testing, debug']
__version__ = '0.11.10'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

program_name = instances.program_name()

LICENSE = """
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
    See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program (the LICENCE.txt file). If not, see
    https://www.gnu.org/licenses/."""

platform_check.check_platform()
vcheck.minversion('3.6')

boinc_commands.set_boincpath()
