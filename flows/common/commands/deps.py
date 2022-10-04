"""Show dependencies
"""

_command = {'help': 'Show dependencies as graph', 'params': None}


def run(core):
    core.release.print_graph()
    print("Version:", core.release._version)
    return 0
