"""Tool system for agent capabilities.

This module provides the tool infrastructure for agents to:
- Search the web for current information
- Perform mathematical calculations
- Extract structured entities from unstructured text
- Query the venture knowledge graph

Import all tools to ensure they're registered in the global tool_registry.
"""

# Import base classes and registry
from app.core.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from app.core.tools.registry import tool_registry

# Import all tools to trigger their registration
# (Each tool registers itself on import via tool_registry.register())
from app.core.tools.calculator import CalculatorTool
from app.core.tools.entity_extractor import EntityExtractionTool
from app.core.tools.kg_query import KGQueryTool
from app.core.tools.web_search import BraveSearchTool

__all__ = [
    # Base classes
    "BaseTool",
    "ToolDefinition",
    "ToolParameter",
    "ToolResult",
    # Registry
    "tool_registry",
    # Tools
    "BraveSearchTool",
    "CalculatorTool",
    "EntityExtractionTool",
    "KGQueryTool",
]
