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
__program_name__ = 'count-tasks.py'
__version__ = '0.2.1'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ = 'Development Status :: 3 - Alpha'

import os
import shlex
import subprocess
import sys


class BoincCommand:
    """
    Execute boinc-client commands and parse data.
    """

    EINSTEIN = "http://einstein.phys.uwm.edu/"
    MILKYWAY = "http://milkyway.cs.rpi.edu_milkyway/"

    def __init__(self):
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

    def bccmd_path(self) -> str:
        boinccmd = ''
        if sys.platform[:3] == 'win':
            boinccmd = "\Program Files\BOINC\\boinccmd"
            return boinccmd
        if sys.platform == 'linux':
            boinccmd = "/usr/bin/boinccmd"
            return boinccmd
        if sys.platform == 'darwin':
            boinccmd = '$HOME/Library/Application\ Support/BOINC/boinccmd'
            return boinccmd

        print(
            '[boinccmd] executable not found in its expected default path.')
        return boinccmd

    # def run(self, command: str):
    #     """
    #     Format command for system execution of boinc-client action.
    #
    #     :param command: In use: 'suspend', 'resume', 'read_cc_config'.
    #     :return: Change in boinc-client action.
    #     """
    #
    #     # Project commands require the Project URL, others commands don't
    #     if command in self.projectcmd:
    #         bcmd_path = os.path.join(self.boinccmd)
    #         subprocess.run(f'{bcmd_path} --project {self.EINSTEIN} '
    #                        f'{command}', capture_output=True, text=True,
    #                        shell=True).stdout.split('\n')
    #     elif command == 'read_cc_config':
    #         command_fmt = f'--{command}'
    #         bcmd_path = os.path.join(self.boinccmd)
    #         subprocess.run(f'{bcmd_path} {command_fmt}',
    #                        capture_output=True, text=True, shell=True)
    #     else:
    #         print(f'Unrecognized command: {command}')

    def get_tasks(self, tag: str) -> list:
        """
        Get data from current boinc-client tasks.

        :param tag: Used: 'name', 'state', 'scheduler
                    state', 'fraction done', 'active_task_state'
        :return: List of specified data from current tasks.
        """
        valid_tag = ['name', 'state', 'scheduler, state', 'fraction done',
                     'active_task_state']
        output = []
        cmd_str = self.bccmd_path() + ' --get_tasks'
        if sys.platform == 'linux':
            output = subprocess.run(shlex.split(cmd_str),
                                    capture_output=True,
                                    text=True).stdout.split('\n')
        if sys.platform[:3] == 'win':
            output = subprocess.run(cmd_str,
                                    capture_output=True,
                                    text=True).stdout.split('\n')

        data = []
        tag_str = f'{" " * 3}{tag}: '  # boinccmd stdout format for a tag
        if tag in valid_tag:
            data = [dat.replace(tag_str, '') for dat in output if tag in dat]
            return data
        print(f'Unrecognized data tag: {tag}')
        return data

    def get_reported(self, tag: str) -> list:
        """
        Get data from reported boinc-client tasks.

        :param tag: Used: 'task' returns reported task names.
                          'elapsed time' returns task times, sec.000000.
        :return: List of specified data from reported tasks.
        """

        cmd_str = self.bccmd_path() + ' --get_old_tasks'
        output = []
        if sys.platform == 'linux':
            output = subprocess.run(shlex.split(cmd_str),
                                    capture_output=True,
                                    text=True).stdout.split('\n')
        if sys.platform[:3] == 'win':
            output = subprocess.run(cmd_str,
                                    capture_output=True,
                                    text=True).stdout.split('\n')
        # if sys.platform == 'darwin':
        #     output = subprocess.run(shlex.split(cmd_str)cmd_str,
        #                             capture_output=True,
        #                             text=True).stdout.split('\n')

        data = []
        if tag == 'elapsed time':
            tag_str = f'{" " * 3}{tag}: '
            data = [dat.replace(tag_str, '') for dat in output if tag in dat]
            data = [float(seconds.replace(' sec', '')) for seconds in data]
            return data
        if tag == 'task':
            tag_str = 'task '
            data = [dat.replace(tag_str, '') for dat in output if tag in dat]
            data = [name.rstrip(':') for name in data]
            return data

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
