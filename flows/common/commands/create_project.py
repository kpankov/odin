"""Creates project.yaml file based on existing
"""

_command = {'help': "Project's information", 'params': None}


def run(core):
    core.project.set_var("TEST123", "testtset")
    core.project.write_project_yaml("new.yaml")
    return 0
