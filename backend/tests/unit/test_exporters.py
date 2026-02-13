from unittest.mock import MagicMock, patch

from app.core.artifacts.exporters.markdown_exporter import MarkdownExporter
from app.models.artifact import ArtifactType


def test_markdown_export_lean_canvas() -> None:
    exporter = MarkdownExporter()
    content = {
        "problem": ["High CAC", "Low conversion"],
        "solution": ["AI outreach"],
        "key_metrics": ["MRR"],
        "unique_value_prop": "10x faster prospecting",
        "unfair_advantage": "Proprietary data",
        "channels": ["Direct sales"],
        "customer_segments": ["B2B SaaS"],
        "cost_structure": ["Cloud infra"],
        "revenue_streams": ["Subscriptions"],
    }
    result = exporter.export(ArtifactType.LEAN_CANVAS, "Test Canvas", content)

    assert "# Test Canvas" in result
    assert "High CAC" in result
    assert "AI outreach" in result
    assert "10x faster prospecting" in result
    assert "B2B SaaS" in result


def test_markdown_export_deck_outline() -> None:
    exporter = MarkdownExporter()
    content = {
        "slides": [
            {
                "title": "Problem",
                "key_points": ["Market pain", "User quotes"],
                "visual_suggestion": "Photo of user",
                "speaker_notes": "Emphasize pain",
            },
            {
                "title": "Solution",
                "key_points": ["Product demo"],
                "visual_suggestion": "",
                "speaker_notes": "",
            },
        ]
    }
    result = exporter.export(ArtifactType.DECK_OUTLINE, "Pitch Deck", content)

    assert "# Pitch Deck" in result
    assert "Slide 1: Problem" in result
    assert "Slide 2: Solution" in result
    assert "Market pain" in result
    assert "Product demo" in result


def test_pdf_export_produces_bytes() -> None:
    mock_pdf = MagicMock()
    mock_pdf.HTML.return_value.write_pdf.return_value = b"%PDF-1.4 mock content"

    with patch.dict("sys.modules", {"weasyprint": mock_pdf}):
        from app.core.artifacts.exporters.pdf_exporter import PDFExporter

        exporter = PDFExporter()
        # Use the real Jinja2 rendering, mock only weasyprint conversion
        template = exporter.env.get_template("lean_canvas.html.j2")
        html = template.render(
            title="Test",
            problem=["test"],
            solution=[],
            key_metrics=[],
            unique_value_prop="",
            unfair_advantage="",
            channels=[],
            customer_segments=[],
            cost_structure=[],
            revenue_streams=[],
        )
        assert "<h1>Test</h1>" in html
        assert "test" in html


def test_pdf_export_unicode_in_template() -> None:
    exporter = MarkdownExporter()
    content = {
        "problem": ["Hohe Kosten f\u00fcr Kundenakquise"],
        "solution": ["\u65e5\u672c\u8a9e\u306e\u30c6\u30b9\u30c8"],
        "key_metrics": [],
        "unique_value_prop": "\u00c9l\u00e9gance",
        "unfair_advantage": "",
        "channels": [],
        "customer_segments": [],
        "cost_structure": [],
        "revenue_streams": [],
    }
    result = exporter.export(ArtifactType.LEAN_CANVAS, "Unicode Test", content)
    assert "Hohe Kosten" in result
    assert "\u65e5\u672c\u8a9e" in result
    assert "\u00c9l\u00e9gance" in result
