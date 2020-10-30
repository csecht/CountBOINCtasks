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
__version__ = '0.3.5'
__maintainer__ = 'cecht'
__docformat__ = 'reStructuredText'
__status__ = 'Development Status :: 3 - Alpha'

import os
import shlex
import subprocess
import sys
from subprocess import PIPE


def bccmd_path(cmd_arg: str) -> str:
    """
    Passes boinccmd argument to the default OS path for boinc-client.

    :param cmd_arg: A boinccmd --argument or --command.
    :return: Platform-specific path for executing boinccmd command.
    """

    # Need to accommodate win32 and win36 alternatives, so [:3] for all OS.
    my_os = sys.platform[:3]
    boinc_path = {
        'win': r'\Program Files\BOINC\\boinccmd',
        'lin': '/usr/bin/boinccmd',
        'dar': r'$HOME/Library/Application\ Support/BOINC/boinccmd'
    }
    boinccmd = 'boinccmd executable stub'

    if my_os in boinc_path:
        if os.path.exists(boinc_path[my_os]):
            boinccmd = f'{boinc_path[my_os]} {cmd_arg}'
            return boinccmd
        raise OSError(f'Bad path for boinccmd: {boinc_path[my_os]}')
    if my_os not in boinc_path:
        raise KeyError(f"Platform <{my_os}> is not recognized. "
                       f"Expecting win32, win64, linux, or darwin (Mac OS).")
    return boinccmd


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

    @staticmethod
    def run_boinc(cmd_str: str):
        """
        Run a boinc-client command line for the current system platform.

        :param cmd_str: Complete boinccmd command line, with arguments.
        :return: Execution of boinc-client command specified in cmd_str.
        """
        # TODO: Add exceptions for when subprocess output is null.
        output = ['boinccmd_results_stub']
        if sys.platform[:3] == 'win':
            output = subprocess.run(cmd_str,
                                    stdout=PIPE,
                                    encoding='utf8',
                                    check=True).stdout.split('\n')
        # Use this for Windows, Python 3.8 and 3.9.
        # if sys.platform[:3] == 'win':
        #     output = subprocess.run(cmd_str,
        #                             capture_output=True,
        #                             text=True,
        #                             check=True).stdout.split('\n')
        # Use this for Linux, Python 3.6 and up.
        if sys.platform == 'linux':
            output = subprocess.run(shlex.split(cmd_str),
                                    stdout=PIPE,
                                    encoding='utf8',
                                    check=True).stdout.split('\n')
        # Use this for Linux, Python 3.8 and up.
        # if sys.platform == 'linux':
        #     output = subprocess.run(shlex.split(cmd_str),
        #                             capture_output=True,
        #                             text=True,
        #                             check=True).stdout.split('\n')
        if sys.platform == 'darwin':
            output = subprocess.check_output(cmd_str,
                                             shell=True).decode(
                                                        'utf-8').split('\n')

        return output

    def einstein_action(self, command: str):
        """Execute a boinc-client action for Einstein@Home.

        :param command: In use: 'suspend', 'resume', 'read_cc_config'.
        :return: Change in boinc-client action.
        """
        # TODO: Generalize for any boinc Project.
        # Project commands require the Project URL, others commands don't
        boinccmd = bccmd_path('')
        cmd_str = ''
        if command in self.projectcmd:
            cmd_str = f'{boinccmd} --project {self.EINSTEIN} {command}'
        elif command == 'read_cc_config':
            cmd_str = f'{boinccmd} --{command}'
        else:
            print(f'Unrecognized command: {command}')

        return self.run_boinc(cmd_str)

    def get_tasks(self, tag: str) -> list:
        """
        Get data from current boinc-client tasks.

        :param tag: Used: 'name', 'state', 'scheduler
                    state', 'fraction done', 'active_task_state'
        :return: List of specified data from current tasks.
        """
        valid_tag = ['name', 'state', 'scheduler, state', 'fraction done',
                     'active_task_state']
        cmd_str = bccmd_path('--get_tasks')
        output = self.run_boinc(cmd_str)

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

        :param tag: 'task' returns reported task names.
                    'elapsed time' returns final task times, sec.000000.
        :return: List of specified data from reported tasks.
        """

        cmd_str = bccmd_path('--get_old_tasks')
        output = self.run_boinc(cmd_str)

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
