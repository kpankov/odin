"""Flows and submodules controller"""

# Std
import os
import re

# Core
from core.logger import Logger
import flows


class Flow(object):
    def __init__(self, name=None, url=None) -> None:
        self._name = name
        self._url = url
        self._is_installed = False
        self._flow_dir_path = os.path.join(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "flows"), self._name)
        if self._check_installation():
            self._grep_commands()
            self._grep_configs()
            self._grep_modules()
            self._grep_projects()
            self._grep_templates()

    def _check_installation(self) -> bool:
        if self._name == "common":
            self._is_installed = True
        else:
            if os.path.isdir(self._flow_dir_path) and len(os.listdir(self._flow_dir_path)) > 0:
                self._is_installed = True
            else:
                self._is_installed = False
        return self._is_installed

    def _grep_commands(self):
        commands_dir_path = os.path.join(self._flow_dir_path, "commands")
        if os.path.isdir(commands_dir_path) and len(os.listdir(commands_dir_path)) > 0:
            pass

    def _grep_configs(self):
        pass

    def _grep_modules(self):
        pass

    def _grep_projects(self):
        pass

    def _grep_templates(self):
        pass

    def is_installed(self):
        return self._is_installed

    def get_name(self):
        return self._name

    def get_path(self):
        return self._flow_dir_path

    def get_info_tuple(self):
        return self._name, self._url, self._is_installed

    def get_info(self) -> str:
        return "Name: {}, URL: {}, Installed: {}".format(self._name, self._url, "yes" if self._is_installed else "no")


class Flows(object):
    def __init__(self) -> None:
        self._root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self._flows = []
        self._flows.append(Flow(name="common", url="https://github.com/kpankov/odin.git"))
        self._init_flows()

    def _init_flows(self):
        gitmodules_file_path = os.path.join(self._root_dir, ".gitmodules")
        if os.path.isfile(gitmodules_file_path):
            gitmodules_file = open(gitmodules_file_path, 'r')
            flow_name = None
            flow_url = None
            for index, line in enumerate(gitmodules_file.readlines(), 0):
                if line.strip().startswith("[") and flow_name is None:
                    flow_name = re.findall(r"\s*\[\s*submodule\s*\"flows/([A-Za-z0-9_]+)\"\s*\]", line)
                    if len(flow_name) == 1:
                        flow_name = flow_name[0]
                    else:
                        Logger.fatal("Parsing error: \".gitmodules\":{}: {}".format(index, line))
                if line.strip().startswith("url") and flow_url is None:
                    flow_url = re.findall(r"url\s*=\s*(.*)", line.strip())
                    if len(flow_url) == 1:
                        flow_url = flow_url[0]
                        self._flows.append(Flow(name=flow_name, url=flow_url))
                        flow_name, flow_url = None, None
                    else:
                        Logger.fatal("Parsing error: \".gitmodules\":{}: {}".format(index, line))

    def get_list(self) -> list:
        return self._flows

    def get_commands(self):  # TODO
        commands = []
        for flow in self._flows:
            if flow.is_installed():
                flow_name = flow.get_name()
                print(flow_name)

        return commands
