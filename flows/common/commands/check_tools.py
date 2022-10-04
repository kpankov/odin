"""Show and check tools
"""

import logging

from core.logger import Logger

_command = {'help': 'Show and check tools',
            'params': [{'name': 'open', 'help': 'Open tool', 'default': 'None'},
                       {'name': 'group', 'help': 'Open tool from selected group', 'default': 'None'},
                       {'name': 'params', 'help': 'Params for tool to open', 'default': 'None'}]}

logger = logging.getLogger(__name__)


def run(core):
    if core.args.open != "None":
        if core.args.group == "None":
            tool = core.get_tool(core.args.open)
        else:
            tool = core.get_tool(core.args.open, core.args.group)
        if tool is None:
            Logger.fatal("No such tool!")
        tool.setup()
        print("Starting", tool.executable, "...")
        if tool.lsf_only:
            tool_lsf = core.get_tool("LSF", core.args.group)
            if tool_lsf is not None:
                tool_lsf.setup()
            else:
                logger.warning("You are trying to start LSF-only tool, but Odin can't find LSF tool in tool gruop '{}'!".format(core.args.group))

        if core.args.params == "None":
            run_line, exit_code, stdout, stderr = tool.run(stdout_capture=True)
        else:
            # run_line, exit_code, stdout, stderr = tool.run(params=core.args.params, stdout_capture=True)
            run_line, exit_code, stdout, stderr = tool.run(params=core.args.params, stdout_capture=True)

        print("Run line: {}".format(run_line))
        print("Exit code: {}".format(exit_code))
        print("stdout: {}".format(stdout))
        print("stderr: {}".format(stderr))
    else:
        Logger.info("Show and check tools")
        core.flows.get_tools().print_list()
        return 0
