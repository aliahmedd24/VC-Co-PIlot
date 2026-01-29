"""Vision analysis service for processing images with Claude's vision capabilities.

This service provides high-level analysis methods for different types of visual content:
- Pitch deck slides
- Financial charts and graphs
- OCR and text extraction
- Competitor screenshots
"""

import logging
from typing import Any, BinaryIO

from app.core.agents.llm_client import ClaudeLLMClient
from app.services.vision.prompts import (
    VISION_ANALYST_SYSTEM,
    get_prompt_for_analysis_type,
)

logger = logging.getLogger(__name__)


class VisionAnalyzer:
    """High-level vision analysis service.

    This service wraps the LLM client's vision capabilities with specialized
    prompts for different analysis tasks.

    Usage:
        analyzer = VisionAnalyzer()
        result = await analyzer.analyze_pitch_deck_slide(image_bytes, slide_num=3)
        chart_data = await analyzer.analyze_financial_chart(chart_image)
    """

    def __init__(self, llm_client: ClaudeLLMClient | None = None):
        """Initialize vision analyzer.

        Args:
            llm_client: Optional LLM client (defaults to new Claude client)
        """
        self.llm = llm_client or ClaudeLLMClient()

    async def analyze_pitch_deck_slide(
        self,
        image_data: bytes | BinaryIO,
        slide_number: int | None = None,
        quick_mode: bool = False,
        media_type: str = "image/png",
    ) -> dict[str, Any]:
        """Analyze a pitch deck slide.

        Args:
            image_data: Slide image (bytes or file-like object)
            slide_number: Slide number for context (optional)
            quick_mode: Use quick summary instead of full analysis
            media_type: Image MIME type

        Returns:
            dict with:
                - content: Full analysis text
                - slide_type: Identified slide type
                - key_message: Main takeaway
                - metrics: Extracted numbers and data
                - design_rating: 1-10 score
                - recommendations: List of suggestions
                - usage: Token usage stats
        """
        # Convert file-like object to bytes
        if hasattr(image_data, "read"):
            image_bytes = image_data.read()
            if hasattr(image_data, "seek"):
                image_data.seek(0)
        else:
            image_bytes = image_data

        # Get appropriate prompt
        prompt_type = "pitch_deck_quick" if quick_mode else "pitch_deck"
        prompt = get_prompt_for_analysis_type(prompt_type)

        # Add slide number context
        if slide_number is not None:
            prompt = f"This is slide #{slide_number}.\n\n{prompt}"

        # Analyze
        result = await self.llm.analyze_image(
            image_data=image_bytes,
            prompt=prompt,
            media_type=media_type,
            system=VISION_ANALYST_SYSTEM,
            max_tokens=3000 if not quick_mode else 1000,
        )

        logger.info(
            f"Analyzed pitch deck slide #{slide_number or 'N/A'} "
            f"({result['usage']['input_tokens']} input tokens, "
            f"{result['usage']['output_tokens']} output tokens)"
        )

        # Parse structured data from response (basic parsing)
        # TODO: Use structured output or better parsing
        return {
            "content": result["content"],
            "slide_number": slide_number,
            "raw_response": result.get("raw_response"),
            "usage": result["usage"],
        }

    async def analyze_financial_chart(
        self,
        image_data: bytes | BinaryIO,
        data_only: bool = False,
        media_type: str = "image/png",
    ) -> dict[str, Any]:
        """Analyze a financial chart or graph.

        Args:
            image_data: Chart image (bytes or file-like object)
            data_only: Extract only numerical data, skip insights
            media_type: Image MIME type

        Returns:
            dict with:
                - content: Full analysis
                - chart_type: Identified chart type
                - extracted_data: Structured data points
                - trends: Key insights and trends
                - usage: Token usage stats
        """
        # Convert file-like object to bytes
        if hasattr(image_data, "read"):
            image_bytes = image_data.read()
            if hasattr(image_data, "seek"):
                image_data.seek(0)
        else:
            image_bytes = image_data

        # Get appropriate prompt
        prompt_type = "chart_data_only" if data_only else "chart"
        prompt = get_prompt_for_analysis_type(prompt_type)

        # Analyze
        result = await self.llm.analyze_image(
            image_data=image_bytes,
            prompt=prompt,
            media_type=media_type,
            system=VISION_ANALYST_SYSTEM,
            max_tokens=2500 if not data_only else 1500,
        )

        logger.info(
            f"Analyzed financial chart "
            f"({result['usage']['input_tokens']} input tokens, "
            f"{result['usage']['output_tokens']} output tokens)"
        )

        return {
            "content": result["content"],
            "raw_response": result.get("raw_response"),
            "usage": result["usage"],
        }

    async def perform_ocr(
        self,
        image_data: bytes | BinaryIO,
        structured: bool = False,
        media_type: str = "image/png",
    ) -> dict[str, Any]:
        """Perform OCR on an image to extract text.

        Args:
            image_data: Image with text (bytes or file-like object)
            structured: Extract structured data (forms, tables, etc.)
            media_type: Image MIME type

        Returns:
            dict with:
                - content: Full OCR analysis
                - extracted_text: Plain text content
                - structured_data: Key-value pairs (if structured=True)
                - usage: Token usage stats
        """
        # Convert file-like object to bytes
        if hasattr(image_data, "read"):
            image_bytes = image_data.read()
            if hasattr(image_data, "seek"):
                image_data.seek(0)
        else:
            image_bytes = image_data

        # Get appropriate prompt
        prompt_type = "ocr_structured" if structured else "ocr"
        prompt = get_prompt_for_analysis_type(prompt_type)

        # Analyze
        result = await self.llm.analyze_image(
            image_data=image_bytes,
            prompt=prompt,
            media_type=media_type,
            system=VISION_ANALYST_SYSTEM,
            max_tokens=4000,  # OCR can be lengthy
        )

        logger.info(
            f"Performed OCR on image "
            f"({result['usage']['input_tokens']} input tokens, "
            f"{result['usage']['output_tokens']} output tokens)"
        )

        return {
            "content": result["content"],
            "extracted_text": result["content"],  # Alias for convenience
            "raw_response": result.get("raw_response"),
            "usage": result["usage"],
        }

    async def analyze_competitor_screenshot(
        self,
        image_data: bytes | BinaryIO,
        competitor_name: str | None = None,
        screenshot_type: str = "general",
        media_type: str = "image/png",
    ) -> dict[str, Any]:
        """Analyze a competitor product screenshot.

        Args:
            image_data: Screenshot image (bytes or file-like object)
            competitor_name: Name of competitor (optional, for context)
            screenshot_type: Type of screenshot ('general', 'landing_page', 'dashboard', etc.)
            media_type: Image MIME type

        Returns:
            dict with:
                - content: Full analysis
                - ui_insights: UI/UX observations
                - features: Identified features
                - competitive_advantages: Strengths and differentiators
                - recommendations: How to compete
                - usage: Token usage stats
        """
        # Convert file-like object to bytes
        if hasattr(image_data, "read"):
            image_bytes = image_data.read()
            if hasattr(image_data, "seek"):
                image_data.seek(0)
        else:
            image_bytes = image_data

        # Get appropriate prompt
        if screenshot_type == "landing_page":
            prompt = get_prompt_for_analysis_type("competitor_landing")
        else:
            prompt = get_prompt_for_analysis_type("competitor")

        # Add competitor context
        if competitor_name:
            prompt = f"This is a screenshot of {competitor_name}'s product.\n\n{prompt}"

        # Analyze
        result = await self.llm.analyze_image(
            image_data=image_bytes,
            prompt=prompt,
            media_type=media_type,
            system=VISION_ANALYST_SYSTEM,
            max_tokens=3000,
        )

        logger.info(
            f"Analyzed competitor screenshot{' (' + competitor_name + ')' if competitor_name else ''} "
            f"({result['usage']['input_tokens']} input tokens, "
            f"{result['usage']['output_tokens']} output tokens)"
        )

        return {
            "content": result["content"],
            "competitor_name": competitor_name,
            "raw_response": result.get("raw_response"),
            "usage": result["usage"],
        }

    async def analyze_table(
        self,
        image_data: bytes | BinaryIO,
        media_type: str = "image/png",
    ) -> dict[str, Any]:
        """Extract data from a table image.

        Args:
            image_data: Table image (bytes or file-like object)
            media_type: Image MIME type

        Returns:
            dict with:
                - content: Extracted table as markdown
                - structured_data: Table data as list of dicts
                - usage: Token usage stats
        """
        # Convert file-like object to bytes
        if hasattr(image_data, "read"):
            image_bytes = image_data.read()
            if hasattr(image_data, "seek"):
                image_data.seek(0)
        else:
            image_bytes = image_data

        prompt = get_prompt_for_analysis_type("table")

        result = await self.llm.analyze_image(
            image_data=image_bytes,
            prompt=prompt,
            media_type=media_type,
            system=VISION_ANALYST_SYSTEM,
            max_tokens=2000,
        )

        logger.info(
            f"Extracted table data "
            f"({result['usage']['input_tokens']} input tokens, "
            f"{result['usage']['output_tokens']} output tokens)"
        )

        return {
            "content": result["content"],
            "raw_response": result.get("raw_response"),
            "usage": result["usage"],
        }

    async def analyze_general(
        self,
        image_data: bytes | BinaryIO,
        custom_prompt: str | None = None,
        media_type: str = "image/png",
    ) -> dict[str, Any]:
        """General-purpose image analysis.

        Args:
            image_data: Image (bytes or file-like object)
            custom_prompt: Optional custom analysis prompt
            media_type: Image MIME type

        Returns:
            dict with:
                - content: Analysis result
                - usage: Token usage stats
        """
        # Convert file-like object to bytes
        if hasattr(image_data, "read"):
            image_bytes = image_data.read()
            if hasattr(image_data, "seek"):
                image_data.seek(0)
        else:
            image_bytes = image_data

        prompt = custom_prompt or get_prompt_for_analysis_type("general")

        result = await self.llm.analyze_image(
            image_data=image_bytes,
            prompt=prompt,
            media_type=media_type,
            system=VISION_ANALYST_SYSTEM,
            max_tokens=2000,
        )

        logger.info(
            f"Performed general image analysis "
            f"({result['usage']['input_tokens']} input tokens, "
            f"{result['usage']['output_tokens']} output tokens)"
        )

        return {
            "content": result["content"],
            "raw_response": result.get("raw_response"),
            "usage": result["usage"],
        }


def get_vision_analyzer(llm_client: ClaudeLLMClient | None = None) -> VisionAnalyzer:
    """Factory function to get a vision analyzer instance.

    Args:
        llm_client: Optional LLM client to use

    Returns:
        Configured VisionAnalyzer instance
    """
    return VisionAnalyzer(llm_client=llm_client)
