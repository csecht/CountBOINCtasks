#!/usr/bin/env python3
"""
Executes BOINC commands and parsing task data through boinccmd.
Not all boinc-client commands are supported.
Functions:
set_boinc_path() - Return OS-specific path for BOINC's boinccmd binary.
run_boinc() - Execute a boinc-client command line; returns output.
get_version() - Get version number of boinc client; return list of one.
check_boinc() - Check whether BOINC client is running; exit if not.
get_reported() - Get data for reported boinc-client tasks.
get_tasks() - Get data for current boinc-client tasks.
get_runningtasks() - Get names of running boinc-client tasks for a
    specified app.
project_url() - Return dictionary of BOINC project NAMES and server urls.
get_project_url() - Return current local host boinc-client Project URLs.
project_action() - Execute a boinc-client action for a specified Project.
no_new_tasks() - Get Project status for "Don't request more work".

    Copyright (C) 2020-2021  C. Echt

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see https://www.gnu.org/licenses/.
"""
__author__ = 'cecht, BOINC ID: 990821'
__copyright__ = 'Copyright (C) 2020-2021 C. Echt'
__credits__ = ['Inspired by rickslab-gpu-utils',
               'Keith Myers - Testing, debug']
__license__ = 'GNU General Public License'
__module_name__ = 'boinc_commands.py'
__module_ver__ = '0.5.5'
__dev_environment__ = "Python 3.8 - 3.9"
__project_url__ = 'https://github.com/csecht/CountBOINCtasks'
__maintainer__ = 'cecht'
__status__ = 'Development Status :: 4 - Beta'

import shlex
import sys
from pathlib import Path
from subprocess import Popen, PIPE, STDOUT, CalledProcessError

from COUNTmodules import utils

CFGFILE = Path('countCFG.txt').resolve()

# Tuples that may be used in various functions:
TASK_TAGS = ('name', 'WU name', 'project URL', 'received',
             'report deadline', 'ready to report', 'state',
             'scheduler state', 'active_task_state',
             'app version num', 'resources', 'final CPU time',
             'final elapsed time', 'final elapsed time',
             'exit status', 'signal', 'estimated CPU time remaining',
             'slot', 'PID', 'current CPU time',
             'CPU time at time_now checkpoint', 'fraction done',
             'swap size', 'working set size', 'master URL'
             )

PROJECT_CMD = ('reset', 'detach', 'update', 'suspend', 'resume',
              'nomorework', 'allowmorework', 'detach_when_done',
              'dont_detach_when_done'
               )

# REPORTED_TAGS = ('task', 'project URL', 'app name', 'exit status',
#                 'elapsed time', 'completed time', 'get_reported time')
#
# GETTASKS_TAGS = ('name', 'state', 'scheduler state',  'fraction done',
#                'active_task_state')


def set_boincpath() -> str:
    """
    Define an OS-specific path for BOINC's boinccmd executable.

    :return: Correct path string for executing boinccmd commands;
        exit if not correct.
    """
    # Need to first check for custom path in the configuration file.
    # Do split to remove the "custom_path" tag, then join to restore the
    #   path with any spaces it might have.
    if Path.is_file(CFGFILE):
        cfg = Path('countCFG.txt').read_text()
        for line in cfg.splitlines():
            if '#' not in line and 'custom_path' in line:
                parts = line.split()
                del parts[0]
                custom_path = " ".join(parts)

                return custom_path

    # Need to accommodate win32 and win64? so slice [:3] for all platforms.
    #   Only win, lin, and dar values are accommodated here.
    my_os = sys.platform[:3]

    win_path = Path('/Program Files/BOINC/boinccmd.exe')
    lin_path = Path('/usr/bin/boinccmd')
    dar_path = Path.home() / 'Library' / 'Application Support' / 'BOINC' / 'boinccmd'
    # Note: On macOS, the Terminal command line would be entered as:
    # /Users/youtheuser/Library/Application\ Support/BOINC/boinccmd

    default_path = {
        'win': win_path,
        'lin': lin_path,
        'dar': dar_path
    }

    if my_os in default_path:

        # Need to exit program if boinccmd not in default path.
        if not Path.is_file(default_path[my_os]):
            if getattr(sys, 'frozen', False):
                # Exit PyInstaller standalone app here.
                utils.boinccmd_not_found(f'{default_path[my_os]}')

            badpath_msg = (
                '\nThe application boinccmd is not in its expected default path: '
                f'{default_path[my_os]}\n'
                'You should enter your custom path for boinccmd in the'
                " the current folder's configuration file, countCFG.txt.")

            sys.exit(badpath_msg)

        else:
            boinccmd = f'"{default_path[my_os]}"'

        return boinccmd

    print(f"Platform <{my_os}> is not recognized.\n"
          "Expecting win (Win32 or Win64), lin (Linux) or dar (Darwin =>Mac OS).")
    sys.exit(1)


