import sys
import subprocess
from subprocess import Popen, PIPE
import platform
import os
import shutil

from typing import *


COMMANDS = {
    "node": ["node", "-v"],
    "npm": ["npm", "-v"],
    "yarn": ["yarn", "-v"],
    "ts-node": ["ts-node", "-v"],
    "tsc": ["tsc", "--version"],
}


class TRun_command(TypedDict, total=False):
    success: bool
    res: Any
    err: Any
    code: int


# =========================================================
# 基础工具函数（单一职责）
# =========================================================


def _is_windows() -> bool:
    return platform.system().lower() == "windows"


def _get_default_shell() -> str:
    return "cmd" if _is_windows() else "bash"


def _success_result(res: Any = "", code: int = 0) -> TRun_command:
    return {
        "success": True,
        "res": res,
        "err": "",
        "code": code,
    }


def _error_result(err: Any = "", code: int = -1) -> TRun_command:
    return {
        "success": False,
        "res": "",
        "err": err,
        "code": code,
    }


def _normalize_input_buffer(strBuffer: Optional[str], decode: str) -> Optional[bytes]:
    """
    将输入 stdin 统一转成 bytes
    """
    if strBuffer is None:
        return None

    if isinstance(strBuffer, str):
        return strBuffer.encode(decode)

    if isinstance(strBuffer, bytes):
        return strBuffer

    return str(strBuffer).encode(decode)


def _decode_output(data: bytes, decode: str) -> str:
    """
    安全解码 stdout / stderr
    """
    if not data:
        return ""
    return data.decode(decode, errors="replace")


def _normalize_pause_seconds(pause: Union[bool, int], default_seconds: int = 3) -> Optional[int]:
    """
    统一 pause 逻辑：
    - True  => 手动暂停（返回 None）
    - int   => 延时秒数
    - False => 不暂停（返回 0）
    """
    if isinstance(pause, int) and not isinstance(pause, bool):
        return pause

    if pause is True:
        return None

    return 0


def _get_creationflags_for_new_console() -> int:
    """
    Windows 新控制台标志
    """
    if _is_windows():
        return getattr(subprocess, "CREATE_NEW_CONSOLE", 0)
    return 0


def _join_command(command: List[str]) -> str:
    """
    list 命令转字符串
    """
    return " ".join(command)


# =========================================================
# shell 解析
# =========================================================


def get_shell(shell_type: str = None) -> str:
    """
    - param shell_type :{str} cmd|bash|powershell
    """
    has_bash = shutil.which("bash") or shutil.which("bash.exe")
    has_cmd = shutil.which("cmd")
    has_shell_type = shutil.which(shell_type) if shell_type else None

    return has_shell_type or has_cmd or has_bash or _get_default_shell()


def _resolve_shell(shell_type: Optional[str] = None) -> str:
    """
    统一 shell 获取
    """
    if shell_type:
        return get_shell(shell_type)
    return get_shell(_get_default_shell())


# =========================================================
# cwd / 平台校验
# =========================================================


def _validate_windows_only() -> Optional[TRun_command]:
    """
    仅 Windows 允许的逻辑入口校验
    """
    if not _is_windows():
        return _error_result("插件没有兼容非window环境")
    return None


# =========================================================
# 新窗口命令构造
# =========================================================


def _build_windows_cmd_start_command(command: str, pause: Union[bool, int], shell_path: str) -> str:
    """
    构造 Windows cmd 新窗口执行命令
    """
    command_head = f'start "" {shell_path} /c "'
    command_body = command

    if isinstance(pause, int) and not isinstance(pause, bool):
        command_end = f' & timeout /t {pause}"'
    elif pause is True:
        command_end = ' & pause"'
    else:
        command_end = '"'

    return command_head + command_body + command_end


def _build_bash_new_console_command(command: str, pause: Union[bool, int], shell_path: str) -> List[str]:
    """
    构造 bash 新窗口执行命令
    """
    wait_seconds = _normalize_pause_seconds(pause, default_seconds=3)

    if wait_seconds is None:
        # True => 近似手动等待
        wait_seconds = 999999

    if wait_seconds == 0:
        command_end = "; exit"
    else:
        command_end = f'; echo; echo "Window Close In {wait_seconds} Sec"; ' f"read -t {wait_seconds} -n 1 -s -r; exit"

    return [shell_path, "-c", command + command_end]


# =========================================================
# 新窗口执行（只负责打开，不负责捕获）
# =========================================================


def _open_new_console_windows_cmd(
    command: str, pause: Union[bool, int], cwd: Optional[str], shell_path: str
) -> TRun_command:
    _command = _build_windows_cmd_start_command(command, pause, shell_path)
    Popen(_command, shell=True, cwd=cwd)
    return _success_result()


def _open_new_console_bash(command: str, pause: Union[bool, int], cwd: Optional[str], shell_path: str) -> TRun_command:
    _command = _build_bash_new_console_command(command, pause, shell_path)
    Popen(_command, cwd=cwd, creationflags=_get_creationflags_for_new_console())
    return _success_result()


def _run_in_new_console_for_string_command(
    command: str,
    shell_type: Optional[str],
    cwd: Optional[str],
    pause: Union[bool, int],
) -> TRun_command:
    """
    字符串命令：在新窗口中执行
    """
    shell_path = _resolve_shell(shell_type)
    shell_name = os.path.basename(shell_path).lower()

    if "cmd" in shell_name:
        return _open_new_console_windows_cmd(command, pause, cwd, shell_path)

    if "bash" in shell_name:
        return _open_new_console_bash(command, pause, cwd, shell_path)

    # fallback
    return _open_new_console_windows_cmd(command, pause, cwd, shell_path)


