import os
import unittest
import shutil
import time
import subprocess

from core.project import Project


class TestProject(unittest.TestCase):

    def test_000_get_user_name(self):
        print(" test_000_get_user_name() ".center(80, "-"))

        project = Project("../../flows/common/projects/sample_yaml/project.yaml", [])
        user_name = project.get_user_name()
        print("Odin's username: {}".format(user_name))
        if os.name == "nt":
            user_name_system = subprocess.getoutput("echo %username%")
        else:
            user_name_system = subprocess.getoutput("whoami")
        print("System username: {}".format(user_name_system))
        self.assertEqual(user_name, user_name_system)

    def test_010_get_project_file_type(self):
        print(" test_010_get_project_file_type() ".center(80, "-"))

        project_xml_path = "../../flows/common/projects/sample_xml/project.xml"
        project_yaml_path = "../../flows/common/projects/sample_yaml/project.yaml"
        project_yml_path = "../../flows/common/projects/sample_yaml/project.yml"

        project_xml = Project(project_xml_path, [])
        project_yaml = Project(project_yaml_path, [])
        shutil.copy(project_yaml_path, project_yml_path)
        project_yml = Project(project_yml_path, [])

        self.assertEqual(project_xml.get_project_file_type(), "xml")
        self.assertEqual(project_yaml.get_project_file_type(), "yaml")
        self.assertEqual(project_yml.get_project_file_type(), "yml")

        os.remove(project_yml_path)

    def test_020_load(self):
        print(" test_020_load() (failed) ".center(80, "-"))

        with self.assertRaises(IOError):
            project = Project("../../flows/common/projects/sample_yaml/project.abc", [])
