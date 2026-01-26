"""OpenAI embedding service."""

import asyncio

from app.config import settings
from app.core.brain.rag.retriever import EmbeddingService


class OpenAIEmbeddingService(EmbeddingService):
    """OpenAI embedding service implementing the EmbeddingService protocol.

    Uses text-embedding-3-small for generating document embeddings.
    """

    def __init__(self, model: str | None = None):
        """Initialize the embedding service.

        Args:
            model: Embedding model name (defaults to settings.embedding_model).
        """
        try:
            from openai import AsyncOpenAI

            self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        except ImportError:
            raise ImportError(
                "openai package not installed. Run: pip install openai"
            ) from None

        self.model = model or settings.embedding_model
        self.dimensions = settings.embedding_dimensions

    async def embed(self, text: str) -> list[float]:
        """Generate embedding for a single text.

        Args:
            text: Text to embed.

        Returns:
            Embedding vector as list of floats.
        """
        # Truncate text if too long (max ~8000 tokens for embedding models)
        text = text[:32000]  # Rough character limit

        response = await self.client.embeddings.create(
            model=self.model,
            input=text,
            dimensions=self.dimensions,
        )
        return response.data[0].embedding

    async def embed_batch(
        self,
        texts: list[str],
        batch_size: int = 100,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed.
            batch_size: Maximum texts per API call.

        Returns:
            List of embedding vectors.
        """
        all_embeddings: list[list[float]] = []

        # Process in batches to avoid API limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]

            # Truncate each text
            batch = [t[:32000] for t in batch]

            response = await self.client.embeddings.create(
                model=self.model,
                input=batch,
                dimensions=self.dimensions,
            )

            # Sort by index to maintain order
            sorted_data = sorted(response.data, key=lambda x: x.index)
            all_embeddings.extend([d.embedding for d in sorted_data])

            # Rate limiting delay between batches
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)

        return all_embeddings


# Singleton instance
_embedding_service: OpenAIEmbeddingService | None = None


def get_embedding_service() -> OpenAIEmbeddingService:
    """Get or create the embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = OpenAIEmbeddingService()
    return _embedding_service