def run_boinc(cmd_str: str) -> list:
    """
    Execute a boinc-client command line.

    :param cmd_str: A boinccmd action, command with arguments.
    :return: Data from a boinc-client command specified in cmd_str.
    """
    # source: https://stackoverflow.com/questions/33560364/
    if sys.platform[:3] == 'win':
        cmd = cmd_str
    else:
        cmd = shlex.split(cmd_str)

    try:
        with Popen(cmd, stdout=PIPE, stderr=STDOUT, text=True) as output:
            text = output.communicate()[0].split('\n')

        # When boinc-client is running, the specified cmd option from a get_ method
        #   will fill the first element of the text list with its output. When not
        #   running, boinccmd stderr will fill the first list element.
        #   Is stderr "can't connect to local host" exclusive to BOINC not running?
        if "can't connect to local host" in text:
            print(f"\nOOPS! There is a boinccmd error: {text[0]}\n"
                  f"The BOINC client associated with {cmd[0]} is not running.\n"
                  "You need to quit now and get BOINC running.")

            # If boinc not running, then text will be a null list.
            return text

        return text

    # This exception will only be raised by bad code calling one of the get_ methods.
    except CalledProcessError as cpe:
        msg = ('If the boinccmd usage message is displayed, then'
               ' boinccmd has a bad command argument.')
        print(f'\n{msg}\n{cpe}')
        # NOTE: exit works in count-tasks, not in gcount-tasks.
        sys.exit(1)


def get_version(cmd=' --client_version') -> list:
    """
    Get version number of the boinc client.

    :param cmd: The boinc command to get the client version.
    :return: version info, as a list of one string.
    """

    # Note: run_boinc() always returns a list.
    output = run_boinc(set_boincpath() + cmd)

    return output


def check_boinc():
    """
    Check whether BOINC client is running; exit if not.
    """

    # Note: Any BC boinccmd will return this string (as a list)
    #   if boinc-client is not running; use get_version() b/c it is short.
    if "can't connect to local host" in get_version():
        print('BOINC ERROR: BOINC commands cannot be executed.\n'
              'Is the BOINC client running?   Exiting now...')
        sys.exit(1)


def get_reported(tag: str, cmd=' --get_old_tasks') -> list:
    """
    Get data from reported boinc-client tasks.

    :param tag: e.g., 'task' returns reported task names.
                'elapsed time' returns final task times, sec.000000.
                Use 'all' to get full output from cmd
    :param cmd: The boinccmd command for tasks reported to boinc server.
    :return: List of specified data parsed from cmd.
    """

    output = run_boinc(set_boincpath() + cmd)
    if tag == 'all':
        return output

    # Need only data from tagged lines of boinccmd output.
    data = ['invalid_boinc_command']

    if tag == 'elapsed time':
        tag_str = f'{" " * 3}{tag}: '
        data = [line.replace(tag_str, '') for line in output if tag in line]
        data = [float(e_time.replace(' sec', '')) for e_time in data]
        return data

    if tag == 'task':
        tag_str = 'task '
        data = [line.replace(tag_str, '') for line in output if tag in line]
        data = [name.rstrip(':') for name in data]
        return data

    print(f'Unrecognized data tag: {tag}')
    return data


def get_tasks(tag: str, cmd=' --get_tasks') -> list:
    """
    Get data from current boinc-client tasks.

    :param tag: Examples: 'name', 'state', 'scheduler
                state', 'fraction done', 'active_task_state'
                Use 'all' to get full output from *cmd*.
    :param cmd: The boinccmd command to get queued tasks information.
    :return: List of tagged data parsed from cmd output.
    """

    output = run_boinc(set_boincpath() + cmd)

    if tag == 'all':
        return output

    data = ['stub_boinc_data']
    tag_str = f'{" " * 3}{tag}: '  # boinccmd output format for a data tag.

    # if tag in taskXDFtags:  # Not currently used by count_now-tasks.
    if tag in TASK_TAGS:
        data = [line.replace(tag_str, '') for line in output if tag_str in line]
        return data

    print(f'Unrecognized data tag: {tag}')
    return data


def get_runningtasks(tag: str, app_type: str,
                     cmd=' --get_simple_gui_info') -> list:
    """
    Get names of running boinc-client tasks of the specified app.

    :param tag: boinccmd output line tag, e.g., 'name', 'WU name'.
                Use 'all' to get full output from cmd
    :param app_type: The app type present in all target task names,
                    e.g. O3AS, LATeah, etc.
    :param cmd: The boinccmd command to get task information.
    :return: List of tagged data parsed from cmd. output.
    """

    # NOTE: cmd=' --get_tasks' will also work, but
    #   get_simple_gui_info lists only active tasks.
    output = run_boinc(set_boincpath() + cmd)

    if tag == 'all':
        return output

    tag_str = f'{" " * 3}{tag}: '  # boinccmd output format for a tag line of data.
    task_name = None
    data = []

    # Need to determine whether a task's task state line following its name line
    #    specifies that it is a running task (active_task_state: EXECUTING).
    # Each loop, need to clear task name to ensure target task name is paired
    #    with its active state and not that of a prior non-EXECUTING task.
    for line in output:
        if app_type in line and tag_str in line:
            task_name = line.replace(tag_str, '')
            continue

        if task_name is not None and 'EXECUTING' in line:
            data.append(task_name)
            task_name = None

    return data


