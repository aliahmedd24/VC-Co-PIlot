"""LLM client abstraction for Claude and OpenAI."""

import base64
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from app.config import settings


class LLMClient(ABC):
    """Abstract LLM client interface."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            system: Optional system prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            Generated text content.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            system: Optional system prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Yields:
            Text chunks as they arrive.
        """
        pass


class ClaudeLLMClient(LLMClient):
    """Anthropic Claude LLM client."""

    def __init__(self, model: str | None = None):
        """Initialize the Claude client.

        Args:
            model: Model name (defaults to settings.default_model).
        """
        try:
            import anthropic

            self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        except ImportError:
            raise ImportError(
                "anthropic package not installed. Run: pip install anthropic"
            ) from None

        self.model = model or settings.default_model

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a completion using Claude."""
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "You are a helpful AI assistant.",
            messages=messages,
        )
        return response.content[0].text

    async def stream(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion using Claude."""
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "You are a helpful AI assistant.",
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def complete_with_tools(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, any]],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> dict[str, any]:
        """Generate completion with tool use capability.

        This method enables Claude to use tools during generation. If Claude
        decides to use a tool, the response will include tool_calls that need
        to be executed and their results fed back to Claude.

        Args:
            messages: List of message dicts with 'role' and 'content'.
            tools: List of tool definitions in Claude format.
            system: Optional system prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            dict with:
                - content: Text content from Claude (may be empty if only tool calls)
                - tool_calls: List of dicts with 'id', 'name', and 'input' for each tool call
                - stop_reason: Why generation stopped ('end_turn', 'tool_use', etc.)
        """
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "You are a helpful AI assistant.",
            messages=messages,
            tools=tools,
        )

        # Parse response content blocks
        content_blocks = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content_blocks.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        return {
            "content": "\n".join(content_blocks) if content_blocks else "",
            "tool_calls": tool_calls,
            "stop_reason": response.stop_reason
        }

    async def complete_with_vision(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate completion with vision (image) support.

        This method supports messages with image content blocks. Images should be
        provided as content arrays with both text and image blocks.

        Message format example:
        {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": "<base64-encoded-image>"
                    }
                },
                {
                    "type": "text",
                    "text": "What's in this image?"
                }
            ]
        }

        Args:
            messages: List of message dicts. 'content' can be string or list of content blocks.
            system: Optional system prompt.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature.

        Returns:
            Generated text content.
        """
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system or "You are a helpful AI assistant with vision capabilities.",
            messages=messages,
        )

        # Extract text from response
        content_blocks = []
        for block in response.content:
            if block.type == "text":
                content_blocks.append(block.text)

        return "\n".join(content_blocks) if content_blocks else ""

    async def analyze_image(
        self,
        image_data: bytes,
        prompt: str,
        media_type: str = "image/png",
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> dict[str, any]:
        """Analyze a single image with Claude's vision capabilities.

        Convenience method for analyzing a single image without manually
        constructing the message format.

        Args:
            image_data: Image bytes (PNG, JPEG, WEBP, or GIF)
            prompt: Analysis prompt/question about the image
            media_type: Image MIME type (image/png, image/jpeg, image/webp, image/gif)
            system: Optional system prompt
            max_tokens: Maximum tokens in response

        Returns:
            dict with:
                - content: Analysis text
                - raw_response: Full response object

        Example:
            result = await client.analyze_image(
                image_data=pdf_page_bytes,
                prompt="Extract all metrics and KPIs from this slide.",
                media_type="image/png"
            )
            print(result["content"])
        """
        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode("utf-8")

        # Build vision message
        message = {
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": media_type,
                        "data": image_base64
                    }
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }

        # Get response
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.5,  # Lower temperature for more factual vision analysis
            system=system or "You are an expert at analyzing images and documents with precision.",
            messages=[message],
        )

        # Extract text content
        content_text = ""
        for block in response.content:
            if block.type == "text":
                content_text += block.text

        return {
            "content": content_text,
            "raw_response": response,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            }
        }


class OpenAILLMClient(LLMClient):
    """OpenAI LLM client."""

    def __init__(self, model: str = "gpt-4o"):
        """Initialize the OpenAI client.

        Args:
            model: Model name (defaults to gpt-4o).
        """
        try:
            from openai import AsyncOpenAI

            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            ) from None

        self.model = model

    async def complete(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Generate a completion using OpenAI."""
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        return response.choices[0].message.content or ""

    async def stream(
        self,
        messages: list[dict[str, str]],
        system: str | None = None,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """Stream a completion using OpenAI."""
        full_messages = []
        if system:
            full_messages.append({"role": "system", "content": system})
        full_messages.extend(messages)

        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=full_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True,
        )

        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


def get_llm_client(provider: str = "claude") -> LLMClient:
    """Factory function to get an LLM client.

    Args:
        provider: Either 'claude' or 'openai'.

    Returns:
        Configured LLM client.
    """
    if provider == "claude":
        return ClaudeLLMClient()
    elif provider == "openai":
        return OpenAILLMClient()
    else:
        raise ValueError(f"Unknown provider: {provider}. Use 'claude' or 'openai'.")
