"""Chart data extraction tool for structured data from visualizations.

This specialized tool focuses on extracting numerical data, metrics,
and structured information from charts, graphs, and financial visualizations.
"""

import json
import logging

from app.config import settings
from app.core.tools.base import BaseTool, ToolDefinition, ToolResult
from app.services.storage import get_storage_service
from app.services.vision import VisionAnalyzer

logger = logging.getLogger(__name__)


class ChartDataExtractorTool(BaseTool):
    """Extract structured numerical data from charts and graphs.

    This tool specializes in:
    - Identifying chart types (line, bar, pie, scatter, etc.)
    - Extracting all data points with precision
    - Extracting axes labels, units, and ranges
    - Calculating trends and growth rates
    - Returning structured, machine-readable data
    """

    @property
    def definition(self) -> ToolDefinition:
        """Return the tool definition for Claude."""
        return ToolDefinition(
            name="extract_chart_data",
            description=(
                "Extract structured numerical data from charts, graphs, and financial visualizations. "
                "Use this when you need precise numbers from visual charts in documents. "
                "Returns chart type, data series, axes information, and calculated metrics like growth rates. "
                "Best for financial projections, traction charts, market size graphs, and revenue charts."
            ),
            input_schema={
                "type": "object",
                "properties": {
                    "document_id": {
                        "type": "string",
                        "description": "ID of the document containing the chart"
                    },
                    "page_number": {
                        "type": "number",
                        "description": "Page number where the chart appears (1-indexed)"
                    },
                    "visual_content_id": {
                        "type": "string",
                        "description": "Direct ID of the VisualContent record (alternative to document_id + page_number)"
                    },
                    "data_only": {
                        "type": "boolean",
                        "description": "If true, extract only data points without analysis. Default false.",
                        "default": False
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
        data_only: bool = False,
        **context
    ) -> ToolResult:
        """Extract chart data from a document.

        Args:
            document_id: ID of document
            page_number: Page number (1-indexed)
            visual_content_id: Direct visual content ID
            data_only: Extract only data, skip analysis
            **context: Must include 'brain' for database access

        Returns:
            ToolResult with extracted chart data
        """
        # Check if vision is enabled
        if not settings.vision_enabled:
            return ToolResult(
                tool_name="extract_chart_data",
                success=False,
                error="Vision capabilities are not enabled. Set VISION_ENABLED=true in configuration.",
                result={}
            )

        # Get brain from context
        brain = context.get("brain")
        if not brain:
            return ToolResult(
                tool_name="extract_chart_data",
                success=False,
                error="Brain context not provided. Chart extraction requires database access.",
                result={}
            )

        try:
            # Import models
            from sqlalchemy import select
            from app.models.visual_content import VisualContent

            # Get database session
            session = brain.db

            # Find the visual content
            if visual_content_id:
                result = await session.execute(
                    select(VisualContent).where(VisualContent.id == visual_content_id)
                )
                visual_content = result.scalar_one_or_none()

                if not visual_content:
                    return ToolResult(
                        tool_name="extract_chart_data",
                        success=False,
                        error=f"Visual content not found: {visual_content_id}",
                        result={}
                    )

            elif page_number is not None:
                result = await session.execute(
                    select(VisualContent).where(
                        VisualContent.document_id == document_id,
                        VisualContent.page_number == page_number
                    )
                )
                visual_content = result.scalar_one_or_none()

                if not visual_content:
                    return ToolResult(
                        tool_name="extract_chart_data",
                        success=False,
                        error=f"No visual content found for document {document_id}, page {page_number}",
                        result={}
                    )

            else:
                return ToolResult(
                    tool_name="extract_chart_data",
                    success=False,
                    error="Must provide either 'visual_content_id' or 'page_number'",
                    result={}
                )

            # Check if we have cached chart data extraction
            if (visual_content.vision_analysis and
                visual_content.vision_analysis.get("analysis_type") == "chart" and
                not data_only):

                cached_content = visual_content.vision_analysis.get("content", "")

                logger.info(
                    f"Using cached chart analysis for visual_content {visual_content.id}"
                )

                return ToolResult(
                    tool_name="extract_chart_data",
                    success=True,
                    result={
                        "content": cached_content,
                        "extracted_data": visual_content.extracted_data or {},
                        "page_number": visual_content.page_number,
                        "cached": True
                    },
                    citations=[
                        {
                            "snippet": f"Chart data from page {visual_content.page_number}",
                            "source": f"document:{document_id}",
                            "relevance": 1.0
                        }
                    ],
                    metadata={
                        "chart_analysis": True,
                        "page": visual_content.page_number
                    }
                )

            # Need fresh analysis - download image
            storage = get_storage_service()
            image_bytes = await storage.download_file(visual_content.storage_key)

            # Analyze chart
            vision_analyzer = VisionAnalyzer()
            analysis_result = await vision_analyzer.analyze_financial_chart(
                image_bytes,
                data_only=data_only,
                media_type="image/png"
            )

            # Try to extract structured data from the response
            # This is a basic extraction - in production, could use structured output
            extracted_data = self._parse_chart_data(analysis_result["content"])

            # Update visual content
            visual_content.vision_analysis = {
                "content": analysis_result["content"],
                "usage": analysis_result.get("usage", {}),
                "analysis_type": "chart",
            }
            visual_content.extracted_data = extracted_data
            await session.commit()

            logger.info(
                f"Extracted chart data from visual_content {visual_content.id}"
            )

            return ToolResult(
                tool_name="extract_chart_data",
                success=True,
                result={
                    "content": analysis_result["content"],
                    "extracted_data": extracted_data,
                    "page_number": visual_content.page_number,
                    "usage": analysis_result.get("usage", {}),
                    "cached": False
                },
                citations=[
                    {
                        "snippet": f"Chart data extracted from page {visual_content.page_number}",
                        "source": f"document:{document_id}",
                        "relevance": 1.0
                    }
                ],
                metadata={
                    "chart_analysis": True,
                    "page": visual_content.page_number,
                    "data_points": len(extracted_data.get("series", []))
                }
            )

        except Exception as e:
            logger.error(f"Chart data extraction failed: {str(e)}")
            return ToolResult(
                tool_name="extract_chart_data",
                success=False,
                error=f"Chart extraction error: {str(e)}",
                result={}
            )

    def _parse_chart_data(self, analysis_text: str) -> dict:
        """Parse structured data from chart analysis text.

        This is a basic implementation. In production, use Claude's
        structured output or more sophisticated parsing.

        Args:
            analysis_text: Raw analysis text from vision

        Returns:
            dict with extracted structured data
        """
        # Try to find JSON blocks in the analysis
        # Look for common patterns in the response

        extracted = {
            "chart_type": None,
            "series": [],
            "axes": {},
            "metrics": {}
        }

        # Basic parsing - look for key phrases
        text_lower = analysis_text.lower()

        # Chart type detection
        if "line chart" in text_lower or "line graph" in text_lower:
            extracted["chart_type"] = "line"
        elif "bar chart" in text_lower or "bar graph" in text_lower:
            extracted["chart_type"] = "bar"
        elif "pie chart" in text_lower:
            extracted["chart_type"] = "pie"
        elif "scatter" in text_lower:
            extracted["chart_type"] = "scatter"
        elif "area chart" in text_lower:
            extracted["chart_type"] = "area"

        # Look for JSON blocks (Claude sometimes returns JSON)
        import re
        json_blocks = re.findall(r'```json\n(.*?)\n```', analysis_text, re.DOTALL)
        if json_blocks:
            try:
                parsed_json = json.loads(json_blocks[0])
                extracted.update(parsed_json)
            except json.JSONDecodeError:
                pass

        # Look for table-like data (simplified)
        # This would be more sophisticated in production

        return extracted


# Register the tool on import
from app.core.tools.registry import tool_registry
tool_registry.register(ChartDataExtractorTool())
