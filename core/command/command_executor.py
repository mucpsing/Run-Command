# -*- coding: utf-8 -*-
#
# @Author: CPS
# @email: 373704015@qq.com
# @Date: 2026-03-31 16:46:47.094925
# @Last Modified by: CPS
# @Last Modified time: 2026-03-31 16:46:47.094925
# @file_path "W:\CPS\IDE\SublimeText\JS_SublmieText\Data\Packages\cps-Run-Command\core\command"
# @Filename "command_executor.py"
# @Description: 核心执行器（同步 / 异步 / 实时流）
#
import os
import shutil
from typing import List, Optional, Union

from .command_utils import is_windows, get_default_shell_name, normalize_pause_seconds


def get_shell(shell_type: str = None) -> str:
    """
    - param shell_type : cmd | bash | powershell
    """
    has_bash = shutil.which("bash") or shutil.which("bash.exe")
    has_cmd = shutil.which("cmd")
    has_shell_type = shutil.which(shell_type) if shell_type else None

    return has_shell_type or has_cmd or has_bash or get_default_shell_name()


def resolve_shell(shell_type: Optional[str] = None) -> str:
    if shell_type:
        return get_shell(shell_type)
    return get_shell(get_default_shell_name())


def shell_name(shell_path: str) -> str:
    return os.path.basename(shell_path).lower()


def build_windows_cmd_start_command(command: str, pause: Union[bool, int], shell_path: str) -> str:
    command_head = f'start "" {shell_path} /c "'
    command_body = command

    if isinstance(pause, int) and not isinstance(pause, bool):
        command_end = f' & timeout /t {pause}"'
    elif pause is True:
        command_end = ' & pause"'
    else:
        command_end = '"'

    return command_head + command_body + command_end


def build_bash_new_console_command(command: str, pause: Union[bool, int], shell_path: str) -> List[str]:
    wait_seconds = normalize_pause_seconds(pause)

    if wait_seconds is None:
        wait_seconds = 999999

    if wait_seconds == 0:
        command_end = "; exit"
    else:
        command_end = f'; echo; echo "Window Close In {wait_seconds} Sec"; ' f"read -t {wait_seconds} -n 1 -s -r; exit"

    return [shell_path, "-c", command + command_end]


def build_capture_command(command: str, shell_type: Optional[str] = None) -> List[str]:
    shell_path = resolve_shell(shell_type)
    current_shell_name = shell_name(shell_path)

    if "cmd" in current_shell_name:
        return [shell_path, "/c", command]

    if "bash" in current_shell_name:
        return [shell_path, "-c", command]

    if "powershell" in current_shell_name:
        return [shell_path, "-Command", command]

    return [shell_path, "/c", command]
