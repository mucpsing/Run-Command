import sys
import subprocess
from subprocess import Popen, PIPE
import platform
import os

from typing import *

COMMANDS = {
    "node": ["node", "-v"],
    "npm": ["npm", "-v"],
    "yarn": ["yarn", "-v"],
    "ts-node": ["ts-node", "-v"],
    "tsc": ["tsc", "--version"],
}


def check_command(target: str) -> bool:
    res = False
    global COMMANDS
    if target in COMMANDS.keys():
        res = run_command(COMMANDS[target]).strip()
        print(res)
    return True if res else False


class TRun_command(TypedDict):
    success: bool
    res: Any
    err: Any


def get_shell(shell_type: str = None) -> str:
    """
    - param shell_type :{str} cmd|bash
    """
    import shutil

    has_bash = shutil.which("bash") or shutil.which("bash.exe")
    has_cmd = shutil.which("cmd")
    has_shell_type = shutil.which(shell_type)

    return has_shell_type or has_cmd or has_bash


def run_command(
    command: list,
    strBuffer: str = Optional[str],
    shell: bool = False,
    decode: str = "utf-8",
    cwd=Optional[str],
    pause: Union[bool, int] = False,
):
    """
    @Description {description}

    - param command   :{list} 通过列表将需要输入的shell命令传入
    - param strBuffer :{str}  需要传输的数据
    - param shell     :{bool} 是否开启一个独立的shell执行指令
    - param decode    :{str}  对返回的结果指定编码方式
    - param pause     :{bool} 是否暂停，如果输入数字，则是延时关闭
    - panam cwd       :{str}  指定工作目录

    @example
    ```python
    command = ['node', '-v']

    # 简单单向指令
    run_command(command)

    # 复杂交互指令
    res = run_command(command, decode='gb2312', shell=True, pause=True)
    if res['success']:
        print(res['res'])
    else:
        print(res['err'])
    ```
    @returns `{str}` {description}

    """

    os_type = platform.system().lower()
    if os_type == "windows":
        use_shell = "cmd"
    else:
        use_shell = "bash"

    # 指定工作目录
    if cwd:
        os.chdir(cwd)

    try:
        # run with inside
        if shell:
            command_head = f'start {use_shell} /c "'
            command_body = " ".join(command)
            command_end = ""

            if isinstance(pause, bool):
                command_end = ' & pause"' if pause else '"'
            elif isinstance(pause, int):
                command_end = f' & timeout /t {pause}"'

            _command = command_head + command_body + command_end
            Popen(_command, shell=True)
            # return True
            return {"success": True}

        # run with outside
        child_process = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)

        # 过来一遍 strBuffer
        if strBuffer != None:
            if isinstance(strBuffer, str):
                strBuffer = strBuffer.encode(decode)

        # 执行 command
        stdout, stderr = child_process.communicate(input=strBuffer, timeout=10000)

        if stdout:
            if decode:
                return {"res": stdout.decode(decode), "success": True}
            return {"res": stdout, "success": True}

        if stderr:
            print("run_command() 命令完成:", stderr)
            return {"res": str(stderr), "success": True}

        return {"success": False, "err": "nothing change"}

    except Exception as err:
        print("run_command() 运行出错:", command)
        return {"err": err, "success": False}


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
    @Description {description}

    - param command   :{str}  采用字符串，确保命令完整
    - param strBuffer :{str}  需要传输的数据
    - param shell     :{bool} 是否开启一个独立的shell执行指令
    - param shell_type :{str}  使用什么类型的shell，默认cmd，
    - param pause     :{bool} 是否在新的窗口执行指令，如果提供int类型，则在int秒后关闭窗口
    - param pause     :{bool} 是否在新的窗口执行指令，如果提供int类型，则在int秒后关闭窗口
    - panam cwd       :{str}  指定工作目录

    @example
    ```python
    command = ['node', '-v']

    # 简单单向指令
    run_command(command)

    # 复杂交互指令
    res = run_command(command, decode='gb2312', shell=True, pause=True)
    if res['success']:
        print(res['res'])
    else:
        print(res['err'])
    ```
    @returns `{str}` {description}

    """
    # 指定工作目录
    is_windows = platform.system() == "Windows"
    if not is_windows:
        return {"success": False, "msg": "插件没有兼容非window环境"}

    wait_seconds = 6
    if cwd:
        os.chdir(cwd)

    use_shell = get_shell(shell_type)

    if "cmd" in use_shell and shell:
        command_head = f'start {use_shell} /c "'
        command_body = command
        command_end = ' & pause"' if pause else '"'
        if isinstance(pause, int):
            command_end = f' & timeout /t {pause}"'

        _command = command_head + command_body + command_end
        Popen(_command, shell=True)
        return {"success": True}

    if "bash" in use_shell and shell:
        wait_seconds = pause if pause and isinstance(pause, int) else 3
        command_head = [use_shell, "-c"]
        command_body = command
        command_end = (
            f"; echo; echo Window Close In {wait_seconds} Ses; read -t {wait_seconds} -n 1 -s -r; exit"  # 超时功能
        )

        # run out side 交互均有外部控制
        _command = command_head + [command_body + command_end]
        Popen(_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
        return {"success": True}

    try:
        # run with inside
        child_process = Popen(command, stdout=PIPE, stdin=PIPE, stderr=PIPE, shell=True)

        # 过来一遍 strBuffer
        if strBuffer != None:
            if isinstance(strBuffer, str):
                strBuffer = strBuffer.encode(decode)

        # 执行 command
        stdout, stderr = child_process.communicate(input=strBuffer, timeout=10000)

        if stdout:
            if decode:
                return {"res": stdout.decode(decode), "success": True}
            return {"res": stdout, "success": True}

        if stderr:
            print("run_command() 命令完成:", stderr)
            return {"res": str(stderr), "success": True}

        return {"success": False, "err": "nothing change"}

    except Exception as err:
        print("run_command() 运行出错:", command)
        return {"err": err, "success": False}


if __name__ == "__main__":
    use_shell = get_shell("bash")
    command = ["git", "--ver123123sion"]
    wait_seconds = 3
    command_head = [use_shell, "-c"]
    command_body = " ".join(command)
    command_end = f"; echo; echo Window Close In {wait_seconds} Ses; read -t {wait_seconds} -n 1 -s -r; exit"

    # run out side 交互均有外部控制
    _command = command_head + [command_body + command_end]
    print("_command: ", _command)
    Popen(_command, creationflags=subprocess.CREATE_NEW_CONSOLE)
