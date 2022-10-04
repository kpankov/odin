"""Flows managing
"""

import os
import re

from core.logger import Logger
from core.vcs_git import VcsGit

_command = {'help': "Flows managing",
            'params': [{"name": "update", "help": "Update submodule [name] or 'all'", "default": None}],
            'no_project': True}


def get_flows_submodules(core):
    _flows = {}
    for _flow in core.flows.get_flows():
        _flows[_flow] = None
    gitmodules_file_path = os.path.join(core.glob_vars["ODIN_PATH"], ".gitmodules")
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
                    _flows[flow_name] = flow_url
                    flow_name, flow_url = None, None
                else:
                    Logger.fatal("Parsing error: \".gitmodules\":{}: {}".format(index, line))
    return _flows


def run(core):
    Logger.info("List of supported flows:")
    flows = get_flows_submodules(core)
    for flow in flows:
        Logger.info("\t> {}\t{}".format(flow, "local" if flows[flow] is None else flows[flow]))
        for command in core.flows.get_commands(flow):
            Logger.info("\t\t- {}".format(command.get("name")))

    if core.args.update is not None:  # TODO: Add 'all' case
        url = flows.get(core.args.update, None)
        if url is None:
            Logger.fatal("Can't update submodule \"{}\"!".format(core.args.update))
        else:
            flows_dir_path = os.path.join(core.glob_vars["ODIN_PATH"], "flows")
            git = VcsGit(url=url, local_path=os.path.join(flows_dir_path, core.args.update))
            Logger.info("Update {} flow...".format(core.args.update))
            if git.submodule_update() == 0:
                Logger.green("> Updated")
            else:
                return 1

    return 0
