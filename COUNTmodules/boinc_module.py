#!/usr/bin/env python3
"""BOINCmodule - executing BOINC commands and parsing task data.
.. note: Not all boinc-client commands are supported.

    Copyright (C) 2020  C. Echt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <https://www.gnu.org/licenses/>.
"""

__author__ = 'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2020 C. Echt'
__credits__ = ['Inspired by rickslab-gpu-utils']
__license__ = 'GNU General Public License'
__program_name__ = 'count-tasks'
__version__ = '0.1.0'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ = 'Development Status :: 3 - Alpha'

import shlex
import shutil
import subprocess
import sys

boinccmd = shutil.which("boinccmd")
# if not boinccmd:
#     print('Package [boinccmd] executable not found. Install for...\n'
#           'Linux: sudo apt-get install boinc-client boinc-manager\n'
#           'Win: see https://boinc.berkeley.edu/wiki/Installing_BOINC\n'
#           'Exiting...')
#     # LOGGER.debug('boinccmd path: %s', boinccmd)
#     sys.exit(1)

try:
    boinccmd = shutil.which("boinccmd")
except OSError as err:
    print('Package [boinccmd] executable not found. Install for...\n'
          'Linux: sudo apt-get install boinc-client boinc-manager\n'
          'Win: see https://boinc.berkeley.edu/wiki/Installing_BOINC\n'
          'Exiting...')
    print(err)
    sys.exit(1)


class BoincCommand:
    """
    Execute boinc-client commands and parse data.
    """

    EINSTEIN = "http://einstein.phys.uwm.edu/"
    MILKYWAY = "http://milkyway.cs.rpi.edu_milkyway/"

    def __init__(self):
        self.boinc = boinccmd
        self.projectcmd = ('suspend', 'resume', 'get_app_config')
        self.tasktags = ('name', 'WU name', 'project URL', 'received',
                         'report deadline', 'ready to report', 'state',
                         'scheduler state',  'active_task_state',
                         'app version num', 'resources', 'final CPU time',
                         'final elapsed time', 'final elapsed time',
                         'exit status', 'signal', 'estimated CPU time '
                         'remaining', 'slot', 'PID', 'current CPU time',
                         'CPU time at last checkpoint', 'fraction done',
                         'swap size', 'working set size')
        self.oldtags = ('task', 'project URL', 'app name', 'exit status',
                        'elapsed time', 'completed time', 'get_reported time')

    def run(self, command: str):
        """
        Format command for system execution of boinc-client action.

        :param command: In use: 'suspend', 'resume', 'read_cc_config'.
        :return: Change in boinc-client action.
        """
        # Project commands require the Project URL, others commands don't
        if command in self.projectcmd:
            cmd_str = f'{self.boinc} --project {self.EINSTEIN} {command}'
            subprocess.check_output(shlex.split(cmd_str), shell=False)
        elif command == 'read_cc_config':
            cmd_str = f'{self.boinc} --{command}'
            subprocess.check_output(shlex.split(cmd_str), shell=False)
        else:
            print(f'Unrecognized command: {command}')
        # LOGGER.debug('bnccmd parameter: %s', command)

    def get_tasks(self, tag: str) -> list:
        """
        Get data from current boinc-client tasks.

        :param tag: Used: 'name', 'state', 'scheduler
                    state', 'fraction done', 'active_task_state'
        :return: List of specified data from current tasks.
        """
        data = []
        cmd_str = f'{self.boinc} --get_tasks'
        tag_str = f'{" " * 3}{tag}: '
        output = subprocess.check_output(shlex.split(cmd_str),
                                         shell=False).decode().split('\n')
        try:
            for i in output:
                if i.__contains__(tag_str):
                    i = i.replace(tag_str, '')
                    data.append(i)
            return data
        except ValueError:
            print(f'Unrecognized data tag: {tag}')
        return data

    def get_reported(self, tag: str) -> list:
        """
        Get data from get_reported boinc-client tasks.

        :param tag: Used: 'task' returns get_reported task names.
                          'elapsed time' returns task times, sec.000000.
        :return: List of specified data from get_reported tasks.
        """
        data = []
        cmd_str = f'{self.boinc} --get_old_tasks'
        output = subprocess.check_output(shlex.split(cmd_str),
                                         shell=False).decode().split('\n')
        # Need to modify search tag to match pattern in boinc output.
        if tag == 'task':
            tag_str = 'task '
        else:
            tag_str = f'{" " * 3}{tag}: '

        try:
            for i in output:
                if i.__contains__(tag_str):
                    i = i.replace(tag_str, '')
                    if tag == 'task':
                        i = i.rstrip(':')
                    if tag == 'elapsed time':
                        i = i.replace(' sec', "")
                        i = float(i)
                    data.append(i)
            return data
        except ValueError:
            print(f'Unrecognized data tag: {tag}')
        return data


def about() -> None:
    """
    Print details about this module.
    """
    print(__doc__)
    print('Author: ', __author__)
    print('Copyright: ', __copyright__)
    print('Credits: ', *[f'\n      {item}' for item in __credits__])
    print('License: ', __license__)
    print('Version: ', __version__)
    print('Maintainer: ', __maintainer__)
    print('Status: ', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
