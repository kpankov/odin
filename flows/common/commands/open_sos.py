'''
Open GUI for Cliosoft SoS repo

Author: Konstantin Pankov <kpankov@quantenna.com>

Details:
Run 'soscmd gui'
'''

from core.logger import Logger
from core.vcs_sos import VcsSos

_command = {'help': 'Open Cliosoft SoS GUI for all repositories or for selected one',
            'params': [{'name': 'proj', 'help': 'Project name (default all)', 'type': 'string', 'default': 'all'}]}


def run(data):
    if data.args.proj == "all":
        for wa in data.release.get_all_sos_paths():
            VcsSos(data.project.replace_variables(wa)).open_gui()
    else:
        print("Open SoS for", data.args.proj, "only...")
        repo = data.release.get_repo_sos(data.args.proj)
        if repo is not None:
            VcsSos(data.project.replace_variables(repo.local_path)).open_gui()
        else:
            Logger.fatal("No such repository!")
    return 0
