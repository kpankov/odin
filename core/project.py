import getpass
import logging
import os
import re
import yaml

from core.logger import Logger

logger = logging.getLogger(__name__)


class Step:
    """A class that used to represent a Step object

    Parameters
    ----------
    name : str
        name of step
    parameter : str
        parameter that used when step executes
    tools : list of tools
        contain tools used when step executes

    """

    def __init__(self, name, parameter="None", tools=[]):
        """
        Parameters
        ----------
        name : str
            name of step
        parameter : str
            parameter that used when step executes
        tools : list of tools
            contain tools used when step executes
        """
        self.name = name
        self.parameter = parameter
        self.tools = tools

    def print(self):
        """Prints information about step"""

        print(4 * " ", "Step name: ", self.name)
        print(4 * " ", "Step parameter: ", self.parameter)
        for tool in self.tools:
            tool.print()


class Tool:
    """A class object that represents the tool
    
    Attributes
    ----------
    name : str
        The name of tool
    parameter : str
        The parameter that used when tool runs

    """

    def __init__(self, name, parameter):
        """
        Parameters
        -----------
        name : str
            The name of tool
        parameter : str
            The parameter that used when tool runs
        """
        self.name = name
        self.parameter = parameter

    def print(self):
        """Prints information about tool"""

        print(8 * " ", "Tool name: ", self.name)
        print(8 * " ", "Tool parameters: ", self.parameter)


