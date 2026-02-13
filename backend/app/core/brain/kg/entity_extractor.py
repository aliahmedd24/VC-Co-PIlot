import json
from typing import Any

import structlog
from anthropic import Anthropic

from app.config import settings

logger = structlog.get_logger()

EXTRACTION_SYSTEM_PROMPT = """You are an entity extraction specialist for venture capital analysis.
Given document text from a startup, extract structured entities.

Entity types you should extract:
- market: Market segments, TAM/SAM/SOM data, market trends
- icp: Ideal Customer Profile descriptions
- competitor: Competitor names and details
- product: Product features, capabilities, tech stack
- team_member: Team member names, roles, background
- metric: Key metrics (revenue, users, growth rates)
- funding_assumption: Financial assumptions, burn rate, runway
- risk: Identified risks and challenges

For each entity, return:
- "type": one of the entity types above
- "data": an object with a "name" key (string) and any other relevant fields
- "confidence": a float from 0.0 to 1.0 indicating extraction confidence

Return ONLY a valid JSON array. No markdown, no explanation. Example:
[
  {"type": "competitor", "data": {"name": "Acme Corp"}, "confidence": 0.85},
  {"type": "metric", "data": {"name": "Monthly Revenue"}, "confidence": 0.9}
]

If no entities can be extracted, return an empty array: []
"""


class EntityExtractor:
    """Claude-based structured entity extraction from document text.

    This is a sync service intended to be called from Celery workers.
    """

    def __init__(self) -> None:
        self.client: Anthropic | None = None

    def _get_client(self) -> Anthropic:
        """Lazy-init the Anthropic client."""
        if self.client is None:
            self.client = Anthropic(api_key=settings.anthropic_api_key)
        return self.client

    def extract_from_text(self, text: str) -> list[dict[str, Any]]:
        """Send text to Claude for structured entity extraction.

        Returns list of extracted entity dicts. Handles invalid JSON
        gracefully by returning empty list and logging a warning.
        """
        if not text.strip():
            return []

        client = self._get_client()
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=EXTRACTION_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": text[:50000]}],
        )

        content_block = response.content[0]
        raw: str = content_block.text  # type: ignore[union-attr]

        try:
            entities = json.loads(raw)
            if not isinstance(entities, list):
                raise ValueError("Expected JSON array")
            logger.info("entities_extracted", count=len(entities))
            result: list[dict[str, Any]] = entities
            return result
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(
                "entity_extraction_invalid_json",
                error=str(exc),
                raw_preview=raw[:200],
            )
            return []


entity_extractor = EntityExtractor()
