"""Central registry for all available tools.

The ToolRegistry provides a singleton pattern for managing all tools
available to agents. Tools are registered once and can be retrieved
and executed by name.
"""

from typing import Optional
from app.core.tools.base import BaseTool, ToolDefinition, ToolResult


class ToolRegistry:
    """Central registry for all available tools.

    This class maintains a dictionary of all registered tools and provides
    methods to register, retrieve, and execute tools by name.

    Usage:
        # Register a tool
        tool_registry.register(MyTool())

        # Get tool definitions for Claude
        definitions = tool_registry.get_definitions(["web_search", "calculator"])

        # Execute a tool
        result = await tool_registry.execute("web_search", query="AI startups", count=5)
    """

    def __init__(self):
        """Initialize an empty tool registry."""
        self._tools: dict[str, BaseTool] = {}

    def register(self, tool: BaseTool):
        """Register a tool in the registry.

        Args:
            tool: The tool instance to register

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        tool_name = tool.definition.name
        if tool_name in self._tools:
            raise ValueError(f"Tool '{tool_name}' is already registered")
        self._tools[tool_name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        """Retrieve a tool by name.

        Args:
            name: The name of the tool to retrieve

        Returns:
            The tool instance, or None if not found
        """
        return self._tools.get(name)

    def get_definitions(self, tool_names: list[str]) -> list[ToolDefinition]:
        """Get tool definitions for a list of tool names.

        This is used to provide Claude with the list of available tools
        and their schemas.

        Args:
            tool_names: List of tool names to get definitions for

        Returns:
            List of ToolDefinition objects for the requested tools
            (skips any tools that don't exist)
        """
        definitions = []
        for name in tool_names:
            tool = self._tools.get(name)
            if tool:
                definitions.append(tool.definition)
        return definitions

    async def execute(self, name: str, **kwargs) -> ToolResult:
        """Execute a tool by name with the given parameters.

        Args:
            name: The name of the tool to execute
            **kwargs: Parameters to pass to the tool's execute method

        Returns:
            ToolResult with the execution result or error
        """
        tool = self.get(name)
        if not tool:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Tool not found: {name}",
                result=None
            )

        try:
            return await tool.execute(**kwargs)
        except Exception as e:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Tool execution error: {str(e)}",
                result=None
            )

    def list_tools(self) -> list[str]:
        """Get a list of all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())


# Global registry instance
# Tools register themselves on import by calling tool_registry.register()
tool_registry = ToolRegistry()