class Project:
    def __init__(self, project_file_path, global_variables):
        self._project_file_path = project_file_path
        self._project_file_type = None
        self._global_variables = global_variables
        self._name = "Unknown"
        self._variables = {}
        self._modules = []
        self._user_name = getpass.getuser()
        self.load()

    def get_user_name(self) -> str:
        """To get username you can use $USER variable, but often this can be overwritten by human. Use this method if
        you want to get "real" username.
        :return:
        Real username
        """
        return self._user_name

    def get_project_file_type(self) -> str:
        """Returns project configuration file type: xml or yaml.
        :return:
        "xml" or "yaml"
        """
        return self._project_file_type

    def load(self, custom_project_file_path=None, global_variables=None) -> bool:
        """This method detects .xml, .yaml and .yml files and calls other methods to load project file.

        Parameters
        ----------
        custom_project_file_path : string
            Custom project file path (will be stored in a class object)
        global_variables : list
            Custom global variables list (will be stored in a class object)

        Return
        ------
        result : bool
            Result of loading. True - is OK. False - failure.
        """
        if global_variables is not None:
            self._global_variables = global_variables

        if custom_project_file_path is not None and os.path.isfile(custom_project_file_path):
            self._project_file_path = custom_project_file_path
        elif not os.path.isfile(self._project_file_path):
            logger.warning("Can't find file " + self._project_file_path + "!")
            raise IOError
            return False

        project_file_dir, project_file_name = os.path.split(self._project_file_path)
        project_file_name_wo_ext, project_file_ext = os.path.splitext(project_file_name)

        if project_file_name_wo_ext != "project":
            Logger.warning("Please, use project.xml or project.yaml or project.yml file name for project file.")

        try:
            self._project_file_type = project_file_ext.split(".")[1]
        except IndexError:
            Logger.fatal("Can't define ext of project file!")
            return False

        logger.debug("Project file path: {}".format(self._project_file_path))

        if project_file_ext == ".xml":
            return self.load_xml()
        elif project_file_ext == ".yaml" or project_file_ext == ".yml":
            return self.load_yaml()
        else:
            Logger.fatal("Project file with unsupported extension '{}'!".format(project_file_ext))
            return False

    def load_yaml(self):
        project_data = {}
        with open(self._project_file_path, 'r') as project_file:
            project_data.update(yaml.load(project_file, Loader=yaml.FullLoader))

        if project_data.get("project") is None:
            Logger.fatal("Yaml file has wrong format!")
            return False

        self._name = project_data.get("project", {}).get("name")
        self._variables = project_data.get("project", {}).get("variables")
        self._modules = project_data.get("project", {}).get("modules")

        return True

    def load_xml(self):
        project_xml = etree.parse(self._project_file_path)
        project_xml_top = project_xml.getroot()

        self._name = project_xml_top.findtext("name")

        variables = project_xml_top.find("variables")
        for var in variables:
            self._variables[var.findtext("name")] = var.findtext("value")
            if var.findtext("auto") is not None and self._global_variables[var.findtext("auto")] is not None:
                self._variables[var.findtext("name")] = self._global_variables[var.findtext("auto")]
                Logger.info("Variable " + var.findtext("name") + " replaced by " + var.findtext("auto"))

        modules = project_xml_top.find("modules")
        if modules is not None:
            for module in modules:
                module_vars = {}
                module_filelists = {}
                module_steps = []
                variables = module.find("variables")
                if variables is not None:
                    for var in variables:
                        var_name = var.findtext("name")
                        var_value = var.findtext("value")
                        module_vars[var_name] = var_value
                filelists = module.find("filelists")
                if filelists is not None:
                    for filelist in filelists:
                        module_filelist = []
                        module_filelist_name = filelist.findtext("name")
                        files = filelist.findall("file")
                        for file in files:
                            module_filelist.append(file.text)
                    module_filelists[module_filelist_name] = module_filelist
                steps = module.find("steps")
                if steps is not None:
                    for step in steps:
                        list_tools = []
                        module_step_name = step.findtext("name")
                        module_step_parameter = step.findtext("parameter")
                        tools = step.find("tools")
                        if tools is not None:
                            for tool in tools:
                                tools_name = tool.findtext("name")
                                tools_parameter = tool.findtext("parameter")
                                list_tools.append(Tool(tools_name, tools_parameter))
                        module_steps.append(Step(module_step_name, module_step_parameter, list_tools))
                self._modules.append(
                    {'name': module.findtext("name"), 'type': module.findtext("type"), 'vars': module_vars,
                     'filelists': module_filelists, 'steps': module_steps})
        return True

    def recursive_replace(self, text, env={}):
        """Recursively replace environment variables by values

        Parameters
        ----------
        env : dictionary of strings
            dictionary of used environment variables
        """

        if text is not None:
            m = re.search('(\$)(\w+)', text)
            if m is not None:
                text = text.replace(m.group(0), self.get_global_var(m.group(2), env))
                text = self.recursive_replace(text, env)
        return text

    def resolve_module_vars(self, env=None):
        """Replace variables in modules by values environment varibales

        Parameters
        ----------
        env : dictionary of string
            dictionary of environment variables used in the project
        """
        if self._modules is not None:
            for module in self._modules:
                if module['vars'] is not None:
                    for name in module['vars']:
                        module['vars'][name] = self.recursive_replace(module['vars'][name], env)

    def get_module_vars_dict(self, type):
        if self._modules is not None:
            for module in self._modules:
                if module["type"] == type:
                    if module['vars'] is not None:
                        return module['vars']
        return None

    def is_var(self, name) -> bool:
        """
        Check if variable exists in the project
        :param name:
            Name of var
        :return:
            True if exists, False if not exists
        """
        if self._variables.get(name) is None:
            return False
        return True

    def get_var(self, name):
        ret = self._variables.get(name)
        if ret is None:
            logger.error("No such variable \"{}\" in the project! Try to add this to project config file.".format(name))
            os.abort()
        return ret

    def set_var(self, name, value):
        ret = self._variables.get(name)
        if ret is None:
            self._variables[name] = value

    def update_var(self, name, value):
        ret = self._variables.get(name)
        if ret is None:
            logger.error("Can't update project var! No such variable \"{}\" in the project! Try to add this to project config file.".format(name))
            os.abort()
        else:
            self._variables[name] = value

    def print_vars(self):
        for var in self._variables:
            print(var + ": " + self._variables[var])

    def replace_variables(self, expression):
        for var in self._variables:
            try:
                expression = expression.replace("$" + var, self._variables[var])
            except TypeError:
                return expression  # TODO: VAL-113
        return expression

    def replace_variables_in_parameters(self, env):
        """Replaces environment vars in parameter and name of tool in step by value of environment var
        
        Parameters
        ----------
        env : dictionary of strings
            dictionary of used environment variables
        """
        if self._modules is not None:
            for module in self._modules:
                if module['steps'] is not None:
                    for step in module['steps']:
                        if step.tools is not None:
                            for tool in step.tools:
                                # print("START", tool.parameter)
                                tool.parameter = self.recursive_replace(tool.parameter, env)
                                tool._name = self.recursive_replace(tool._name, env)
                                # print("END", tool.parameter)

    def set_vars_to_env(self):
        for var in self._variables:
            os.environ[var] = self._variables[var]

    def get_all_vars(self):
        return self._variables

    def get_module_data(self, type):
        for module in self._modules:
            if module["type"] == type:
                return module

    def modules_info(self):
        """Prints information about modules
        """
        for module in self._modules:
            print(100 * "-")
            for key in module.keys():
                if key != "steps":
                    print(key, ": ", module[key])
                else:
                    if module[key] == None:
                        print(key, ": None")
                    else:
                        print("Steps:")
                        for step in module[key]:
                            step.print()
        print(100 * "-")

    def get_global_var(self, name, virtual_env={}):
        ret = self._variables.get(name)
        if ret is None:
            ret = os.getenv(name)
        if ret is None:
            ret = virtual_env.get(name)
        if ret is None:
            logger.warning("Can't find variable \"{}\" in project, environment, virtual env!".format(name))
        return ret

    def replace_vars(self, to_replace, recursive=True, real_env_enable=False, virtual_env={}) -> str or list or dict:
        if type(to_replace) is str:
            m = re.findall(r'(?<!\$)\$(?!\$)(\w+)', to_replace)
            if bool(m):
                for item in m:
                    if self.get_global_var(item, virtual_env) is not None:
                        to_replace = to_replace.replace("${}".format(item), self.get_global_var(item, virtual_env))
                        stop_flag = False
                    else:
                        # logger.warning("Can't replace variable inside \"{}\"!".format(to_replace))
                        stop_flag = True
                if recursive and not stop_flag:
                    to_replace = self.replace_vars(to_replace, True, real_env_enable, virtual_env)
            postponed_vars = re.findall(r'\$\$(\w+)', to_replace)
            if bool(postponed_vars):
                logger.debug("Postponed var(s) found: {}".format(", ".join(postponed_vars)))
        elif type(to_replace) is list:
            for index, item in enumerate(to_replace):
                to_replace[index] = self.replace_vars(item, recursive, real_env_enable, virtual_env)
        elif type(to_replace) is dict:
            for item in to_replace:
                to_replace[item] = self.replace_vars(to_replace[item], recursive, real_env_enable, virtual_env)
        return to_replace

    def replace_postponed_vars(self, to_replace: str, replace_by: dict):
        """Replace postponed vars like "$$SAMPLE_PARAM"

        Usage example:
        core.project.replace_postponed_vars(core.project.get_var("TEST"), {"SAMPLE_PARAM": "Wololo"})

        :param to_replace:
        String with "$$SAMPLE_PARAM"
        :param replace_by:
        Dict with vars for replacement
        :return:
        String with replaced "$$SAMPLE_PARAM"
        """
        postponed_vars = re.findall(r'\$\$(\w+)', to_replace)
        if bool(postponed_vars):
            for item in postponed_vars:
                return to_replace.replace("$${}".format(item), replace_by[item])

    def resolve_vars(self):
        self._variables = self.replace_vars(self._variables)

    def write_project_yaml(self, path):
        """Save project as new YAML file
        :param path:
            New file path
        """
        new_yaml = {"project": {"name": self._name, "variables": self._variables, "modules": self._modules}}

        try:
            new_yaml_file = open(path, "w")
        except IOError:
            logger.error("Can't write to a file \"{}\"".format(path))
            os.abort()
        else:
            yaml.dump(new_yaml, new_yaml_file)
        finally:
            new_yaml_file.close()
