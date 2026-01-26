"""LLM client abstraction for Claude and OpenAI."""

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
