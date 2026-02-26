"""Tool handler for generate_presentation — creates PPTX from deck_outline artifacts."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any

import structlog

from app.core.artifacts.exporters.pptx_exporter import pptx_exporter
from app.core.tools.registry import ToolDefinition, tool_registry
from app.models.artifact import ArtifactType

logger = structlog.get_logger()

# Persistent temp dir for generated files (survives across requests)
_GENERATED_DIR = Path(tempfile.gettempdir()) / "vc_copilot_generated"
_GENERATED_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

GENERATE_PRESENTATION_DEF = ToolDefinition(
    name="generate_presentation",
    description=(
        "Generate a professional PPTX presentation from an existing "
        "deck_outline artifact. Returns a download URL for the file."
    ),
    input_schema={
        "type": "object",
        "required": ["artifact_id"],
        "properties": {
            "artifact_id": {
                "type": "string",
                "description": "UUID of the deck_outline artifact",
            },
        },
    },
)


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


async def handle_generate_presentation(
    tool_input: dict[str, Any],
    executor: Any,
) -> dict[str, Any]:
    """Generate PPTX from a deck_outline artifact."""
    from sqlalchemy import select

    from app.models.artifact import Artifact

    artifact_id = tool_input.get("artifact_id", "")

    # Load artifact from database
    stmt = select(Artifact).where(Artifact.id == artifact_id)
    result = await executor.db.execute(stmt)
    artifact = result.scalar_one_or_none()

    if artifact is None:
        return {"error": f"Artifact {artifact_id} not found"}

    if artifact.type != ArtifactType.DECK_OUTLINE:
        return {
            "error": (
                f"Expected deck_outline artifact, "
                f"got {artifact.type.value}"
            ),
        }

    slides = artifact.content.get("slides", [])
    if not slides:
        return {"error": "Artifact has no slides"}

    try:
        pptx_bytes = pptx_exporter.export(
            artifact_type=ArtifactType.DECK_OUTLINE,
            title=artifact.title,
            content=artifact.content,
        )
    except Exception as exc:
        logger.error("pptx_generation_failed", error=str(exc))
        return {"error": f"PPTX generation failed: {exc}"}

    # Save to temp storage
    file_hash = hashlib.sha256(pptx_bytes[:256]).hexdigest()[:12]
    filename = f"{artifact.title[:40].replace(' ', '_')}_{file_hash}.pptx"
    filepath = _GENERATED_DIR / filename
    filepath.write_bytes(pptx_bytes)

    logger.info(
        "presentation_generated",
        artifact_id=artifact_id,
        filename=filename,
        size_bytes=len(pptx_bytes),
        slide_count=len(slides),
    )

    return {
        "status": "success",
        "filename": filename,
        "download_url": f"/api/v1/artifacts/downloads/{filename}",
        "slide_count": len(slides),
        "size_bytes": len(pptx_bytes),
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_presentation_tools() -> None:
    """Register presentation generation tools."""
    tool_registry.register(
        GENERATE_PRESENTATION_DEF,
        handle_generate_presentation,
    )
