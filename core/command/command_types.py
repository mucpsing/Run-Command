# -*- coding: utf-8 -*-
#
# @Author: CPS
# @email: 373704015@qq.com
# @Date: 2026-03-31 16:46:47.094925
# @Last Modified by: CPS
# @Last Modified time: 2026-03-31 16:46:47.094925
# @file_path "W:\CPS\IDE\SublimeText\JS_SublmieText\Data\Packages\cps-Run-Command\core\command"
# @Filename "command_types.py"
# @Description: TypedDict / 类型定义
#
from typing import Any, TypedDict, Optional, Callable


class TRunCommand(TypedDict, total=False):
    success: bool
    res: Any
    err: Any
    code: int
    pid: int


# 实时输出回调
# line: 当前输出行
# source: "stdout" | "stderr"
TStreamCallback = Optional[Callable[[str, str], None]]
