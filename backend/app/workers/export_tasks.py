"""Export tasks for generating Markdown and PDF artifacts."""

import json
from datetime import datetime
from typing import Any

from app.workers.celery_app import celery_app


def _artifact_to_markdown(
    artifact_data: dict[str, Any],
    include_versions: bool = False,
) -> str:
    """Convert artifact data to Markdown format."""
    md_parts = []

    # Header
    md_parts.append(f"# {artifact_data['title']}")
    md_parts.append("")
    md_parts.append(f"**Type:** {artifact_data['type']}")
    md_parts.append(f"**Status:** {artifact_data['status']}")
    md_parts.append(f"**Owner:** {artifact_data['owner_agent']}")
    md_parts.append(f"**Created:** {artifact_data['created_at']}")
    md_parts.append(f"**Updated:** {artifact_data['updated_at']}")
    md_parts.append("")
    md_parts.append("---")
    md_parts.append("")

    # Content
    md_parts.append("## Content")
    md_parts.append("")
    content = artifact_data.get("content", {})
    md_parts.append(_dict_to_markdown(content))
    md_parts.append("")

    # Assumptions
    if artifact_data.get("assumptions"):
        md_parts.append("## Assumptions")
        md_parts.append("")
        for i, assumption in enumerate(artifact_data["assumptions"], 1):
            if isinstance(assumption, dict):
                md_parts.append(f"{i}. {json.dumps(assumption)}")
            else:
                md_parts.append(f"{i}. {assumption}")
        md_parts.append("")

    # Version history
    if include_versions and artifact_data.get("versions"):
        md_parts.append("## Version History")
        md_parts.append("")
        for version in artifact_data["versions"]:
            md_parts.append(f"### Version {version['version']}")
            md_parts.append(f"- **Created by:** {version.get('created_by', 'Unknown')}")
            md_parts.append(f"- **Date:** {version['created_at']}")
            if version.get("diff"):
                from app.core.artifacts.diff_engine import DiffEngine

                summary = DiffEngine.summarize_changes(version["diff"])
                md_parts.append(f"- **Changes:** {summary}")
            md_parts.append("")

    return "\n".join(md_parts)


def _dict_to_markdown(d: dict[str, Any], level: int = 0) -> str:
    """Convert a dictionary to Markdown format with nested sections."""
    parts = []
    indent = "  " * level

    for key, value in d.items():
        if isinstance(value, dict):
            parts.append(f"{indent}### {key.replace('_', ' ').title()}")
            parts.append(_dict_to_markdown(value, level + 1))
        elif isinstance(value, list):
            parts.append(f"{indent}**{key.replace('_', ' ').title()}:**")
            for item in value:
                if isinstance(item, dict):
                    parts.append(f"{indent}- {json.dumps(item)}")
                else:
                    parts.append(f"{indent}- {item}")
        else:
            parts.append(f"{indent}**{key.replace('_', ' ').title()}:** {value}")

    return "\n".join(parts)


def _markdown_to_pdf(markdown_content: str, output_path: str) -> str:
    """Convert Markdown to PDF using weasyprint."""
    import markdown
    from weasyprint import HTML

    # Convert Markdown to HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=["tables", "fenced_code"],
    )

    # Wrap in basic HTML structure with styles
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                max-width: 800px;
                margin: 40px auto;
                padding: 20px;
                color: #333;
            }}
            h1 {{ color: #1a1a2e; border-bottom: 2px solid #4a4a6a; padding-bottom: 10px; }}
            h2 {{ color: #2d2d44; margin-top: 30px; }}
            h3 {{ color: #4a4a6a; }}
            code {{ background: #f4f4f8; padding: 2px 6px; border-radius: 3px; }}
            pre {{ background: #f4f4f8; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background: #f4f4f8; }}
            hr {{ border: none; border-top: 1px solid #eee; margin: 30px 0; }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # Generate PDF
    HTML(string=full_html).write_pdf(output_path)

    return output_path


@celery_app.task(bind=True, max_retries=3)
def export_artifact_task(
    self,
    artifact_id: str,
    format: str,
    include_versions: bool = False,
) -> dict[str, Any]:
    """
    Background task to export an artifact.

    Args:
        artifact_id: The artifact to export
        format: Export format ('markdown' or 'pdf')
        include_versions: Whether to include version history

    Returns:
        Dict with export status and file path/URL
    """
    import asyncio

    return asyncio.run(
        _export_artifact_async(artifact_id, format, include_versions)
    )


async def _export_artifact_async(
    artifact_id: str,
    format: str,
    include_versions: bool,
) -> dict[str, Any]:
    """Async implementation of artifact export."""
    import tempfile
    from pathlib import Path

    from app.core.artifacts.manager import ArtifactManager
    from app.dependencies import get_db_context

    async with get_db_context() as db:
        manager = ArtifactManager(db)
        artifact = await manager.get_artifact(artifact_id, include_versions=include_versions)

        if not artifact:
            return {"status": "error", "message": "Artifact not found"}

        # Build artifact data dict
        artifact_data = {
            "id": artifact.id,
            "title": artifact.title,
            "type": artifact.type.value,
            "status": artifact.status.value,
            "owner_agent": artifact.owner_agent,
            "content": artifact.content,
            "assumptions": artifact.assumptions,
            "created_at": artifact.created_at.isoformat(),
            "updated_at": artifact.updated_at.isoformat(),
            "versions": [],
        }

        if include_versions and artifact.versions:
            artifact_data["versions"] = [
                {
                    "version": v.version,
                    "content": v.content,
                    "diff": v.diff,
                    "created_by": v.created_by,
                    "created_at": v.created_at.isoformat(),
                }
                for v in artifact.versions
            ]

        # Generate Markdown
        markdown_content = _artifact_to_markdown(artifact_data, include_versions)

        # Create output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c in "-_ " else "_" for c in artifact.title)
        filename = f"{safe_title}_{timestamp}"

        with tempfile.TemporaryDirectory() as tmpdir:
            if format == "markdown":
                output_path = Path(tmpdir) / f"{filename}.md"
                output_path.write_text(markdown_content, encoding="utf-8")
                file_ext = "md"
            elif format == "pdf":
                output_path = Path(tmpdir) / f"{filename}.pdf"
                _markdown_to_pdf(markdown_content, str(output_path))
                file_ext = "pdf"
            else:
                return {"status": "error", "message": f"Unknown format: {format}"}

            # Upload to storage
            from app.services.storage import StorageService

            storage = StorageService()
            storage_key = f"exports/{artifact_id}/{filename}.{file_ext}"

            with open(output_path, "rb") as f:
                await storage.upload_file(
                    file=f,
                    key=storage_key,
                    content_type="application/pdf" if format == "pdf" else "text/markdown",
                )

            download_url = await storage.get_download_url(storage_key)

            return {
                "status": "success",
                "artifact_id": artifact_id,
                "format": format,
                "storage_key": storage_key,
                "download_url": download_url,
            }