def _run_in_new_console_for_list_command(
    command: List[str],
    cwd: Optional[str],
    pause: Union[bool, int],
) -> TRun_command:
    """
    list 命令：在新窗口中执行
    """
    command_str = _join_command(command)
    shell_path = _resolve_shell(_get_default_shell())
    shell_name = os.path.basename(shell_path).lower()

    if "cmd" in shell_name:
        return _open_new_console_windows_cmd(command_str, pause, cwd, shell_path)

    if "bash" in shell_name:
        return _open_new_console_bash(command_str, pause, cwd, shell_path)

    return _open_new_console_windows_cmd(command_str, pause, cwd, shell_path)


# =========================================================
# 当前进程执行（负责捕获 stdout/stderr）
# =========================================================


def _communicate_process(
    child_process: subprocess.Popen,
    input_data: Optional[bytes],
    decode: str,
) -> TRun_command:
    """
    统一处理 communicate 与结果返回
    """
    stdout, stderr = child_process.communicate(input=input_data, timeout=10000)

    stdout_text = _decode_output(stdout, decode)
    stderr_text = _decode_output(stderr, decode)
    code = child_process.returncode

    if code == 0:
        return _success_result(res=stdout_text, code=code)

    return _error_result(err=stderr_text or stdout_text or "command failed", code=code)


def _run_capture_list_command(
    command: List[str],
    strBuffer: Optional[str],
    decode: str,
    cwd: Optional[str],
) -> TRun_command:
    """
    当前进程执行 list 命令并捕获输出
    """
    input_data = _normalize_input_buffer(strBuffer, decode)

    child_process = Popen(
        command,
        stdout=PIPE,
        stdin=PIPE,
        stderr=PIPE,
        shell=False,
        cwd=cwd,
    )

    return _communicate_process(child_process, input_data, decode)


def _run_capture_string_command(
    command: str,
    strBuffer: Optional[str],
    decode: str,
    cwd: Optional[str],
    shell_type: Optional[str] = None,
) -> TRun_command:
    """
    当前进程执行 string 命令并捕获输出
    """
    input_data = _normalize_input_buffer(strBuffer, decode)
    shell_path = _resolve_shell(shell_type)
    shell_name = os.path.basename(shell_path).lower()

    if "cmd" in shell_name:
        popen_command = [shell_path, "/c", command]
    elif "bash" in shell_name:
        popen_command = [shell_path, "-c", command]
    elif "powershell" in shell_name:
        popen_command = [shell_path, "-Command", command]
    else:
        popen_command = [shell_path, "/c", command]

    child_process = Popen(
        popen_command,
        stdout=PIPE,
        stdin=PIPE,
        stderr=PIPE,
        shell=False,
        cwd=cwd,
    )

    return _communicate_process(child_process, input_data, decode)


# =========================================================
# 入口函数（只做参数接收与路由）
# =========================================================


def run_command(
    command: list,
    strBuffer: Optional[str] = None,
    shell: bool = False,
    decode: str = "utf-8",
    cwd: Optional[str] = None,
    pause: Union[bool, int] = False,
):
    """
    @Description
    list 形式命令入口函数

    - param command   :{list} 通过列表将需要输入的shell命令传入
    - param strBuffer :{str}  需要传输的数据
    - param shell     :{bool} 是否开启一个独立的shell执行指令
    - param decode    :{str}  对返回的结果指定编码方式
    - param pause     :{bool} 是否暂停，如果输入数字，则是延时关闭
    - panam cwd       :{str}  指定工作目录
    """
    try:
        if shell:
            return _run_in_new_console_for_list_command(
                command=command,
                cwd=cwd,
                pause=pause,
            )

        return _run_capture_list_command(
            command=command,
            strBuffer=strBuffer,
            decode=decode,
            cwd=cwd,
        )

    except Exception as err:
        print("run_command() 运行出错:", command)
        return _error_result(err)


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
    @Description
    string 形式命令入口函数

    - param command    :{str} 采用字符串，确保命令完整
    - param strBuffer  :{str} 需要传输的数据
    - param shell      :{bool} 是否开启一个独立的shell执行指令
    - param shell_type :{str} 使用什么类型的shell，默认cmd
    - param decode     :{str} 输出编码
    - param cwd        :{str} 指定工作目录
    - param pause      :{bool|int} 新窗口执行时是否暂停 / 延时关闭
    """
    try:
        windows_check = _validate_windows_only()
        if windows_check:
            return windows_check

        if shell:
            return _run_in_new_console_for_string_command(
                command=command,
                shell_type=shell_type,
                cwd=cwd,
                pause=pause,
            )

        return _run_capture_string_command(
            command=command,
            strBuffer=strBuffer,
            decode=decode,
            cwd=cwd,
            shell_type=shell_type,
        )

    except Exception as err:
        print("run_command_new() 运行出错:", command)
        return _error_result(err)


# =========================================================
# 业务函数
# =========================================================


def check_command(target: str) -> bool:
    """
    检查命令是否存在并可执行
    """
    global COMMANDS

    if target not in COMMANDS:
        return False

    result = run_command(COMMANDS[target])

    if not result.get("success"):
        return False

    res_text = str(result.get("res", "")).strip()
    print(res_text)
    return bool(res_text)


# =========================================================
# 调试入口
# =========================================================

if __name__ == "__main__":
    # 1) list 模式：捕获输出
    print(run_command(["node", "-v"]))

    # 2) string 模式：捕获输出
    print(run_command_new("git --version", shell=False, shell_type="cmd"))

    # 3) string 模式：bash 新窗口运行
    # print(run_command_new("git --version", shell=True, shell_type="bash", pause=3))

    # 4) string 模式：cmd 新窗口运行
    # print(run_command_new("echo hello world", shell=True, shell_type="cmd", pause=True))
