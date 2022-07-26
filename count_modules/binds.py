#!/usr/bin/env python3
"""
Functions to set tkinter mouse click and keyboard bindings.
Functions:
    click() - Mouse button bindings for a named object.
    keyboard() - Bind a key to a function for the specified toplevel.
"""
# Copyright (C) 2021 C. Echt under GNU General Public License'

import sys
from tkinter import constants, Menu

from count_modules import files

MY_OS = sys.platform[:3]


def click(click_type, click_widget) -> None:
    """
    Mouse button bindings for the named tk widget.
    Creates pop-up menu of commands for the clicked object.
    Example: from count_modules import binds
             binds.click('right', mywidget, root)

    :param click_type: Example mouse button or button modifiers;
        left', 'right', 'shift', 'ctrl', 'shiftctrl', etc.
        'right': popup menu of text edit and window commands.
    :param click_widget: Name of the widget in which click commands are
        to be active.
    """

    def on_click(event, command):
        """
        Sets menu command to the selected predefined virtual event.
        Event is a unifying binding across multiple platforms.
        https://www.tcl.tk/man/tcl8.6/TkCmd/event.htm#M7
        """
        # Need to set possible Text widgets to be editable in case
        #   they are set to be readonly, tk.DISABLED.
        event.widget.event_generate(f'<<{command}>>')

    # Based on: https://stackoverflow.com/questions/57701023/
    def popup_menu(event):
        popup = Menu(None, tearoff=0, takefocus=0)

        popup.add_command(
            label='Select all',
            command=lambda: on_click(event, 'SelectAll'))
        popup.add_command(
            label='Copy',
            command=lambda: on_click(event, 'Copy'))
        popup.add_command(
            label='Paste',
            command=lambda: on_click(event, 'Paste'))
        popup.add_command(
            label='Cut',
            command=lambda: on_click(event, 'Cut'))
        popup.add(constants.SEPARATOR)
        popup.add_command(
            label='Close window',
            command=lambda: click_widget.winfo_toplevel().destroy())

        popup.tk_popup(event.x_root + 10, event.y_root + 15)

    if click_type == 'right':
        if MY_OS in 'lin, win':
            click_widget.bind('<Button-3>', popup_menu)
        elif MY_OS == 'dar':
            click_widget.bind('<Button-2>', popup_menu)


def keyboard(func: str,
             topwin,
             filepath=None,
             text=None) -> None:
    """
    Bind a key to a function for the specified Toplevel() window. Use to
    add standard keyboard actions or to provide keybinding equivalents
    for button commands used in the Toplevel() window.

    Example usage in a function that creates a mytopwin Toplevel and
    using import: 'from count_modules import binds':
        binds.keyboard('close', mytopwin)
        binds.keyboard('append', mytopwin, MYFILEPATH, txt)

    :param func: Function to execute: 'close', 'append', 'saveas'.
                 For 'close', the key is 'w' with OS-specific modifier.
                 For 'append' and 'saveas', the key is 's' with
                 OS-specific modifier.
    :param topwin: Name of tk.Toplevel() window object.
    :param filepath: A Path file object; use with *func* 'saveas' and
                     'append'.
    :param text: Text to append to *filepath*; use with *func* 'append'.
    """
    cmd_key = ''
    if MY_OS in 'lin, win':
        cmd_key = 'Control'
    elif MY_OS == 'dar':
        cmd_key = 'Command'

    if func == 'close':
        topwin.bind(
            f'<{f"{cmd_key}"}-w>',
            lambda _: topwin.winfo_toplevel().destroy())

    elif func == 'append':
        topwin.bind(
            f'<{f"{cmd_key}"}-s>',
            lambda _: files.append_txt(filepath, text, True, topwin))

    elif func == 'saveas':
        topwin.bind(
            f'<{f"{cmd_key}"}-s>',
            lambda _: files.save_as(filepath, topwin))
