"""Demo command **info**
"""

_command = {'help': "Project's information", 'params': None, 'flags': [{'name': 'v', 'help': 'Version of Odin'}]}


def run(core):
    print("Global vars:")
    print("\n".join(["\t{} = {}".format(var, core.glob_vars[var]) for var in core.glob_vars]))
    print()
    print("Project info:")
    print("\tName:", core.project._name)
    print("\tVariables:")
    print("\n".join(["\t\t${} = {}".format(var, core.project._variables[var]) for var in core.project._variables]))
    print("\tModules:")
    if bool(core.project._modules):
        print("\n".join(["\t\t{}".format(mod['name']) for mod in core.project._modules]))
    else:
        print("\t\tNo modules in this project")

    if core.args.v:
        print("Odin Version: 2.0.0")

    return 0
