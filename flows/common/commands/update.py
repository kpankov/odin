"""Update all VCS repositories
"""

from core.scoreboard import Scoreboard
from core.scoreboard import scoreboard_step
from core.vcs_sos import VcsSos

_command = {'help': 'Update all repositories according release.xml',
            'params': [{'name': 'VER', 'help': 'Version of release.xml', 'type': 'string', 'default': 'HEAD'}],
            'flags': [{'name': 'dry', 'help': 'Dry run'}]}


@scoreboard_step("update", "Updated")
def run(core):
    if core.args.dry:
        print('Dry run enabled')
    print("Cliosoft SoS part:")
    for repo in core.release.get_all_repo_sos():
        print("\tRepo " + repo.get_name())
        if not core.args.dry:
            VcsSos(core.project.replace_variables(repo.local_path)).update(core.project.replace_variables(repo.tag))
            VcsSos(core.project.replace_variables(repo.local_path)).populate()

    # print("Git part:")  # TODO: VAL-113

    # if Scoreboard(core).update_step("update", "Passed", "SoS are updated"):
    #     print("Scoreboard updated.")

    return 0
