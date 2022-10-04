"""Scoreboard module

This module allows the user to collect some command's results into
the file *scoreboard.yaml*.

Example structure of scoreboard file:
    * collection1:
        * element1:
            * filed1: data1
            * filed2: data2
            * ...
        * element2:
            * filed1: data1
            * filed2: data2
            * ...
    * collection2:
        * element1:
            * filed1: data1
            * filed2: data2
            * ...
    * ...
"""

import os
import yaml
import logging

from core.core import Core
from core.logger import Logger

logger = logging.getLogger(__name__)

# Const
SCOREBOARD_FILE_NAME = "scoreboard.yaml"


class Scoreboard(object):

    def __init__(self, core):
        self.core = core
        if core.project.is_var("WORKING_DIR"):
            self.scoreboard_file_path = os.path.join(core.project.get_var("WORKING_DIR"), SCOREBOARD_FILE_NAME)
        else:
            self.scoreboard_file_path = os.path.join(core.glob_vars["ODIN_WORKDIR_PATH"], SCOREBOARD_FILE_NAME)

    def is_initialized(self) -> bool:
        """
        Check existing if scoreboard yaml file
        :return:
        True if scoreboard file exists, False if not
        """
        if os.path.isfile(self.scoreboard_file_path):
            return True
        return False

    def get_file_path(self):
        return self.scoreboard_file_path

    def _read_scoreboard(self):
        if os.path.isfile(self.scoreboard_file_path):
            build_yaml_file = open(self.scoreboard_file_path, 'r')
            data = yaml.load(build_yaml_file, Loader=yaml.FullLoader)
            build_yaml_file.close()
            return data
        else:
            return None

    def _write_scoreboard(self, data):
        build_yaml_file = open(self.scoreboard_file_path, "w")
        yaml.dump(data, build_yaml_file)
        build_yaml_file.close()
        return True

    def clean_up(self):
        """Delete existing scoreboard.yaml
        """
        os.system("rm -rf " + self.scoreboard_file_path)

    def create_from_template(self, filename):
        templates_dir_path = os.path.join(self.core.glob_vars['ODIN_PATH'], 'flows', 'validation', 'templates')
        if not os.path.isdir(templates_dir_path):
            logger.error('Bad path for template: {}'.format(templates_dir_path))
            os.abort()
        fpga_build_scoreboard_file_path = os.path.join(templates_dir_path, filename)
        self.clean_up()
        os.system("cp " + fpga_build_scoreboard_file_path + " " + self.scoreboard_file_path)
        return self.scoreboard_file_path

    def update_step(self, step, result, comment) -> bool:
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        if step in valuesYaml["steps"]:
            valuesYaml["steps"][step]["result"] = result
            valuesYaml["steps"][step]["comment"] = comment
        else:
            return False

        return  self._write_scoreboard(valuesYaml)

    def update_repositories(self, list) -> bool:
        """Update list of repositories

        Parameters
        ----------
        list: str
            List of repositories

        Returns
        -------
        result: bool
            Returns true if updating was successful, if unsuccessful - false

        Warning
        -------
        Only for SoS repositories.
        """
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        if "repositories" not in valuesYaml:
            valuesYaml["repositories"] = {}

        for repo in list:
            valuesYaml["repositories"][repo.get_name()] = self.core.project.replace_variables(repo.get_tag())

        return self._write_scoreboard(valuesYaml)

    def update_repository(self, repo_name, repo_tag) -> bool:
        """Update repository

        Parameters
        ----------
        repo_name: str
            Name of repository

        Returns
        -------
        result: bool
            Returns true if updating was successful, if unsuccessful: false

        Warning
        -------
        Only for SoS repositories.
        """
        values_yaml = self._read_scoreboard()
        if values_yaml is None:
            return False

        if 'repositories' not in values_yaml:
            values_yaml['repositories'] = {}

        values_yaml['repositories'][repo_name] = self.core.project.replace_variables(repo_tag)

        return self._write_scoreboard(values_yaml)

    def clean_repositories(self) -> bool:
        """Cleans list of repositories

        Returns
        -------
            Returns True if scoreboard.xml exists and clean was done, False - if not
        """
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        valuesYaml["repositories"].clear()

        return  self._write_scoreboard(valuesYaml)

    def clean_builds(self) -> bool:
        """Cleans list of builds in scoreboard

        Returns
        -------
            Returns True if scoreboard.xml exists and clean was done, False - if not
        """
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        valuesYaml["builds"].clear()

        return  self._write_scoreboard(valuesYaml)

    def append_builds_info(self, platform, build_info) -> bool:
        """Append build_info element for determined platform

        Parameters
        ----------
        platform : str
            Name of used platform
        build_info : str
            Information about build

        Returns
        -------
            Returns True if scoreboard.xml exists, and clean was done, else - False
        """
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        try:
            valuesYaml["builds"][platform].append(build_info)
        except KeyError:
            valuesYaml["builds"][platform] = []
            valuesYaml["builds"][platform].append(build_info)

        return  self._write_scoreboard(valuesYaml)

    def update_builds(self, platform=None) -> bool:
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        # TODO: add adding parameters of platform

        return self._write_scoreboard(valuesYaml)

    def get(self, field_name):
        """Gets value of a top field

        Parameters
        ----------
        field_name : str
            Name of the field

        Returns
        -------
        result: any
            Returns value of the field or None if the field doesn't exist or False if can't open scoreboard file
        """
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        if field_name in valuesYaml:
            return valuesYaml[field_name]
        else:
            return None

    def get_build_info(self, platform):
        return self.get("builds")[platform]

    def get_steps(self):
        return self.get("steps")

    def add_top_field(self, field_name, field_data) -> bool:
        """Add new top filed or change existing

        Parameters
        ----------
        field_name : str
            Name of the field
        field_data : str
            Value of the filed

        Returns
        -------
        result: bool
            True if successful
        """
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        valuesYaml[field_name] = field_data

        return self._write_scoreboard(valuesYaml)

    def add(self, collection, name, data) -> bool:
        """Adds new collection's element.

        Parameters
        ----------
        collection : str
            The file location of the spreadsheet TODO
        name : str
            A flag used to print the columns to the console TODO
        data : any
            A flag used to print the columns to the console TODO

        Returns
        -------
        result: bool
            True if successful
        """
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        if collection not in valuesYaml:
            valuesYaml[collection] = {}
        valuesYaml[collection][name] = data

        return  self._write_scoreboard(valuesYaml)

    def change(self, collection, name, field, vol):
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        if collection not in valuesYaml:
            valuesYaml[collection] = {}
        valuesYaml[collection][name][field] = vol

        return self._write_scoreboard(valuesYaml)

    def add_build(self, target, data) -> bool:
        """Add build

        Parameters
        ----------
        target: str
            Name of a target (fpga_c, fpga_d, veloce)

        Returns
        -------
        result: bool
            True if build was added, or False if failed
        """
        valuesYaml = self._read_scoreboard()
        if valuesYaml is None:
            return False

        if "builds" not in valuesYaml:
            valuesYaml["builds"] = {}
        if target not in valuesYaml["builds"]:
            valuesYaml["builds"][target] = []

        valuesYaml["builds"][target].append(data)

        return self._write_scoreboard(valuesYaml)

    def add_sim_test(self, test, result) -> bool:
        return self.add("sim_tests", test, result)

    def test_failed(self, name):
        self.change("sim_tests", name, "result", "Failed")

    def test_passed(self, name):
        self.change("sim_tests", name, "result", "Passed")

    def get_testlist_sve(self):
        testlist = []
        if os.path.isfile(self.scoreboard_file_path):
            build_yaml_file = open(self.scoreboard_file_path, 'r')
            valuesYaml = yaml.load(build_yaml_file, Loader=yaml.FullLoader)
            build_yaml_file.close()
            collection = "sim_tests"
            if collection in valuesYaml:
                for test in valuesYaml[collection]:
                    if valuesYaml[collection][test]["type"] == "sve":
                        testlist.append(valuesYaml[collection][test]["name"])
            else:
                return None
        else:
            return None
        return testlist


class FpgaScoreboard(Scoreboard):  # TODO: No need?
    def __init__(self, core) -> None:
        super().__init__(core)


def scoreboard_step(step, comment="Ok"):
    def actual_decorator(func):
        def wrapper(*args, **kwargs):
            score_board = Scoreboard(Core())
            if score_board.is_initialized():
                print(" Scoreboard: start of step \"{}\" ".format(step).center(80, "-"))
                retval = func(*args)
                if retval == 0:
                    if not score_board.update_step(step, "Passed", comment):
                        Logger.warning("Can't update scoreboard!")
                else:
                    if not score_board.update_step(step, "Failed", "Unknown error"): # TODO: comment
                        Logger.warning("Can't update scoreboard!")
                print(" Scoreboard: end of step \"{}\" ".format(step).center(80, "-"))
                return retval
            else:
                return func(*args)
        return wrapper
    return actual_decorator
