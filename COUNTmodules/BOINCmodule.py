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
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'

import logging
import shlex
import shutil
import subprocess
import sys

from COUNTmodules import __version__, __status__

# LOGGER = logging.getLogger('count-tasks')

boinccmd = shutil.which("boinccmd")
if not boinccmd:
    print('Package [boinccmd] executable not found. Install for...\n'
          'Linux: sudo apt-get install boinc-client boinc-manager\n'
          'Win: see https://boinc.berkeley.edu/wiki/Installing_BOINC\n'
          'Exiting...')
    # LOGGER.debug('boinccmd path: %s', boinccmd)
    sys.exit(1)

try:
    boinccmd = shutil.which("boinccmd")
except OSError as e:
    print('Package [boinccmd] executable not found. Install for...\n'
          'Linux: sudo apt-get install boinc-client boinc-manager\n'
          'Win: see https://boinc.berkeley.edu/wiki/Installing_BOINC\n'
          'Exiting...')
    print(e)
    sys.exit(1)


class BoincCommand:
    """Execute boinc-client commands and parse data."""

    def __init__(self):
        self.boinc = boinccmd
        self.einstein = "http://einstein.phys.uwm.edu/"
        self.milkyway = "http://milkyway.cs.rpi.edu_milkyway/"
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
                        'elapsed time', 'completed time', 'reported time')

    def run(self, command: str):
        """
        Format command for system execution of boinc-client action.

        :param command: In use: 'suspend', 'resume', 'read_cc_config'.
        :return: Change in boinc-client action.
        """
        # Project commands require the Project URL, others commands don't
        if command in self.projectcmd:
            cmd_str = f'{self.boinc} --project {self.einstein} {command}'
            subprocess.check_output(shlex.split(cmd_str), shell=False)
        elif command == 'read_cc_config':
            cmd_str = f'{self.boinc} --{command}'
            subprocess.check_output(shlex.split(cmd_str), shell=False)
        else:
            print(f'Unrecognized command: {command}')
        # LOGGER.debug('bnccmd parameter: %s', command)

    def tasks(self, tag: str = None) -> tuple:
        """
        Get current boinc-client tasks, parse task data.

        :param tag: Used: 'name', 'state', 'scheduler
                    state', 'fraction done', 'active_task_state'
        :return: All tasks or select task data, as tuple.
        """

        if tag in self.tasktags:
            cmd_str = f'{self.boinc} --get_tasks'
            tag_str = f'{" " * 3}{tag}: '
            output = subprocess.check_output(shlex.split(cmd_str),
                                             shell=False).decode().split('\n')
            data = []
            # Need only data specified by the task's tag.
            for i in output:
                if i.__contains__(tag_str):
                    i = i.replace(tag_str, '')
                    data.append(i)
            return tuple(data)
        elif tag is None:
            cmd_str = f'{self.boinc} --get_tasks'
            output = subprocess.check_output(shlex.split(cmd_str),
                                             shell=False).decode().split('\n')
            return tuple(output)
        else:
            print(f'Unrecognized data tag: {tag}')
        # LOGGER.debug('task parameters: %s', tag)

    def reported(self, tag: str = None) -> list:
        """
        Get reported boinc-client tasks, parse reported data.

        :param tag: Used: 'task' returns reported task names.
                          'elapsed time' returns task times, sec.000000.
        :return: All reported or current task data, as list.
        """

        if tag in self.oldtags:
            cmd_str = f'{self.boinc} --get_old_tasks'
            output = subprocess.check_output(shlex.split(cmd_str),
                                             shell=False).decode().split('\n')
            if tag == 'task':
                tag_str = 'task '
            else:
                tag_str = f'{" " * 3}{tag}: '
            data = []
            # Need only data specified by the task's tag.
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
        elif tag is None:
            cmd_str = f'{self.boinc} --get_old_tasks'
            output = subprocess.check_output(shlex.split(cmd_str),
                                             shell=False).decode().split('\n')
            return output
        else:
            print(f'Unrecognized data tag: {tag}')
        # LOGGER.debug('reported task parameters: %s', tag)


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
