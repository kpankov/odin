'''
Closes all GUI for Cliosoft SoS

Author: Konstantin Pankov <kpankov@quantenna.com>

Details:
Run 'exitsos'
'''

from core.vcs_sos import VcsSos

_command = {'help': 'Closes all GUI for Cliosoft SoS', 'params': None}

def run(data):
    for wa in data.release.get_all_sos_paths():
        VcsSos(data.project.replace_variables(wa)).exit()
    return 0
