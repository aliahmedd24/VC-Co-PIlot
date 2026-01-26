"""Entity extraction from text using Claude (stubbed for now)."""

from dataclasses import dataclass
from typing import Any

from app.models.kg_entity import KGEntityType


@dataclass
class ExtractedEntity:
    """An entity extracted from text."""

    type: KGEntityType
    data: dict[str, Any]
    confidence: float
    evidence_snippet: str


class EntityExtractor:
    """Extract structured entities from unstructured text.

    Currently uses keyword-based extraction. Full Claude-based
    extraction can be enabled by setting use_llm=True and providing
    an Anthropic client.
    """

    # Keyword patterns for each entity type
    PATTERNS: dict[KGEntityType, list[str]] = {
        KGEntityType.MARKET: ["market", "tam", "sam", "som", "industry", "sector"],
        KGEntityType.ICP: ["customer", "user", "buyer", "persona", "target"],
        KGEntityType.COMPETITOR: ["competitor", "alternative", "vs", "versus", "competing"],
        KGEntityType.PRODUCT: ["product", "feature", "solution", "platform", "app"],
        KGEntityType.TEAM_MEMBER: ["founder", "ceo", "cto", "team", "cofounder"],
        KGEntityType.METRIC: ["mrr", "arr", "revenue", "growth", "churn", "cac", "ltv"],
        KGEntityType.FUNDING_ASSUMPTION: ["raise", "funding", "round", "valuation", "dilution"],
        KGEntityType.RISK: ["risk", "threat", "challenge", "weakness", "concern"],
    }

    def __init__(self, use_llm: bool = False, anthropic_client: Any = None):
        self.use_llm = use_llm
        self.client = anthropic_client

    async def extract_entities(self, text: str) -> list[ExtractedEntity]:
        """Extract entities from text.

        Args:
            text: The text to extract entities from.

        Returns:
            List of extracted entities with confidence scores.
        """
        if self.use_llm and self.client:
            return await self._extract_with_llm(text)
        return self._extract_with_keywords(text)

    def _extract_with_keywords(self, text: str) -> list[ExtractedEntity]:
        """Simple keyword-based extraction."""
        entities: list[ExtractedEntity] = []
        lower_text = text.lower()
        sentences = text.split(".")

        for entity_type, keywords in self.PATTERNS.items():
            for keyword in keywords:
                if keyword in lower_text:
                    # Find sentence containing keyword
                    snippet = ""
                    for sentence in sentences:
                        if keyword in sentence.lower():
                            snippet = sentence.strip()
                            break

                    if snippet:
                        entities.append(
                            ExtractedEntity(
                                type=entity_type,
                                data={"extracted_text": snippet, "keyword_match": keyword},
                                confidence=0.4,  # Low confidence for keyword match
                                evidence_snippet=snippet[:200],
                            )
                        )
                        break  # One entity per type per extraction

        return entities

    async def _extract_with_llm(self, text: str) -> list[ExtractedEntity]:
        """LLM-based extraction using Claude.

        TODO: Implement when Anthropic client is available.
        """
        # Placeholder for LLM-based extraction
        # This would call Claude with a structured prompt to extract entities
        # For now, fall back to keyword extraction
        return self._extract_with_keywords(text)