def project_url() -> dict:
    """Dictionary of BOINC project NAMES and server urls
    """
    return {
        'AMICABLE': 'https://sech.me/boinc/Amicable/',
        'ASTEROID': 'http://asteroidsathome.net/boinc/',
        'TACC': 'https://boinc.tacc.utexas.edu/',
        'CITIZEN': 'https://csgrid.org/csg/',
        'CLIMATE': 'https://www.cpdn.org/',
        'COLLATZ': 'https://boinc.thesonntags.com/collatz/',
        'COSMOL': 'http://www.cosmologyathome.org/',
        'EINSTEIN': 'http://einstein.phys.uwm.edu/',
        'GERASIM': 'http://gerasim.boinc.ru/',
        'GPUGRID': 'https://www.gpugrid.net/',
        'IBERCIVIS': 'https://boinc.ibercivis.es/ibercivis/',
        'ITHENA': 'https://root.ithena.net/usr/',
        'LHC': 'https://lhcathome.cern.ch/lhcathome/',
        'MILKYWAY': 'http://milkyway.cs.rpi.edu/milkyway/',
        'MIND': 'https://mindmodeling.org/',
        'MINECRAFT': 'https://minecraftathome.com/minecrafthome/',
        'MLC': 'https://www.mlcathome.org/mlcathome/',
        'MOO': 'http://moowrap.net/',
        'NANOHUB': 'https://boinc.nanohub.org/nanoHUB_at_home/',
        'NFS': 'https://escatter11.fullerton.edu/nfs/',
        'NUMBER': 'https://numberfields.asu.edu/NumberFields/',
        'ODLK': 'https://boinc.progger.info/odlk/',
        'ODLK1': 'https://boinc.multi-pool.info/latinsquares/',
        'PRIME': 'http://www.primegrid.com/',
        'QUCHEM': 'https://quchempedia.univ-angers.fr/athome/',
        'RADIOACT': 'http://radioactiveathome.org/boinc/',
        'RAKE': 'https://rake.boincfast.ru/rakesearch/',
        'RNA': 'http://www.rnaworld.de/rnaworld/',
        'ROSETTA': 'https://boinc.bakerlab.org/rosetta/',
        'SRBASE': 'http://srbase.my-firewall.org/sr5/',
        'UNIVERSE': 'https://universeathome.pl/universe/',
        'WOLRD': 'https://universeathome.pl/universe/',
        'YOYO': 'http://www.rechenkraft.net/yoyo/'
    }


def get_project_url(tag='master URL', cmd=' --get_project_status') -> list:
    """
    Get all current local host boinc-client Project URLs.

    :param tag: Only need the name of each Project's boinc server URL.
    :param cmd: The boinccmd command to get Project information.
    :return: List of tagged data parsed from cmd output..
    """

    output = run_boinc(set_boincpath() + cmd)

    data = ['stub_boinc_data']
    tag_str = f'{" " * 3}{tag}: '  # boinccmd output format for a data tag.

    if tag in TASK_TAGS:
        data = [line.replace(tag_str, '') for line in output if tag in line]

        return data

    print(f'Unrecognized data tag: {tag}')
    return data


def project_action(project: str, action: str):
    """
    Execute a boinc-client action for a specified Project.

    :param project: A project_url dict key for a BOINC 'PROJECT'
    :param action: Use: 'suspend', 'resume', or 'update'.
    :return: Execution of specified boinc-client action.
    """

    # Project commands require the Project URL, others commands don't
    if action in PROJECT_CMD:
        cmd_str = f'{set_boincpath()} --project {project_url()[project]} {action}'

        return run_boinc(cmd_str)

    msg = (f'Unrecognized action: {action}. Expecting one of these: '
           f'{PROJECT_CMD}')
    return msg


def no_new_tasks(cmd=' --get_project_status') -> bool:
    """
    Get Project status for "Don't request more work".

    :param cmd: The boinccmd command to get Project information.
    :return: True or False indicating status of "No new tasks"
             Project setting.
    """

    output = run_boinc(set_boincpath() + cmd)

    tag_str = f'{" " * 3}don\'t request more work: '
    nnw = [line.replace(tag_str, '') for line in output if tag_str in line]

    if 'yes' in nnw:
        return True

    return False


def about() -> None:
    """
    Print basic information about this module.
    """
    print(__doc__)
    print(f'{"Author:".ljust(11)}', __author__)
    print(f'{"Copyright:".ljust(11)}', __copyright__)
    print(f'{"License:".ljust(11)}', __license__)
    print(f'{"Module:".ljust(11)}', __module_name__)
    print(f'{"Module ver.:".ljust(11)}', __module_ver__)
    print(f'{"Dev Env:".ljust(11)}', __dev_environment__)
    print(f'{"URL:".ljust(11)}', __project_url__)
    print(f'{"Maintainer:".ljust(11)}', __maintainer__)
    print(f'{"Status:".ljust(11)}', __status__)
    sys.exit(0)


if __name__ == '__main__':
    about()
