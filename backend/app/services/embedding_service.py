import structlog
from openai import OpenAI

from app.config import settings

logger = structlog.get_logger()

EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSIONS = 1536
MAX_BATCH_SIZE = 100


class EmbeddingService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=settings.openai_api_key)

    def embed_text(self, text: str) -> list[float]:
        response = self.client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=text,
        )
        return response.data[0].embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        all_embeddings: list[list[float]] = []

        for i in range(0, len(texts), MAX_BATCH_SIZE):
            batch = texts[i : i + MAX_BATCH_SIZE]
            response = self.client.embeddings.create(
                model=EMBEDDING_MODEL,
                input=batch,
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)
            logger.info(
                "embeddings_created",
                batch_start=i,
                batch_size=len(batch),
                total=len(texts),
            )

        return all_embeddings


embedding_service = EmbeddingService()
