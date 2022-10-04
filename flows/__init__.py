from keyword import iskeyword
from os import listdir
from os.path import dirname, join, isdir, isfile
from sys import modules

from core.logger import Logger
from core.tools import Tools

basedir = dirname(__file__)

__all__ = []
for name in listdir(basedir):
    flow_dir_path = join(basedir, name)
    if isdir(flow_dir_path) and len(listdir(flow_dir_path)) > 0 and not name.startswith('_') \
            and name.isidentifier() and not iskeyword(name):
        if len(listdir(flow_dir_path)) == 1 and listdir(flow_dir_path).pop() == ".git":
            Logger.warning("Only .git folder in flow \"{}\"!".format(name))
            continue
        try:
            __import__(__name__ + '.' + name)
        except Exception as e:
            Logger.warning('Ignoring exception while loading the \"{}\" flow. Exception: {}'.format(name, e))
        else:
            __all__.append(name)
__all__.sort()


def get_flows() -> list:
    return __all__


def get_commands(selected_flow=None) -> list:
    ret = []

    for flow in __all__:
        if selected_flow is not None and selected_flow != flow:
            continue
        try:
            commands = getattr(modules[__name__ + '.' + flow], "commands").__all__
        except AttributeError:
            Logger.fatal("No commands in flow \"{}\"".format(flow))

        for command in commands:
            command_dict = getattr(modules[__name__ + '.' + flow + ".commands." + command], "_command")
            ret.append(
                {"flow": flow, "name": command, "help": command_dict["help"], "params": command_dict["params"],
                 "flags": command_dict.get("flags", None), "silent": command_dict.get("silent", False),
                 "no_project": command_dict.get("no_project", False)})
    return ret


def get_command(command_name: str) -> dict:
    for command in get_commands():
        if command["name"] == command_name:
            return command
    Logger.error("No such command \"{}\"".format(command_name))
    return None


def get_flow_of_command(command_name: str) -> str:
    return get_command(command_name)["flow"]


def get_params_of_command(command_name: str) -> str:
    return get_command(command_name)["params"]


def get_silent_of_command(command_name: str) -> bool:
    return get_command(command_name)["silent"]


def get_no_project_of_command(command_name: str) -> bool:
    return get_command(command_name)["no_project"]


def get_tools() -> Tools:
    tools_file_list = []
    for flow in __all__:
        tools_file_path = join(join(join(basedir, flow), "configs"), "tools.yaml")
        if isfile(tools_file_path):
            tools_file_list.append(tools_file_path)
    tools = Tools()
    tools.parse_yaml(tools_file_list)
    return tools
