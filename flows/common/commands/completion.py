"""Get info for completion
"""

_command = {'help': 'Get info for completion',
            'params': [{'name': 'cmd', 'help': "Command name to get it's params", 'default': 'None'}],
            'silent': True}


def run(core):

    if core.args.cmd == "None":
        for cmd in core.flows.get_commands():
            print(cmd["name"])
    else:
        for param in core.flows.get_params_of_command(core.args.cmd):
            print(param["name"])

    return 0
