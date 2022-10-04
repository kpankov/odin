from core.merger import merge_files_new

_command = {'help': '3-way merge. See exit code for success megre or not (0 - success).', 'params': [{'name': 'my', 'help': '"My" file', 'type': 'string', 'default': 'None'}, {'name': 'base', 'help': '"Base" file', 'type': 'string', 'default': 'None'}, {'name': 'other', 'help': '"Other" file', 'type': 'string', 'default': 'None'}, {'name': 'output', 'help': 'Merged file', 'type': 'string', 'default': 'None'}]}

def run(core):
    return merge_files_new(core.args.my, core.args.base, core.args.other, core.args.output)
