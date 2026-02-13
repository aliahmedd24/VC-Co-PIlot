import math
import uuid
from datetime import UTC, datetime

import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.brain import ChunkResult

logger = structlog.get_logger()

HALF_LIFE_DAYS = 70
DECAY_CONSTANT = 0.693 / HALF_LIFE_DAYS


class RAGRetriever:
    """Freshness-weighted pgvector cosine similarity search."""

    @staticmethod
    def freshness_weight(created_at: datetime) -> float:
        """Compute freshness decay weight. Half-life = 70 days."""
        now = datetime.now(tz=UTC)
        if created_at.tzinfo is None:
            age_days = (now.replace(tzinfo=None) - created_at).total_seconds() / 86400
        else:
            age_days = (now - created_at).total_seconds() / 86400
        return math.exp(-DECAY_CONSTANT * age_days)

    @staticmethod
    def compute_final_score(similarity: float, created_at: datetime) -> float:
        """Compute final_score = cosine_similarity * freshness_weight."""
        return similarity * RAGRetriever.freshness_weight(created_at)

    async def search(
        self,
        db: AsyncSession,
        venture_id: uuid.UUID,
        query_embedding: list[float],
        max_chunks: int = 10,
    ) -> list[ChunkResult]:
        """Run freshness-weighted pgvector search.

        Uses raw SQL with pgvector <=> operator for cosine distance.
        Fetches 2x candidates, re-ranks by freshness, returns top N.
        """
        sql = text("""
            SELECT
                dc.id AS chunk_id,
                dc.document_id,
                dc.content,
                dc.created_at,
                1 - (dc.embedding <=> :query_embedding) AS similarity
            FROM document_chunks dc
            WHERE dc.venture_id = :venture_id
              AND dc.embedding IS NOT NULL
            ORDER BY dc.embedding <=> :query_embedding
            LIMIT :fetch_limit
        """)

        result = await db.execute(
            sql,
            {
                "query_embedding": str(query_embedding),
                "venture_id": str(venture_id),
                "fetch_limit": max_chunks * 2,
            },
        )
        rows = result.fetchall()

        scored: list[ChunkResult] = []
        for row in rows:
            fw = self.freshness_weight(row.created_at)
            final = row.similarity * fw
            scored.append(
                ChunkResult(
                    chunk_id=str(row.chunk_id),
                    document_id=str(row.document_id),
                    content=row.content,
                    similarity=round(row.similarity, 6),
                    freshness_weight=round(fw, 6),
                    final_score=round(final, 6),
                )
            )

        scored.sort(key=lambda c: c.final_score, reverse=True)
        return scored[:max_chunks]


rag_retriever = RAGRetriever()
