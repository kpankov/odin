"""Tools core module
"""

import os
import sys
from subprocess import run, PIPE, Popen

import yaml

from core.logger import Logger
from core.logger import bcolors


def _check_field(field) -> bool:
    """
    Check if filed is not None and != "None"(str)
    :return:
    False if field is None or == "None", True in other cases
    """
    if field is None or field == "None":
        return False
    return True


class Tool(object):
    """Class for single tool
    """

    def __init__(self, group, name, executable, version="None", bin_path="None", path="None", lib="None",
                 license="None", env={}, lsf_only=False) -> None:
        self.group = group
        self.name = name
        self.executable = executable
        self.version = version
        self.bin_path = bin_path
        self.path = path
        self.lib = lib
        self.license = license
        self.env = env
        self.lsf_only = lsf_only

        self.env_ready = False

    def setup(self):
        """
        Set tool's parameters (PATH, LD_LIBRARY_PATH, LM_LICENSE_FILE, other env vars) into odin's virtual environment.
        """
        if _check_field(self.bin_path):
            os.environ["PATH"] = self.bin_path + ":" + os.environ.get("PATH", "")
        if _check_field(self.path):
            os.environ["PATH"] = self.path + ":" + os.environ.get("PATH", "")
        if _check_field(self.lib):
            os.environ["LD_LIBRARY_PATH"] = self.lib + ":" + os.environ.get("LD_LIBRARY_PATH", "")
        if _check_field(self.license):
            os.environ["LM_LICENSE_FILE"] = self.license + ":" + os.environ.get("LM_LICENSE_FILE", "")
        if _check_field(self.env):
            for env_var in self.env:
                os.environ[env_var] = self.env.get(env_var)
        self.env_ready = True

    def run(self, params = None, stdout_capture: bool = False):
        """
        Run tool (just run for testing purposes).
        :param params:
        String of params
        :param stdout_capture:
        stdout capturing True/False
        :return:
        Set of (run_line, exit_code, stdout, stderr)
        """
        if self.env_ready is not True:
            self.setup()

        run_line = self.executable
        if params is not None:
            if type(params) is list:
                run_line += " " + " ".join(params)
            elif type(params) is str:
                run_line += " " + params

        if self.lsf_only:
            print("Starting using LSF...")
            run_line = "bsub -Is '" + run_line + "'"

        # Run
        if stdout_capture:
            process_handle = Popen(run_line, stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = process_handle.communicate()
            stdout, stderr = stdout.decode(sys.stdout.encoding or 'utf-8'), stderr.decode(sys.stderr.encoding or 'utf-8')
            exit_code = process_handle.returncode
        else:
            exit_code = os.system(run_line + " &")
            stdout = None
            stderr = None

        return run_line, exit_code, stdout, stderr


class Tools:
    """
    Class for tools' collection
    """
    def __init__(self) -> None:
        self.xml_path = None
        self.groups = []
        self.tools = []

    def parse_yaml(self, yaml_paths):
        file_data = {}
        for yaml_path in yaml_paths:
            if os.path.isfile(yaml_path):
                build_yaml_file = open(yaml_path, 'r')
                file_data.update(yaml.load(build_yaml_file, Loader=yaml.FullLoader)["tools"])
                build_yaml_file.close()
            else:
                Logger.error("No such file \"{}\"".format(yaml_path))
        for group in file_data:
            self.groups.append(group)
            for tool in file_data[group]:
                self.tools.append(Tool(group, tool["name"], tool["executable"],
                                       version=tool.get("version", None),
                                       bin_path=tool.get("bin_path", None),
                                       path=tool.get("path", None),
                                       lib=tool.get("lib", None),
                                       license=tool.get("license", None),
                                       env=tool.get("env", None),
                                       lsf_only=tool.get("lsf_only", False)
                                       ))

    def print_list(self):
        for group in self.groups:
            print()
            Logger.info("Group \"" + group + "\":")
            tools = self.get_tools_from_group(group)
            for tool in tools:
                Logger.info("\tTool \"" + tool.name + "\":")
                Logger.info("\t\tExecutable: {}".format(tool.executable))
                Logger.info("\t\t   Version: {}".format(tool.version))
                Logger.info("\t\t  Bin path: {}".format(tool.bin_path))
                Logger.info("\t\t   License: {}".format(tool.license))
                Logger.info("\t\t  Env vars: {}".format(str(tool.env)))
                Logger.info("\t\t  LSF only: {}".format(str(tool.lsf_only)))
                if tool.bin_path is not None:
                    path = os.path.join(tool.bin_path, tool.executable)
                    if os.path.isfile(path):
                        Logger.info("\t\t     Check: " + bcolors.OKGREEN + "PASS" + bcolors.ENDC)
                    else:
                        Logger.info("\t\t     Check: " + bcolors.FAIL + "FAIL" + bcolors.ENDC)
                else:
                    path = tool.executable
                    if run("which " + path, stdout=PIPE, stderr=PIPE, universal_newlines=True,
                           shell=True).returncode != 0:
                        Logger.info("\t\t     Check: " + bcolors.FAIL + "FAIL" + bcolors.ENDC)
                    else:
                        Logger.info("\t\t     Check: " + bcolors.OKGREEN + "PASS" + bcolors.ENDC)

    def get_groups_list(self):
        return self.groups

    def get_tools_from_group(self, group):
        ret_list = []
        for tool in self.tools:
            if tool.group == group:
                ret_list.append(tool)
        return ret_list

    def get_tool(self, name, group=None) -> Tool:

        counter = 0
        for tool in self.tools:
            if tool.name == name:
                if group is not None and tool.group == group:
                    return tool
                counter += 1
                res_tool = tool
        if counter == 0:
            return None
        if counter == 1:
            return res_tool
        if counter > 1:
            Logger.fatal("More then one instance of {} found! Use \"group\" parameter.".format(name))
            return None

    def replace_pathes_vars(self, project):
        for tool in self.tools:
            tool.path = project.recursive_replace(tool.path)
            tool.bin_path = project.recursive_replace(tool.bin_path)

    def check_tool(self, name, group) -> bool:
        """Checks if tool is available.
        
        Parameters
        ----------
        name : str
            The name of the tool
        
        Returns
        -------
        bool
            True - if tool is available.
            Flase - if tool is unavailable.
        """
        tool = self.get_tool(name, group)
        if tool.bin_path != "None":
            path = os.path.join(tool.bin_path, tool.executable)
            if os.path.isfile(path):
                return True
            else:
                return False
        else:
            path = tool.executable
            if run("which " + path, stdout=PIPE, stderr=PIPE, universal_newlines=True, shell=True).returncode != 0:
                return False
            else:
                return True
