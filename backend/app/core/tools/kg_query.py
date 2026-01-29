"""Knowledge Graph query tool for accessing venture knowledge.

This tool enables agents to search and retrieve structured entities
from the venture's knowledge graph.
"""

from app.core.tools.base import BaseTool, ToolDefinition, ToolResult
from app.models.kg_entity import KGEntityType


class KGQueryTool(BaseTool):
    """Query the venture's knowledge graph.

    This tool provides access to the structured knowledge graph containing
    entities like competitors, metrics, ICPs, team members, risks, and markets.
    It's useful for:
    - Finding existing information before web search
    - Retrieving confirmed facts about the venture
    - Getting structured data for analysis
    - Building on previously gathered intelligence
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition for Claude."""
        return ToolDefinition(
            name="query_knowledge_graph",
            description=(
                "Search the venture's knowledge graph for entities like competitors, metrics, "
                "ICPs, team members, risks, and markets. Use this FIRST before web search to "
                "find existing information. Returns structured entity data with confidence scores. "
                "Each entity has type, data (JSON), confidence (0-1), and status (confirmed, needs_review, etc.)"
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": (
                            "Search query to match against entity data. Use keywords like company names, "
                            "metric names, person names, etc. Leave empty to get all entities of specified types."
                        )
                    },
                    "entity_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["competitor", "metric", "icp", "team_member", "risk", "market", "product", "funding_assumption"]
                        },
                        "description": "Filter by entity types. If not specified, searches all types."
                    }
                },
                "required": ["query"]
            }
        )

    async def execute(self, query: str, entity_types: list[str] | None = None, **context) -> ToolResult:
        """Execute a knowledge graph query.

        Args:
            query: Search query (keywords to match)
            entity_types: Optional list of entity types to filter
            **context: Must include 'brain' (StartupBrain instance)

        Returns:
            ToolResult with list of matching entities
        """
        # Get brain from context
        brain = context.get("brain")
        if not brain:
            return ToolResult(
                tool_name="query_knowledge_graph",
                success=False,
                error="Brain context not provided. This tool requires access to the knowledge graph.",
                result=[]
            )

        # Convert entity type strings to enums
        type_enums = None
        if entity_types:
            try:
                type_enums = [KGEntityType(t.upper()) for t in entity_types]
            except ValueError as e:
                return ToolResult(
                    tool_name="query_knowledge_graph",
                    success=False,
                    error=f"Invalid entity type: {str(e)}",
                    result=[]
                )

        try:
            # Search the knowledge graph
            entities = await brain.kg.search_entities(
                query=query,
                types=type_enums,
                include_suggested=True  # Include all entities for agent consideration
            )

            # Format results for the LLM
            formatted_entities = []
            for entity in entities:
                formatted_entity = {
                    "type": entity.type.value,
                    "data": entity.data,
                    "confidence": entity.confidence,
                    "status": entity.status.value,
                    "id": entity.id
                }
                formatted_entities.append(formatted_entity)

            # Create a readable summary for the result
            if not formatted_entities:
                result_text = f"No entities found matching '{query}'"
                if entity_types:
                    result_text += f" of types: {', '.join(entity_types)}"
            else:
                result_text = f"Found {len(formatted_entities)} entities:\n\n"
                for i, ent in enumerate(formatted_entities[:10], 1):  # Limit to first 10 for readability
                    ent_data = ent["data"]
                    # Try to extract a name/title field
                    name = ent_data.get("name") or ent_data.get("title") or ent_data.get("segment") or "Unnamed"
                    result_text += f"{i}. [{ent['type']}] {name} (confidence: {ent['confidence']:.2f}, status: {ent['status']})\n"
                    result_text += f"   Data: {str(ent_data)[:200]}...\n\n"

                if len(formatted_entities) > 10:
                    result_text += f"\n... and {len(formatted_entities) - 10} more entities."

            return ToolResult(
                tool_name="query_knowledge_graph",
                success=True,
                result=formatted_entities,  # Return structured data
                metadata={
                    "query": query,
                    "entity_count": len(formatted_entities),
                    "types_requested": entity_types or "all",
                    "summary": result_text  # Human-readable summary
                }
            )

        except Exception as e:
            return ToolResult(
                tool_name="query_knowledge_graph",
                success=False,
                error=f"Knowledge graph query error: {str(e)}",
                result=[]
            )


# Register the tool on import
from app.core.tools.registry import tool_registry
tool_registry.register(KGQueryTool())
