"""Tool handler for generate_document — creates DOCX/XLSX from artifacts."""

from __future__ import annotations

import hashlib
import tempfile
from pathlib import Path
from typing import Any

import structlog

from app.core.artifacts.exporters.docx_exporter import (
    _SUPPORTED_TYPES as DOCX_TYPES,
)
from app.core.artifacts.exporters.docx_exporter import (
    docx_exporter,
)
from app.core.artifacts.exporters.xlsx_exporter import (
    _SUPPORTED_TYPES as XLSX_TYPES,
)
from app.core.artifacts.exporters.xlsx_exporter import (
    xlsx_exporter,
)
from app.core.tools.registry import ToolDefinition, tool_registry
from app.models.artifact import ArtifactType

logger = structlog.get_logger()

_GENERATED_DIR = Path(tempfile.gettempdir()) / "vc_copilot_generated"
_GENERATED_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

GENERATE_DOCUMENT_DEF = ToolDefinition(
    name="generate_document",
    description=(
        "Generate a professional Word (.docx) or Excel (.xlsx) document "
        "from an existing artifact. Automatically picks the right format "
        "based on artifact type."
    ),
    input_schema={
        "type": "object",
        "required": ["artifact_id"],
        "properties": {
            "artifact_id": {
                "type": "string",
                "description": "UUID of the artifact to export",
            },
            "format_override": {
                "type": "string",
                "enum": ["docx", "xlsx"],
                "description": (
                    "Force a specific format. If omitted, "
                    "the best format is chosen automatically."
                ),
            },
        },
    },
)


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------


async def handle_generate_document(
    tool_input: dict[str, Any],
    executor: Any,
) -> dict[str, Any]:
    """Generate DOCX or XLSX from an artifact."""
    from sqlalchemy import select

    from app.models.artifact import Artifact

    artifact_id = tool_input.get("artifact_id", "")
    fmt_override = tool_input.get("format_override")

    stmt = select(Artifact).where(Artifact.id == artifact_id)
    result = await executor.db.execute(stmt)
    artifact = result.scalar_one_or_none()

    if artifact is None:
        return {"error": f"Artifact {artifact_id} not found"}

    # Determine format
    atype: ArtifactType = artifact.type
    if fmt_override:
        fmt = fmt_override
    elif atype in XLSX_TYPES:
        fmt = "xlsx"
    elif atype in DOCX_TYPES:
        fmt = "docx"
    else:
        return {
            "error": (
                f"No document exporter for {atype.value}. "
                f"Supported docx: "
                f"{', '.join(t.value for t in DOCX_TYPES)}. "
                f"Supported xlsx: "
                f"{', '.join(t.value for t in XLSX_TYPES)}."
            ),
        }

    try:
        if fmt == "xlsx":
            doc_bytes = xlsx_exporter.export(
                atype, artifact.title, artifact.content,
            )
            ext = "xlsx"
        else:
            doc_bytes = docx_exporter.export(
                atype, artifact.title, artifact.content,
            )
            ext = "docx"
    except Exception as exc:
        logger.error("document_generation_failed", error=str(exc))
        return {"error": f"Document generation failed: {exc}"}

    file_hash = hashlib.sha256(doc_bytes[:256]).hexdigest()[:12]
    safe_title = artifact.title[:40].replace(" ", "_")
    filename = f"{safe_title}_{file_hash}.{ext}"
    filepath = _GENERATED_DIR / filename
    filepath.write_bytes(doc_bytes)

    logger.info(
        "document_generated",
        artifact_id=artifact_id,
        filename=filename,
        format=ext,
        size_bytes=len(doc_bytes),
    )

    return {
        "status": "success",
        "filename": filename,
        "format": ext,
        "download_url": f"/api/v1/artifacts/downloads/{filename}",
        "size_bytes": len(doc_bytes),
    }


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def register_document_tools() -> None:
    """Register document generation tools."""
    tool_registry.register(
        GENERATE_DOCUMENT_DEF,
        handle_generate_document,
    )
