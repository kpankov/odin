"""Release core module
"""

import logging
import os

import yaml
from lxml import etree

DEFAULT_RELEASE_FOLDER = "releases"
DEFAULT_RELEASE_FILENAME = "release"
logger = logging.getLogger(__name__)


class Dependence:
    def __init__(self, kids, next=None):
        if type(kids) is str:
            self.kids = None
            self.name = kids
        else:
            self.kids = kids
            self.name = "Top"
        self.next = next
        self.vcs_local_path = None

    def set_kids(self, kids):
        self.kids = kids

    def add_kids(self, kid) -> None:
        dep = self.kids
        if dep == None:
            self.kids = kid
        else:
            while True:
                if dep.is_last():
                    dep.set_next(kid)
                    break
                else:
                    dep = dep.get_next()

    def is_last(self) -> bool:
        if self.next is None:
            return True
        else:
            return False

    def set_next(self, next):
        self.next = next

    def get_next(self):
        return self.next

    def set_name(self, name):
        self.name = name

    def get_name(self) -> str:
        return self.name

    def get_kids(self):
        return self.kids

    def get_type(self):  # Override it
        return None

    def find_kid(self, name):
        dep = self.get_kids()
        while True:
            if dep.get_name() is name:
                return dep
            else:
                if dep.is_last():
                    break
                else:
                    dep = dep.get_next()
        return None

    def set_local_path(self, path):
        self.vcs_local_path = path


class RepoSos(Dependence):
    def __init__(self, kids, next, name, local_path, tag):
        super().__init__(kids, next=next)
        super().set_name(name)
        self.local_path = local_path
        self.tag = tag

    def get_type(self):
        return "sos"

    def get_tag(self) -> str:
        """Returns tag for RepoSos object

        Returns
        -------
        str
            Returns tag for RepoSos object
        """
        return self.tag


class RepoGit(Dependence):
    def __init__(self, kids, next, name):
        super().__init__(kids, next=next)
        super().set_name(name)

    def get_type(self):
        return "git"


