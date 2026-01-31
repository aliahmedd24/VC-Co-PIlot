"""Tool system for agent capabilities.

This module provides the tool infrastructure for agents to:
- Search the web for current information
- Perform mathematical calculations
- Extract structured entities from unstructured text
- Query the venture knowledge graph
- Analyze visual content with Claude's vision capabilities
- Extract structured data from charts and graphs

Import all tools to ensure they're registered in the global tool_registry.
"""

# Import base classes and registry
from app.core.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult
from app.core.tools.registry import tool_registry

# Import all tools to trigger their registration
# (Each tool registers itself on import via tool_registry.register())
from app.core.tools.calculator import CalculatorTool
from app.core.tools.chart_extractor import ChartDataExtractorTool
from app.core.tools.entity_extractor import EntityExtractionTool
from app.core.tools.kg_query import KGQueryTool
from app.core.tools.vision_analyzer import VisionAnalyzerTool
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
    "ChartDataExtractorTool",
    "EntityExtractionTool",
    "KGQueryTool",
    "VisionAnalyzerTool",
]
