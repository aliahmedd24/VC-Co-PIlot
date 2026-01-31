"""Vision analyzer tool for on-demand image analysis.

This tool enables agents to analyze images from documents, including:
- Pitch deck slides
- Charts and graphs
- Screenshots
- OCR from scanned documents
"""

import logging

from app.config import settings
from app.core.tools.base import BaseTool, ToolDefinition, ToolResult
from app.services.storage import get_storage_service
from app.services.vision import VisionAnalyzer

logger = logging.getLogger(__name__)


class VisionAnalyzerTool(BaseTool):
    """Analyze visual content from documents using Claude's vision capabilities.

    This tool allows agents to request vision analysis of specific pages
    or images from documents. It's useful for:
    - Analyzing pitch deck slides for content and design quality
    - Understanding charts and extracting metrics
    - OCR on scanned documents
    - Competitor screenshot analysis
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition for Claude."""
        return ToolDefinition(
            name="analyze_image",
            description=(
                "Analyze visual content from a document using Claude's vision capabilities. "
                "Use this to examine pitch deck slides, charts, diagrams, or perform OCR on scanned documents. "
                "Requires a document_id and page_number or visual_content_id. "
                "Returns detailed analysis including extracted text, metrics, design quality, and insights."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "ID of the document containing the visual content"
                    },
                    "page_number": {
                        "type": "number",
                        "description": "Page number to analyze (1-indexed). Used if visual_content_id not provided."
                    },
                    "visual_content_id": {
                        "type": "string",
                        "description": "Direct ID of VisualContent record (alternative to document_id + page_number)"
                    },
                    "analysis_type": {
                        "type": "string",
                        "enum": ["pitch_deck", "chart", "ocr", "competitor", "table", "general"],
                        "description": (
                            "Type of analysis to perform: "
                            "'pitch_deck' for slide analysis with design critique, "
                            "'chart' for data extraction from graphs, "
                            "'ocr' for text extraction, "
                            "'competitor' for UI/UX analysis, "
                            "'table' for structured data extraction, "
                            "'general' for basic image description"
                        ),
                        "default": "general"
                    },
                    "custom_prompt": {
                        "type": "string",
                        "description": "Optional custom analysis prompt to override default prompts"
                    }
                },
                "required": ["document_id"]
            }
        )

    async def execute(
        self,
        document_id: str,
        page_number: int | None = None,
        visual_content_id: str | None = None,
        analysis_type: str = "general",
        custom_prompt: str | None = None,
        **context
    ) -> ToolResult:
        """Execute vision analysis on a document image.

        Args:
            document_id: ID of document
            page_number: Page number (1-indexed)
            visual_content_id: Direct visual content ID
            analysis_type: Type of analysis
            custom_prompt: Optional custom prompt
            **context: Must include 'brain' for database access

        Returns:
            ToolResult with vision analysis
        """
        # Check if vision is enabled
        if not settings.vision_enabled:
            return ToolResult(
                tool_name="analyze_image",
                success=False,
                error="Vision capabilities are not enabled. Set VISION_ENABLED=true in configuration.",
                result={}
            )

        # Get brain from context
        brain = context.get("brain")
        if not brain:
            return ToolResult(
                tool_name="analyze_image",
                success=False,
                error="Brain context not provided. Vision analysis requires database access.",
                result={}
            )

        try:
            # Import models here to avoid circular dependencies
            from sqlalchemy import select
            from app.models.visual_content import VisualContent
            from app.models.document import Document

            # Get database session
            session = brain.db

            # Find the visual content
            if visual_content_id:
                # Direct lookup by ID
                result = await session.execute(
                    select(VisualContent).where(VisualContent.id == visual_content_id)
                )
                visual_content = result.scalar_one_or_none()

                if not visual_content:
                    return ToolResult(
                        tool_name="analyze_image",
                        success=False,
                        error=f"Visual content not found: {visual_content_id}",
                        result={}
                    )

            elif page_number is not None:
                # Lookup by document + page number
                result = await session.execute(
                    select(VisualContent).where(
                        VisualContent.document_id == document_id,
                        VisualContent.page_number == page_number
                    )
                )
                visual_content = result.scalar_one_or_none()

                if not visual_content:
                    return ToolResult(
                        tool_name="analyze_image",
                        success=False,
                        error=f"No visual content found for document {document_id}, page {page_number}. "
                              f"Document may not have been processed with vision yet.",
                        result={}
                    )

            else:
                # Need either visual_content_id or page_number
                return ToolResult(
                    tool_name="analyze_image",
                    success=False,
                    error="Must provide either 'visual_content_id' or 'page_number'",
                    result={}
                )

            # Check if we can use cached analysis
            if visual_content.vision_analysis and not custom_prompt:
                cached_analysis = visual_content.vision_analysis
                logger.info(
                    f"Using cached vision analysis for visual_content {visual_content.id}"
                )

                return ToolResult(
                    tool_name="analyze_image",
                    success=True,
                    result={
                        "content": cached_analysis.get("content", ""),
                        "analysis_type": cached_analysis.get("analysis_type", analysis_type),
                        "page_number": visual_content.page_number,
                        "content_type": visual_content.content_type.value,
                        "cached": True
                    },
                    citations=[
                        {
                            "snippet": f"Vision analysis of page {visual_content.page_number}",
                            "source": f"document:{document_id}",
                            "relevance": 1.0
                        }
                    ]
                )

            # Need to perform fresh analysis - download image
            storage = get_storage_service()
            image_bytes = await storage.download_file(visual_content.storage_key)

            # Analyze with vision
            vision_analyzer = VisionAnalyzer()

            if analysis_type == "pitch_deck":
                analysis_result = await vision_analyzer.analyze_pitch_deck_slide(
                    image_bytes,
                    slide_number=visual_content.page_number,
                    media_type="image/png"
                )
            elif analysis_type == "chart":
                analysis_result = await vision_analyzer.analyze_financial_chart(
                    image_bytes,
                    media_type="image/png"
                )
            elif analysis_type == "ocr":
                analysis_result = await vision_analyzer.perform_ocr(
                    image_bytes,
                    structured=True,
                    media_type="image/png"
                )
            elif analysis_type == "competitor":
                analysis_result = await vision_analyzer.analyze_competitor_screenshot(
                    image_bytes,
                    media_type="image/png"
                )
            elif analysis_type == "table":
                analysis_result = await vision_analyzer.analyze_table(
                    image_bytes,
                    media_type="image/png"
                )
            else:  # general
                analysis_result = await vision_analyzer.analyze_general(
                    image_bytes,
                    custom_prompt=custom_prompt,
                    media_type="image/png"
                )

            # Update visual content with new analysis if not custom prompt
            if not custom_prompt:
                visual_content.vision_analysis = {
                    "content": analysis_result["content"],
                    "usage": analysis_result.get("usage", {}),
                    "analysis_type": analysis_type,
                }
                await session.commit()

            logger.info(
                f"Performed fresh vision analysis for visual_content {visual_content.id} "
                f"(type: {analysis_type})"
            )

            return ToolResult(
                tool_name="analyze_image",
                success=True,
                result={
                    "content": analysis_result["content"],
                    "analysis_type": analysis_type,
                    "page_number": visual_content.page_number,
                    "content_type": visual_content.content_type.value,
                    "usage": analysis_result.get("usage", {}),
                    "cached": False
                },
                citations=[
                    {
                        "snippet": f"Vision analysis of page {visual_content.page_number}",
                        "source": f"document:{document_id}",
                        "relevance": 1.0
                    }
                ]
            )

        except Exception as e:
            logger.error(f"Vision analysis failed: {str(e)}")
            return ToolResult(
                tool_name="analyze_image",
                success=False,
                error=f"Vision analysis error: {str(e)}",
                result={}
            )


# Register the tool on import
from app.core.tools.registry import tool_registry
tool_registry.register(VisionAnalyzerTool())