class Release:
    def __init__(self, project_file_path, project_file_type, release="HEAD"):
        self._project_file_path = project_file_path
        self._project_file_type = project_file_type
        self._release = release
        self._release_dir_path = None
        self._release_file_path = None
        self._version = "Unknown"
        self._dependencies = Dependence(None)
        self.repo_sos = []  # TODO
        self.sos_local_paths = []  # TODO
        self.load()

    def load(self, custom_project_file_path=None, project_file_type=None, release=None):
        if project_file_type is not None:
            self._project_file_type = project_file_type

        if release is not None:
            self._release = release

        if custom_project_file_path is not None and os.path.isfile(custom_project_file_path):
            self._project_file_path = custom_project_file_path
        elif not os.path.isfile(self._project_file_path):
            logger.fatal("Can't find file {}!".format(self._project_file_path))
            os.abort()

        self._release_dir_path = os.path.join(os.path.dirname(self._project_file_path), DEFAULT_RELEASE_FOLDER)
        if self._release == "HEAD":
            release_file_name = "{}.{}".format(DEFAULT_RELEASE_FILENAME, self._project_file_type)
        else:
            release_file_name = "{}_{}.{}".format(DEFAULT_RELEASE_FILENAME, self._release, self._project_file_type)
        self._release_file_path = os.path.join(self._release_dir_path, release_file_name)
        logger.debug("Release file path: {}".format(self._release_file_path))

        if not os.path.isfile(self._release_file_path):
            logger.fatal("Can't find release file {}!".format(self._release_file_path))
            os.abort()

        if self._project_file_type == "xml":
            return self.load_xml()
        elif self._project_file_type == "yaml" or self._project_file_type == "yml":
            return self.load_yaml()
        else:
            logger.fatal("Project file with unsupported extension '{}'!".format(self._project_file_type))
            os.abort()

    def load_yaml(self):
        release_data = {}
        with open(self._release_file_path, 'r') as release_file:
            release_data.update(yaml.load(release_file, Loader=yaml.FullLoader))

        if release_data.get("release") is None:
            logger.fatal("Release yaml file has wrong format!")
            os.abort()

        self._version = release_data.get("release", {}).get("version")
        dependencies_dict = release_data.get("release", {}).get("dependencies")

        for dep_type in dependencies_dict:
            self._dependencies.add_kids(Dependence(dep_type))
            node = self._dependencies.find_kid(dep_type)
            for dep in dependencies_dict[dep_type]:
                if dep.get("vcs") == "sos":
                    node.add_kids(RepoSos(None, None, name=dep.get("name"), local_path=dep.get("local_path"),
                                          tag=dep.get("tag")))
                    self.sos_local_paths.append(dep.get("local_path"))  # TODO
                    self.repo_sos.append(
                        RepoSos(None, None, name=dep.get("name"), local_path=dep.get("local_path"),
                                tag=dep.get("tag")))  # TODO
                elif dep.get("vcs") == "git":
                    node.add_kids(RepoGit(None, None, name=dep.get("name")))
                elif dep.get("vcs") == "svn":
                    pass  # TODO
                else:
                    node.add_kids(Dependence(dep.get("name")))

    def load_xml(self):
        release_xml = etree.parse(self._release_file_path)
        release_xml_top = release_xml.getroot()

        self._version = release_xml_top.findtext("version")

        dependencies = release_xml_top.find("dependencies")
        for dep_type in dependencies:
            if dep_type.tag == "hardware":
                pass
            elif dep_type.tag == "software":
                pass
            elif dep_type.tag == "scripts":
                pass
            elif dep_type.tag == "shared":
                pass
            else:
                print("ERROR: Undefined dependence group!")  # TODO
                exit(1)
            self._dependencies.add_kids(Dependence(dep_type.tag))
            node = self._dependencies.find_kid(dep_type.tag)
            for dep in dep_type:
                # print("| ├ " + dep.findtext("name"))
                if dep.findtext("vcs") == "sos":  # TODO: Add others
                    # print("| ├ " + dep.findtext("local_path"))
                    node.add_kids(RepoSos(None, None, name=dep.findtext("name"), local_path=dep.findtext("local_path"),
                                          tag=dep.findtext("tag")))
                    self.sos_local_paths.append(dep.findtext("local_path"))  # TODO
                    self.repo_sos.append(
                        RepoSos(None, None, name=dep.findtext("name"), local_path=dep.findtext("local_path"),
                                tag=dep.findtext("tag")))  # TODO
                else:
                    node.add_kids(Dependence(dep.findtext("name")))

    def print_graph(self):
        print("Dependencies:")

        dep = self._dependencies
        depth = 0

        stack = []

        while True:
            for i in range(0, depth):
                if stack[i].is_last():
                    print("  ", end="")
                else:
                    print("| ", end="")

            if dep.is_last():
                print("└ ", end="")
            else:
                print("├ ", end="")

            if dep.get_type() is None:
                print(dep.get_name())
            else:
                print("{} ({})".format(dep.get_name(), dep.get_type()))

            if dep.kids is not None:
                depth += 1
                stack.append(dep)
                dep = dep.get_kids()
            else:
                if dep.is_last():
                    while dep.is_last():
                        depth -= 1
                        if depth <= 0:
                            break
                        dep = stack.pop()
                    if depth <= 0:
                        break
                    dep = dep.get_next()
                else:
                    dep = dep.get_next()

    def get_repo_sos(self, name):
        for repo in self.repo_sos:
            if repo.get_name() == name:
                return repo
        return None

    def get_all_repo_sos(self):
        return self.repo_sos

    def get_all_sos_paths(self):  # TODO: get_all_repo_sos_paths()
        return self.sos_local_paths  # TODO
