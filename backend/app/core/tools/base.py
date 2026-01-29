"""Base classes and models for tool system.

This module defines the core abstractions for the tool calling system,
including tool definitions, parameters, results, and the base tool interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Defines a parameter for a tool.

    Attributes:
        name: Parameter name
        type: JSON Schema type (string, number, boolean, object, array)
        description: Human-readable description of the parameter
        required: Whether this parameter is required
        enum: Optional list of allowed values
    """
    name: str
    type: str  # JSON Schema type: "string", "number", "boolean", "object", "array"
    description: str
    required: bool = True
    enum: Optional[list[str]] = None


class ToolDefinition(BaseModel):
    """Claude-compatible tool definition.

    This matches the format expected by Claude's tool use API.

    Attributes:
        name: Unique tool identifier
        description: What the tool does and when to use it
        input_schema: JSON Schema defining the tool's parameters
    """
    name: str
    description: str
    input_schema: dict[str, Any]  # JSON Schema format


class ToolResult(BaseModel):
    """Result from executing a tool.

    Attributes:
        tool_name: Which tool was executed
        success: Whether execution succeeded
        result: The actual result data (format varies by tool)
        error: Error message if execution failed
        citations: Source citations for the result (for web searches, etc.)
        metadata: Additional metadata about the execution
    """
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
    citations: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaseTool(ABC):
    """Abstract base class for all tools.

    Each tool must:
    1. Define its interface via the `definition` property
    2. Implement the `execute` method with its logic

    Tools are registered in the ToolRegistry and can be called by agents
    during their execution loop.
    """

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Return Claude-compatible tool definition.

        This defines the tool's name, description, and input schema.
        The schema should follow JSON Schema format.
        """
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters matching the input_schema

        Returns:
            ToolResult with success status, result data, and optional citations
        """
        pass
