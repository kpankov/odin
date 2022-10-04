import logging
from core.scenario import Scenario
from core.scenario import ShellCommand
from core.scenario import OdinCommand

logger = logging.getLogger(__name__)

_command = {'help': "Scenario sample", 'params': []}


def run(core):
    scene = Scenario()
    scene.add_step(ShellCommand(command='pwd', name='init'))
    scene.add_step(OdinCommand(command='info', name='info'))
    scene.add_step(OdinCommand(command='info', args={'v': True}, name='info2'))
    scene.run()
