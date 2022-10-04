
class Core:
    """
    Singleton Core class. It's just for encapsulate all core data classes into one.
    """

    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(Core, cls).__new__(cls)
        return cls.instance

    def set(self, project=None, release=None, flows=None, args=None, glob_vars=None) -> None:
        self.project = project
        self.release = release
        self.flows = flows
        self.args = args
        self.glob_vars = glob_vars

    def get_tool(self, tool_name, tool_group=None):
        """
        Faster way to call core.flows.get_tools().get_tool("tool_name")
        :return:
        Tool class instance
        """
        return self.flows.get_tools().get_tool(tool_name, tool_group)

    def get_tools_from_group(self, tool_group):
        """
        Faster way to call core.flows.get_tools().get_tools_from_group("tool_name")
        :return:
        Tool class instance
        """
        return self.flows.get_tools().get_tools_from_group(tool_group)

    def check_tool(self, tool_name, tool_group) -> bool:
        """
        Faster way to call core.flows.get_tools().check_tool("tool_name")
        :return:
        Bool value
        """
        return self.flows.get_tools().check_tool(tool_name, tool_group)
