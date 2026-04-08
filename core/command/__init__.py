from typing import *
from .command_types import TRunCommand, TStreamCallback
from .command_utils import error_result
from .command_executor import (
    open_new_console_list_command,
    open_new_console_string_command,
    run_capture_list_command,
    run_capture_string_command,
    run_stream_list_command,
    run_stream_string_command,
    run_in_thread,
)


COMMANDS = {
    "node": ["node", "-v"],
    "npm": ["npm", "-v"],
    "yarn": ["yarn", "-v"],
    "ts-node": ["ts-node", "-v"],
    "tsc": ["tsc", "--version"],
}


def check_command(target: str) -> bool:
    if target not in COMMANDS:
        return False

    result = run_command(COMMANDS[target])

    if not result.get("success"):
        return False

    res_text = str(result.get("res", "")).strip()
    print(res_text)
    return bool(res_text)


# =========================================================
# 对外入口（保留原签名）
# =========================================================


def run_command(
    command: list,
    strBuffer: str = Optional[str],
    shell: bool = False,
    decode: str = "utf-8",
    cwd=Optional[str],
    pause: Union[bool, int] = False,
):
    """
    list 命令入口
    """
    try:
        if shell:
            return open_new_console_list_command(
                command=command,
                cwd=cwd,
                pause=pause,
            )

        return run_capture_list_command(
            command=command,
            strBuffer=strBuffer,
            decode=decode,
            cwd=cwd,
        )

    except Exception as err:
        print("run_command() 运行出错:", command)
        return error_result(err)


def run_command_new(
    command: str,
    strBuffer: str = None,
    shell: bool = False,
    shell_type: str = "cmd",
    decode: str = "utf-8",
    cwd=None,
    pause: Union[bool, int] = False,
):
    """
    string 命令入口
    """
    try:
        if shell:
            return open_new_console_string_command(
                command=command,
                shell_type=shell_type,
                cwd=cwd,
                pause=pause,
            )

        return run_capture_string_command(
            command=command,
            strBuffer=strBuffer,
            decode=decode,
            cwd=cwd,
            shell_type=shell_type,
        )

    except Exception as err:
        print("run_command_new() 运行出错:", command)
        return error_result(err)


# =========================================================
# 实时流版本（新增）
# =========================================================


def run_command_stream(
    command: list,
    strBuffer: str = None,
    decode: str = "utf-8",
    cwd=None,
    callback: TStreamCallback = None,
) -> TRunCommand:
    """
    list 命令实时输出
    """
    try:
        return run_stream_list_command(
            command=command,
            strBuffer=strBuffer,
            decode=decode,
            cwd=cwd,
            callback=callback,
        )
    except Exception as err:
        print("run_command_stream() 运行出错:", command)
        return error_result(err)


def run_command_new_stream(
    command: str,
    strBuffer: str = None,
    shell_type: str = "cmd",
    decode: str = "utf-8",
    cwd=None,
    callback: TStreamCallback = None,
) -> TRunCommand:
    """
    string 命令实时输出
    """
    try:
        return run_stream_string_command(
            command=command,
            strBuffer=strBuffer,
            decode=decode,
            cwd=cwd,
            shell_type=shell_type,
            callback=callback,
        )
    except Exception as err:
        print("run_command_new_stream() 运行出错:", command)
        return error_result(err)


# =========================================================
# 异步线程启动（新增）
# =========================================================


def run_command_new_async(
    command: str,
    strBuffer: str = None,
    shell: bool = False,
    shell_type: str = "cmd",
    decode: str = "utf-8",
    cwd=None,
    pause: Union[bool, int] = False,
):
    """
    异步线程执行 run_command_new
    """
    return run_in_thread(
        target=run_command_new,
        args=(command, strBuffer, shell, shell_type, decode, cwd, pause),
    )


def run_command_new_stream_async(
    command: str,
    strBuffer: str = None,
    shell_type: str = "cmd",
    decode: str = "utf-8",
    cwd=None,
    callback: TStreamCallback = None,
):
    """
    异步线程 + 实时流
    """
    return run_in_thread(
        target=run_command_new_stream,
        kwargs={
            "command": command,
            "strBuffer": strBuffer,
            "shell_type": shell_type,
            "decode": decode,
            "cwd": cwd,
            "callback": callback,
        },
    )
