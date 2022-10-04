'''
Create work directory for Cliosoft SoS

Author: Konstantin Pankov <kpankov@quantenna.com>

Details:
Run 'ProjectCreateWorkarea -p <project_name> -d <dir_name> -u <user_name> -l USCA41'
'''

from core.vcs_sos import VcsSos

_command = {'help': 'Create SoS workareas. Prepare release.xml first.', 'params': None}


def run(data):
    print("# New workareas for projects:")
    for wa in data.release.get_all_sos_paths():
        print('\t> {}'.format(data.project.replace_variables(wa)))
        VcsSos(data.project.replace_variables(wa)).create_workarea(data.project.get_user_name())
    return 0
