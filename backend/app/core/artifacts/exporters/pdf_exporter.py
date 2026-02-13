from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from app.models.artifact import ArtifactType

BASE_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "templates"
ARTIFACT_TEMPLATE_DIR = BASE_TEMPLATE_DIR / "artifacts"


class PDFExporter:
    """Render artifact content as PDF using Jinja2 HTML templates + weasyprint."""

    def __init__(self) -> None:
        self.env = Environment(
            loader=FileSystemLoader(
                [str(ARTIFACT_TEMPLATE_DIR), str(BASE_TEMPLATE_DIR)]
            ),
            autoescape=True,
            keep_trailing_newline=True,
        )

    def export(
        self, artifact_type: ArtifactType, title: str, content: dict[str, Any]
    ) -> bytes:
        """Render artifact content to PDF bytes."""
        import weasyprint

        template_name = f"{artifact_type.value}.html.j2"
        template = self.env.get_template(template_name)
        html = template.render(title=title, **content)
        pdf_bytes: bytes = weasyprint.HTML(string=html).write_pdf()
        return pdf_bytes


pdf_exporter = PDFExporter()
