# -*- coding: utf-8 -*-
#
# @Author: CPS
# @email: 373704015@qq.com
# @Date: 2026-03-31 16:46:47.094925
# @Last Modified by: CPS
# @Last Modified time: 2026-03-31 16:46:47.094925
# @file_path "W:\CPS\IDE\SublimeText\JS_SublmieText\Data\Packages\cps-Run-Command\core\command"
# @Filename "command_shell.py"
# @Description: # shell / cmd / bash / powershell 相关
#
import platform
from typing import Any, Optional, Union

from .command_types import TRunCommand


def is_windows() -> bool:
    return platform.system().lower() == "windows"


def get_default_shell_name() -> str:
    return "cmd" if is_windows() else "bash"


def success_result(res: Any = "", code: int = 0, pid: int = 0) -> TRunCommand:
    return {
        "success": True,
        "res": res,
        "err": "",
        "code": code,
        "pid": pid,
    }


def error_result(err: Any = "", code: int = -1, pid: int = 0) -> TRunCommand:
    return {
        "success": False,
        "res": "",
        "err": str(err),
        "code": code,
        "pid": pid,
    }


def normalize_input_buffer(strBuffer: Optional[str], decode: str) -> Optional[bytes]:
    if strBuffer is None:
        return None

    if isinstance(strBuffer, bytes):
        return strBuffer

    if isinstance(strBuffer, str):
        return strBuffer.encode(decode)

    return str(strBuffer).encode(decode)


def decode_output(data: bytes, decode: str) -> str:
    if not data:
        return ""
    return data.decode(decode, errors="replace")


def normalize_pause_seconds(pause: Union[bool, int]) -> Optional[int]:
    """
    - True  => 手动暂停（返回 None）
    - int   => 延时秒数
    - False => 不暂停（返回 0）
    """
    if isinstance(pause, int) and not isinstance(pause, bool):
        return pause

    if pause is True:
        return None

    return 0


def join_command(command: list) -> str:
    return " ".join(command)
