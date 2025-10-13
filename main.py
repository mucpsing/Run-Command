import sublime
import sublime_plugin
import os

from os import path
from .core import shell
from .core.Type import Optional, List
from .core.history import History

from .core.scriptsParser import extract_scripts_from_project_file

DEFAULT_SETTINGS = "cps.sublime-settings"

PANEL_NAME = "cps"
BASE_PACKAGE_NAME = "cps-plugins"
PLUGIN_NAME = "run-commands"

OUTPUT_PANEL_NAME = f"output.{ PANEL_NAME }"

WORK_SPACE = ""
CANT_RUN_WORK_SPACE = [path.abspath("."), path.abspath(path.dirname(__package__))]
COMMAND_NAME = {"update": f"{PANEL_NAME}_update_panel"}


LAST_ACTIVE_PANEL = None  # 最后一次的前置弹出框，用来隐藏清屏
LAST_COMMAND_STR = ""  # 最后一次执行的命令，用来占位
LAST_COMMAND_PLACEHOLDER = True  # 是否使用最后一次输入的命令来占位
RUN_IN_NEW_WINDOW_PREFIX = [":", "$"]  # 指定需要单独执行命令的前缀符号

MODE_CUSTOM_COMMAND = 0
MODE_DELETE_HISTORY = 1

SCRIPTS_SUFFIX: str = "【Project Script】"
SCRIPTS_LIST: List[str] = []


DEFAULT_PANEL_SETTINGS = {
    "auto_indent": False,  # 是否自动缩进
    "draw_indent_guides": False,  #
    "draw_unicode_white_space": None,  #
    "draw_white_space": None,  #
    "fold_buttons": True,  #
    "gutter": False,  #
    "is_widget": True,  #
    "line_numbers": False,  #
    "lsp_active": True,  #
    "margin": 0,  #
    "match_brackets": False,  #
    "rulers": [],  #
    "scroll_past_end": True,  #
    "show_definitions": False,  #
    "tab_size": 4,  #
    "translate_tabs_to_spaces": True,  #
    "word_wrap": False,  #
}


# histroy settings
MSG_SELECTIONS_HELP = 'Press "Enter" to enter a custom command'
HIGHEST_SELECTIONS = [
    "【菜单】 input custom command",
    "【菜单】 delete histroy command",
]
SCRIPTS_LIST = []
history_file = path.join(sublime.packages_path(), "User", f".{__package__}.histroy")
HISTORY = History(history_file, max_count=100)


def ensure_panel(panel_name: str) -> sublime.View:
    """
    @Description 初始化下方信息框

    - param panel_name :{str} 信息框的名称
    """
    window = sublime.active_window()
    panel = window.find_output_panel(panel_name)

    try:
        if panel:
            return panel
        else:
            return create_panel(panel_name)
    except Exception as err:
        print(err)
        return window.find_output_panel("exec")


def create_panel(panel_name: str) -> Optional[sublime.View]:
    global DEFAULT_PANEL_SETTINGS

    window = sublime.active_window()
    panel = window.create_output_panel(panel_name)
    settings = panel.settings()

    [settings.set(key, value) for key, value in DEFAULT_PANEL_SETTINGS]
    return panel


def plugin_loaded():
    ensure_panel(PANEL_NAME)


class CpsUpdatePanelCommand(sublime_plugin.TextCommand):
    """
    @Description 的panel窗体数据。

    - param panel_name :{str} "panel_name":panel_name
    """

    def run(self, edit: sublime.Edit, panel_name: str, data: str):
        global OUTPUT_PANEL_NAME

        window = sublime.active_window()
        panel = window.find_output_panel(panel_name)

        if not panel:
            return print(f"无法找到 {panel_name} 窗口")

        panel.set_read_only(False)
        panel.replace(edit, sublime.Region(0, panel.size()), data)
        panel.set_read_only(True)

        window.run_command("show_panel", {"panel": OUTPUT_PANEL_NAME})


