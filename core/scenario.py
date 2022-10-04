"""
Scenario module
"""

import logging
import os
from sys import modules

from core.core import Core

logger = logging.getLogger(__name__)


class Step:
    _name = 'unknown'

    def __init__(self):
        pass

    def get_name(self):
        return self._name

    def run(self):
        pass


class ShellCommand(Step):
    _name = 'shell'

    def __init__(self, command: str, name: str = None):
        self._run_line = command
        if name is not None:
            self._name = name

    def run(self):
        exit_code = os.system(self._run_line + " &")
        return exit_code


class OdinCommand(Step):
    _name = 'shell'

    def __init__(self, command: str, args: dict = None, name: str = None):
        self._command = command
        command_object = getattr(modules["flows." + Core().flows.get_flow_of_command(self._command) + ".commands"], self._command, None)
        if command_object is None:
            logger.error('No such command {}!'.format(self._command))
            os.abort()
        else:
            self._command_default_args = command_object._command

        if args is not None:
            self._args = args
            is_valid_arg = False
            for arg in self._args:
                if self._command_default_args.get('params', None) is not None:
                    for param in self._command_default_args['params']:
                        if arg == param['name']:
                            is_valid_arg = True
                if self._command_default_args.get('flags', None) is not None:
                    for flag in self._command_default_args['flags']:
                        if arg == flag['name']:
                            is_valid_arg = True
                if not is_valid_arg:
                    logger.error('No such param "{}" in command "{}"!'.format(arg, command))
                    os.abort()
        else:
            self._args = {}

        if self._command_default_args.get('params', None) is not None:
            for param in self._command_default_args['params']:
                if param['name'] not in self._args:
                    self._args[param['name']] = param['default']

        if self._command_default_args.get('flags', None) is not None:
            for flag in self._command_default_args['flags']:
                if flag['name'] not in self._args:
                    self._args[flag['name']] = False

        if name is not None:
            self._name = name

    def run(self):
        core = Core()
        backup = {}
        temporary = []
        if self._args is not None:
            for arg in self._args:
                if getattr(core.args, arg, None) is not None:
                    backup[arg] = getattr(core.args, arg)
                else:
                    temporary.append(arg)
                setattr(core.args, arg, self._args[arg])
        command = getattr(modules["flows." + Core().flows.get_flow_of_command(self._command) + ".commands"], self._command)
        res = command.run(Core())
        for arg in backup:
            setattr(core.args, arg, backup[arg])
        for arg in temporary:
            delattr(core.args, arg)
        return res


class Scenario:
    def __init__(self):
        self._steps = []

    def add_step(self, step):
        self._steps.append(step)

    def run(self):
        for step in self._steps:
            print(' Run step "{}" '.format(step.get_name()).center(80, '-'))
            res = step.run()
            if res != 0:
                print('Command {} failed!'.format(step.get_name()))
                logger.error('Command failed!'.format(step.get_name()))
                break
            print(' End step "{}" '.format(step.get_name()).center(80, '-'))
