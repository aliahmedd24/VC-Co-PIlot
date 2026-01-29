"""Entity extraction tool using LLM for structured data extraction.

This tool enables agents to extract structured entities (competitors, metrics,
ICPs, team members, risks, markets) from unstructured text.
"""

import json
from app.core.tools.base import BaseTool, ToolDefinition, ToolResult
from app.core.agents.llm_client import get_llm_client


class EntityExtractionTool(BaseTool):
    """Extract structured entities from text using Claude.

    This tool uses Claude to extract structured information from unstructured
    text and return it in a standardized JSON format. Useful for:
    - Extracting competitor info from research
    - Parsing metrics from documents
    - Identifying ICP characteristics
    - Finding team member information
    - Extracting risks and market data
    """

    def __init__(self):
        """Initialize the entity extraction tool."""
        self.client = get_llm_client("claude")

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition for Claude."""
        return ToolDefinition(
            name="extract_entities",
            description=(
                "Extract structured entities from unstructured text. Can extract: "
                "competitors (name, description, website, funding), "
                "metrics (name, value, unit, period), "
                "ICP data (segment, characteristics, pain points), "
                "team members (name, role, background), "
                "risks (type, description, impact, mitigation), "
                "market data (size, growth, trends). "
                "Returns JSON array with entity type, data, and confidence score."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to extract entities from (can be web search results, documents, etc.)"
                    },
                    "entity_types": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["competitor", "metric", "icp", "team_member", "risk", "market"]
                        },
                        "description": "Types of entities to extract from the text"
                    }
                },
                "required": ["text", "entity_types"]
            }
        )

    async def execute(self, text: str, entity_types: list[str], **kwargs) -> ToolResult:
        """Execute entity extraction.

        Args:
            text: Text to extract entities from
            entity_types: List of entity types to extract
            **kwargs: Additional context (unused)

        Returns:
            ToolResult with extracted entities as JSON
        """
        if not text or not text.strip():
            return ToolResult(
                tool_name="extract_entities",
                success=False,
                error="Empty text provided",
                result=[]
            )

        if not entity_types:
            return ToolResult(
                tool_name="extract_entities",
                success=False,
                error="No entity types specified",
                result=[]
            )

        # Build extraction prompt with examples
        entity_schemas = self._get_entity_schemas(entity_types)
        system_prompt = f"""Extract entities from the provided text. Return ONLY valid JSON.

Entity types to extract: {', '.join(entity_types)}

Expected JSON format:
[
  {{
    "type": "entity_type",
    "data": {{...entity-specific fields...}},
    "confidence": 0.0-1.0
  }}
]

Entity schemas:
{json.dumps(entity_schemas, indent=2)}

Rules:
- Return ONLY the JSON array, no additional text
- Only extract entities explicitly mentioned or strongly implied
- Set confidence based on how clear the information is (0.0-1.0)
- If no entities found, return empty array []
"""

        user_prompt = f"Extract {', '.join(entity_types)} entities from this text:\n\n{text}"

        try:
            response = await self.client.complete(
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                temperature=0.3,  # Lower temperature for more deterministic extraction
                max_tokens=2048
            )

            # Parse JSON response
            response_clean = response.strip()

            # Handle markdown code blocks if present
            if response_clean.startswith("```"):
                lines = response_clean.split("\n")
                response_clean = "\n".join(lines[1:-1])

            entities = json.loads(response_clean)

            # Validate structure
            if not isinstance(entities, list):
                raise ValueError("Response is not a JSON array")

            for entity in entities:
                if not isinstance(entity, dict):
                    raise ValueError("Entity is not a JSON object")
                if "type" not in entity or "data" not in entity or "confidence" not in entity:
                    raise ValueError("Entity missing required fields (type, data, confidence)")

            return ToolResult(
                tool_name="extract_entities",
                success=True,
                result=entities,
                metadata={
                    "entity_count": len(entities),
                    "types_requested": entity_types,
                    "types_found": list(set(e["type"] for e in entities))
                }
            )

        except json.JSONDecodeError as e:
            return ToolResult(
                tool_name="extract_entities",
                success=False,
                error=f"Failed to parse JSON response: {str(e)}. Response: {response[:200]}",
                result=[]
            )

        except Exception as e:
            return ToolResult(
                tool_name="extract_entities",
                success=False,
                error=f"Entity extraction error: {str(e)}",
                result=[]
            )

    def _get_entity_schemas(self, entity_types: list[str]) -> dict:
        """Get schema examples for requested entity types.

        Args:
            entity_types: List of entity types

        Returns:
            Dictionary mapping entity types to their schemas
        """
        all_schemas = {
            "competitor": {
                "name": "string (required)",
                "description": "string (what they do)",
                "website": "string (optional)",
                "funding": "string (optional, e.g., 'Series A, $10M')",
                "strengths": "string (optional)",
                "weaknesses": "string (optional)"
            },
            "metric": {
                "name": "string (required, e.g., 'Monthly Revenue', 'CAC')",
                "value": "number (required)",
                "unit": "string (optional, e.g., 'USD', 'users', '%')",
                "period": "string (optional, e.g., 'monthly', 'Q1 2024')",
                "trend": "string (optional, e.g., 'growing', 'flat')"
            },
            "icp": {
                "segment": "string (required, e.g., 'SMB SaaS companies')",
                "characteristics": "string (required, key traits)",
                "pain_points": "string (required, main problems)",
                "size": "string (optional, market size)",
                "willingness_to_pay": "string (optional)"
            },
            "team_member": {
                "name": "string (required)",
                "role": "string (required, e.g., 'CEO', 'CTO')",
                "background": "string (optional, previous experience)",
                "expertise": "string (optional, key skills)"
            },
            "risk": {
                "type": "string (required, e.g., 'market', 'technical', 'competitive')",
                "description": "string (required)",
                "impact": "string (required, 'low', 'medium', 'high')",
                "mitigation": "string (optional, how to address)"
            },
            "market": {
                "name": "string (required, market name)",
                "size": "string (optional, e.g., '$10B TAM')",
                "growth_rate": "string (optional, e.g., '15% CAGR')",
                "trends": "string (optional, key trends)",
                "stage": "string (optional, 'emerging', 'growing', 'mature')"
            }
        }

        return {etype: all_schemas[etype] for etype in entity_types if etype in all_schemas}


# Register the tool on import
from app.core.tools.registry import tool_registry
tool_registry.register(EntityExtractionTool())