class CpsRunCommandsCommand(sublime_plugin.TextCommand):
    """
    @Description 通过快捷键可以在任何时候快捷的输入一些简单的shell命令，不支持大量数据处理和需要交互的指令
    @example
    ```bash
    # 调出输入框
    alt + f1

    # 简单的指令
    npm -v & node -v & yarn -v

    # 简单的安装指令
    npm i -D @types/node12

    # "$" 或者 ":" 前缀，调用新的shell窗口运行指令
    # 后续cmd窗口会等待15秒后自动关闭
    $npm init

    # 后续cmd窗口需要用户按任意键才能关闭
    :npm init
    ```
    """

    def run(self, edit: sublime.Edit):
        global HISTORY, HIGHEST_SELECTIONS, DEFAULT_SETTINGS, SCRIPTS_LIST

        SETTINGS = sublime.load_settings(DEFAULT_SETTINGS).get(PLUGIN_NAME, {})

        window = sublime.active_window()
        panel_name = window.active_panel()

        if SETTINGS and SETTINGS["history_count"]:
            commands_count = SETTINGS["history_count"]
        else:
            commands_count = 500

        commands_list = HISTORY.data[0:commands_count]
        # print("创建历史记录", HISTORY.data[0])

        # TODO: 这里添加一个配置明确脚本是内部调用（阻塞）还是外部执行（调用独立shell）
        # if xxxx:
        #     SCRIPTS_LIST = extract_scripts_from_project_file(self.view.file_name())
        SCRIPTS_LIST = [each_script for each_script in extract_scripts_from_project_file(self.view.file_name())]
        # 添加前缀
        SCRIPTS_LIST_WITH_PREFIX = [f"{SCRIPTS_SUFFIX} {command}" for command in SCRIPTS_LIST]

        # 1、生成: "x. command" 的格式
        # 2、将历史记录加入到显示列表
        selection_with_index = [f"{index + 1 }.  {commands_list[index]}" for index in range(len(commands_list))]

        if panel_name:
            window.run_command("hide_panel", {"panel": panel_name})
        else:
            self.show_selection(HIGHEST_SELECTIONS + SCRIPTS_LIST_WITH_PREFIX + selection_with_index)

    def show_selection(self, items: List[str]):
        """
        @Description 让用户选择是自己输入还是历史记录

        - param items :{List[str]} {description}
        """

        global MSG_SELECTIONS_HELP
        sublime.active_window().show_quick_panel(
            items=items,
            on_select=self.on_select,
            flags=0,
            selected_index=-1,
            placeholder=MSG_SELECTIONS_HELP,
        )

    def input_custom_commands(self, placeholder: str = ""):
        """
        - param placeholder :{str} 占位符
        - param mode=0      :{int} 业务模式 MODE_CUSTOM_COMMAND|MODE_DELETE_HISTORY

        """
        global HISTORY
        global LAST_COMMAND_PLACEHOLDER, LAST_COMMAND_STR

        if LAST_COMMAND_PLACEHOLDER:
            placeholder = LAST_COMMAND_STR

        sublime.active_window().show_input_panel(
            caption=f'Use1 the ":" or "$" prefix can make new shell like ":command xxx"',
            initial_text=placeholder,
            on_done=self.on_done,
            on_change=self.on_change,
            on_cancel=self.on_cancel,
        )

    def on_delete_history_command_select(self, command_index: int):
        print("on_delete_history_command_select: ", command_index)

        # 防止误删，当输入是默认时，什么都不做
        if command_index == -1:
            return

        try:
            HISTORY.delete_by_index(command_index)
        except Exception as e:
            print("history delete fail: ", command_index)
            print("history delete fail: ", e)

    def on_select(self, user_select_index: int):
        global SCRIPTS_LIST, MODE_RUN_SCRIPTS
        global HIGHEST_SELECTIONS, HISTORY
        global MODE_CUSTOM_COMMAND, MODE_DELETE_HISTORY

        # 当输入是默认时，什么都不做
        if user_select_index == -1:
            return

        # 【菜单】 delete histroy command
        elif user_select_index == MODE_DELETE_HISTORY:
            # 生成: "x. command" 的格式
            selection_with_index = [f"{index}.  {HISTORY.data[index]}" for index in range(len(HISTORY.data))]

            # 重新显示所有命令
            sublime.active_window().show_quick_panel(
                items=selection_with_index,
                on_select=self.on_delete_history_command_select,
                flags=0,
                selected_index=-1,
                placeholder="select a command to delete",
            )

        # 【菜单】 执行自定义命令，调用pannel
        elif user_select_index == MODE_CUSTOM_COMMAND:
            self.input_custom_commands()

        # 【SCRIPTS】
        # 用户选择的索引小于脚本指令的长度则是执行脚本指令
        elif (len(HIGHEST_SELECTIONS) + len(SCRIPTS_LIST)) > user_select_index:
            script_index = user_select_index - len(HIGHEST_SELECTIONS)
            self.on_done(SCRIPTS_LIST[script_index])

        # 执行历史命令
        else:
            command_index = user_select_index - len(HIGHEST_SELECTIONS) - len(SCRIPTS_LIST)
            self.on_done(HISTORY.data[command_index])

    def on_done(self, user_input: int):
        # print("user_input: ", user_input)
        global PANEL_NAME
        sublime.set_timeout_async(self.run_command(user_input, PANEL_NAME))

    def on_change(self, text: str):
        pass

    def on_cancel(self):
        pass

    def run_command(self, user_input: str, panel_name: str = None):
        """
        入口函数，通过分析用户输入的命令并执行

        - param user_input :{str} 用户的原始输入
        """
        global RUN_IN_NEW_WINDOW_PREFIX
        global HISTORY, COMMAND_NAME
        global PANEL_NAME
        global LAST_COMMAND_STR

        SETTINGS = sublime.load_settings(DEFAULT_SETTINGS).get(PLUGIN_NAME, {})
        LAST_COMMAND_STR = user_input
        has_open_file = self.view.file_name()

        # 如果没有打开文件，指定一个默认的执行工作目录
        if has_open_file:
            work_space = os.path.dirname(has_open_file)
        else:
            work_space = SETTINGS.get("default_workspace", path.join(sublime.packages_path(), __package__))

        # run in new shell window
        run_with_new_window = False

        # add in histroy commands
        record_commands = True
        if user_input[0][0] in RUN_IN_NEW_WINDOW_PREFIX:
            run_with_new_window = 30

            commands = str(user_input[1:]).split(" ")
        else:
            # running in sublime exec
            commands = str(user_input).split(" ")

        if record_commands:
            HISTORY.add(user_input)
            # print("user_input: ", user_input)
            # print("user_input: ", HISTORY.data[0])

        print("commands: ", commands)
        print("run_with_new_window: ", run_with_new_window)
        # res = shell.run_command(
        res = shell.run_command_new(
            commands,
            shell=run_with_new_window,
            pause=run_with_new_window,
            cwd=work_space,
        )

        command_res = None
        if res["success"]:
            if "res" in res:
                command_res = res["res"]
        else:
            command_res = res["err"]

        if command_res:
            sublime.active_window().run_command(
                COMMAND_NAME["update"],
                {
                    "panel_name": panel_name,
                    "data": (
                        f"COMMANDS: {commands}\n"
                        f"WORK_SPACE: {work_space}\n\n"
                        f"{command_res}\n\n"
                        f"[done by {__package__}]"
                    ),
                },
            )


class CpsPanelToggleCommand(sublime_plugin.TextCommand):
    """
    @Description 显示最近一次关闭的消息窗口
    @example
    ```bash
    # 显示/隐藏 最近一次的panel
    alt + f2
    ```
    """

    def run(self, edit: sublime.Edit):
        global LAST_ACTIVE_PANEL, OUTPUT_PANEL_NAME
        active_panel = sublime.active_window().active_panel()
        window = sublime.active_window()

        if active_panel:
            LAST_ACTIVE_PANEL = active_panel
            if active_panel:
                window.run_command("hide_panel", {"panel": active_panel})

        else:
            if LAST_ACTIVE_PANEL in [None, "console"]:
                panel_name = OUTPUT_PANEL_NAME
            else:
                panel_name = LAST_ACTIVE_PANEL

            window.run_command("show_panel", {"panel": panel_name})
