from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from app.models.artifact import ArtifactType

TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates" / "artifacts"


class MarkdownExporter:
    """Render artifact content as Markdown using Jinja2 templates."""

    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=False,
            keep_trailing_newline=True,
        )

    def export(
        self, artifact_type: ArtifactType, title: str, content: dict[str, Any]
    ) -> str:
        """Render artifact content to Markdown string."""
        template_name = f"{artifact_type.value}.md.j2"
        template = self.env.get_template(template_name)
        return template.render(title=title, **content)


markdown_exporter = MarkdownExporter()
