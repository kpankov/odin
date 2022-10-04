#!/usr/bin/env python

import argparse
import os
from sys import modules
import logging

import flows
from core import Core, Logger, Project, Release, print_onsemi_logo

"""
Globals
"""
DEFAULT_PROJECT_FILENAME = "project"
release = "HEAD"  # TODO: Replace this by some argument?

global_variables = {}


def get_project_file_path():  # TODO: Move to a separate file?
    project_file_path = os.getenv("PROJECT_XML", default=os.getenv("PROJECT_YAML", default=os.getenv("PROJECT_YML")))

    if project_file_path is None:
        project_file_path_wo_ext = os.path.join(os.path.abspath(""), DEFAULT_PROJECT_FILENAME)
        for ext in [".xml", ".yaml", ".yml"]:
            if os.path.isfile(project_file_path_wo_ext + ext):
                project_file_path = project_file_path_wo_ext + ext

    if project_file_path is None:
        log.fatal("No project.xml/.yaml/.yml file found! \
                    You can just go to the project's folder or set $PROJECT_XML/PROJECT_YAML/PROJECT_YML env var.")

    return project_file_path


"""Main
"""
if __name__ == "__main__":
    log = Logger(debug_level=Logger.DBG_ALL)  # TODO: Replace by logger from stdlib

    logging.basicConfig(
        # level=logging.INFO,
        level=logging.DEBUG,
        format="%(asctime)s - [%(levelname)s] - %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s",
    )
    logger = logging.getLogger("odin.py")

    global_variables["ODIN_PATH"] = os.path.dirname(os.path.abspath(__file__))
    global_variables["ODIN_WORKDIR_PATH"] = os.getcwd()
    # conf_path = os.path.join(global_variables["ODIN_PATH"], "conf")  # TODO: Delete

    """
    ArgParser
    """
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="command", help='Command list:', dest='command')
    subparser = {}
    for command in flows.get_commands():
        subparser[command["name"]] = subparsers.add_parser(command["name"],
                                                           help="{} ({})".format(command["help"], command["flow"]))
        if command["params"] is not None:
            for param in command["params"]:
                subparser[command["name"]].add_argument('--'+param['name'], default=param['default'], help=param['help'])
        if command["flags"] is not None:
            for flag in command["flags"]:
                subparser[command["name"]].add_argument('-'+flag['name'], nargs="?", default=False, const=True, help=flag['help'])

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        log.bypass("\nUse \"odin.py command -h\" for more information about commands.", flush=True)
        exit(0)

    log.set_silent_mode(flows.get_silent_of_command(args.command))

    print_onsemi_logo(log)

    if not flows.get_no_project_of_command(args.command):
        global_variables["PROJECT_FILE_PATH"] = get_project_file_path()

        """Project
        """
        project = Project(global_variables["PROJECT_FILE_PATH"], global_variables)
        project.resolve_vars()

        """Releases
        """
        release = Release(global_variables["PROJECT_FILE_PATH"], project.get_project_file_type(), release)
    else:
        project = None
        release = None

    """Core
    """
    core_data = Core()
    core_data.set(project=project, release=release, flows=flows, args=args, glob_vars=global_variables)

    command = getattr(modules["flows." + flows.get_flow_of_command(args.command) + ".commands"], args.command)
    try:
        run_command = command.run
    except AttributeError:
        log.fatal("Bad command \"{}\"!".format(args.command))
    else:
        log.bypass(" Run command \"{}\" ".format(args.command).center(80, "-"))
        result = run_command(core_data)
        log.bypass(" End ".center(80, "-"))
        exit(result)
