# -*- coding: utf-8 -*-
#
# @Author: CPS
# @email: 373704015@qq.com
# @Date:
# @Last Modified by: CPS
# @Last Modified time: 2023-02-08 15:04:01.735024
# @file_path "W:\CPS\IDE\SublimeText\JS_SublmieText\Data\Packages\cps-fileheader"
# @Filename "main.py"
# @Description: 解析配置文件，返回脚本执行列表
#

import os, configparser, json

from typing import List

FIELD_SCRIPTS_PY = "tool.poetry.scripts"
PROJECT_PATH_FILE_LIST = [".git", "readme.md", "node_modules"]


def get_project_root(
    file_path: str, max_deep: int = 100, currt_deep: int = 0, SEARCH_LIST=None
) -> str:
    file_folder = os.path.dirname(file_path)

    for each_file in os.listdir(file_folder):
        if each_file in PROJECT_PATH_FILE_LIST:
            return file_folder

    currt_deep += 1
    if currt_deep >= max_deep:
        print("没有根目录的文件", PROJECT_PATH_FILE_LIST)
        return ""

    # 没有找到，获取下一层
    return get_project_root(file_folder, max_deep, currt_deep)


def is_nodejs_project(project_path: str) -> str:
    if not os.path.exists(project_path):
        return ""

    file_list = ["package.json"]
    for each_file in file_list:
        p = os.path.join(project_path, each_file)
        # 只要有一个文件不存在，则返回False
        if os.path.exists(p):
            return p
    return ""


def is_python_project(project_path: str) -> str:
    if not os.path.exists(project_path):
        return ""

    file_list = ["pyproject.toml", "pyproject.tml"]
    for each_file in file_list:
        p = os.path.join(project_path, each_file)
        # 只要有一个文件不存在，则返回False
        if os.path.exists(p):
            return p

    return ""


def extract_scripts_from_project_file(file_path: str) -> List[str]:
    """
    @Description 解析配置文件的sctipts，生成可直接执行的shell指令，以列表形式返回

    - param file_path :{str} 项目的文件，根据.git、 .gitgnore、 README.md 等常见文件推断根目录

    @returns `{ list[str]}` shell指令,解析失败返回空列表
    @example
    ```py
    tar = os.path.realpath("..")

    scripts_list = extract_scripts_from_project_file(tar)

    print("scripts_list", scripts_list)

    >>> scripts_list:  ['poetry run test']

    ```
    """
    res = []

    # 查找项目根目录
    project_path = get_project_root(file_path)
    if not get_project_root:
        return res

    # BUG ParsingError无法解释pdm生成的project.toml文件
    # 先判断是什么项目，当前仅支持python和nodejs
    # project_file = is_python_project(project_path)
    # if not project_file:
    #     project_file = is_nodejs_project(project_path)

    project_file = is_nodejs_project(project_path)
    if not project_file:
        print("无法识别当前项目类型")
        return res

    # 读取ini文件
    if project_file.endswith((".ini", "toml", "tml")):
        ini_data = configparser.ConfigParser()
        ini_data.read(project_file, encoding="utf-8")

        if not FIELD_SCRIPTS_PY in ini_data.keys():
            return res

        for scripts_key in ini_data[FIELD_SCRIPTS_PY]:
            # 发现执行脚本，拼接成命令
            # print("scripts_key: ", scripts_key)
            # print("scripts_val: ", ini_data[FIELD_SCRIPTS][scripts_key])
            res.append(f"poetry run {scripts_key}")

        return res
    # 解析json
    elif project_file.endswith(".json"):
        with open(project_file, mode="r", encoding="utf-8") as f:
            json_data = json.loads(f.read())
            scripts = json_data.get("scripts", {})

            if scripts:
                return [f"npm run {script_key}" for script_key in scripts.keys()]
                # return [fscript_key for script_key in scripts.keys()]

    return list()


if __name__ == "__main__":
    tar = os.path.realpath(r"W:\CPS\MyProject\cps\cps-blog")
    # tar = os.path.realpath("..")

    scripts_list = extract_scripts_from_project_file(tar)

    print("scripts_list: ", scripts_list)
