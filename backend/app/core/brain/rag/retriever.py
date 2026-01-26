"""RAG Retriever with freshness-weighted scoring."""

from dataclasses import dataclass
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk
from app.models.venture import Venture


class EmbeddingService(Protocol):
    """Protocol for embedding service."""

    async def embed(self, text: str) -> list[float]: ...
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...


@dataclass
class ChunkWithScore:
    """A document chunk with relevance scores."""

    id: str
    content: str
    document_id: str
    similarity: float
    freshness_weight: float
    final_score: float
    metadata: dict | None = None


class RAGRetriever:
    """RAG retrieval with freshness-weighted scoring."""

    FRESHNESS_HALF_LIFE_DAYS = 70

    def __init__(
        self, venture_id: str, session: AsyncSession, embedder: EmbeddingService | None = None
    ):
        self.venture_id = venture_id
        self.session = session
        self.embedder = embedder

    async def search(self, query: str, limit: int = 10) -> list[ChunkWithScore]:
        """Search with combined relevance and freshness scoring.

        If no embedder is available, falls back to keyword search.
        """
        if not self.embedder:
            return await self._keyword_search(query, limit)

        query_embedding = await self.embedder.embed(query)
        embedding_str = f"[{','.join(map(str, query_embedding))}]"

        sql = text("""
            SELECT
                dc.id,
                dc.content,
                dc.document_id,
                dc.metadata,
                1 - (dc.embedding <=> :embedding::vector) AS similarity,
                EXP(-0.693 * EXTRACT(EPOCH FROM (NOW() - d.created_at)) / 86400 / :half_life) AS freshness_weight,
                (1 - (dc.embedding <=> :embedding::vector)) *
                EXP(-0.693 * EXTRACT(EPOCH FROM (NOW() - d.created_at)) / 86400 / :half_life) AS final_score
            FROM document_chunks dc
            JOIN documents d ON dc.document_id = d.id
            WHERE dc.venture_id = :venture_id AND dc.embedding IS NOT NULL
            ORDER BY final_score DESC
            LIMIT :limit
        """)

        result = await self.session.execute(
            sql,
            {
                "embedding": embedding_str,
                "venture_id": self.venture_id,
                "half_life": self.FRESHNESS_HALF_LIFE_DAYS,
                "limit": limit,
            },
        )

        return [
            ChunkWithScore(
                id=row.id,
                content=row.content,
                document_id=row.document_id,
                similarity=row.similarity,
                freshness_weight=row.freshness_weight,
                final_score=row.final_score,
                metadata=row.metadata,
            )
            for row in result.fetchall()
        ]

    async def _keyword_search(self, query: str, limit: int) -> list[ChunkWithScore]:
        """Fallback keyword search when embeddings not available."""
        keywords = query.lower().split()

        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.venture_id == self.venture_id)
            .limit(limit * 3)  # Get more to filter
        )
        result = await self.session.execute(stmt)
        chunks = list(result.scalars().all())

        # Score by keyword matches
        scored = []
        for chunk in chunks:
            matches = sum(1 for kw in keywords if kw in chunk.content.lower())
            if matches > 0:
                score = matches / len(keywords)
                scored.append(
                    ChunkWithScore(
                        id=chunk.id,
                        content=chunk.content,
                        document_id=chunk.document_id,
                        similarity=score,
                        freshness_weight=1.0,
                        final_score=score,
                        metadata=chunk.metadata,
                    )
                )

        scored.sort(key=lambda x: x.final_score, reverse=True)
        return scored[:limit]

    async def index_document(self, document_id: str, content: str) -> int:
        """Index a document by chunking and embedding."""
        chunks = self._chunk_text(content)

        if not chunks:
            return 0

        # Get document and venture
        doc_result = await self.session.execute(select(Document).where(Document.id == document_id))
        document = doc_result.scalar_one_or_none()
        if not document:
            raise ValueError(f"Document not found: {document_id}")

        venture_result = await self.session.execute(
            select(Venture).where(Venture.workspace_id == document.workspace_id)
        )
        venture = venture_result.scalar_one_or_none()
        if not venture:
            raise ValueError(f"No venture for workspace: {document.workspace_id}")

        # Embed if embedder available
        embeddings: list[list[float] | None] = [None] * len(chunks)
        if self.embedder:
            texts = [c["text"] for c in chunks]
            embeddings = await self.embedder.embed_batch(texts)

        # Create chunk objects
        chunk_objects = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings, strict=False)):
            chunk_obj = DocumentChunk(
                id=str(uuid4()),
                document_id=document_id,
                venture_id=venture.id,
                content=chunk["text"],
                embedding=embedding,
                chunk_index=idx,
                metadata=chunk.get("metadata"),
            )
            chunk_objects.append(chunk_obj)

        self.session.add_all(chunk_objects)
        return len(chunk_objects)

    def _chunk_text(
        self, text: str, target_size: int = 512, overlap: int = 64
    ) -> list[dict[str, Any]]:
        """Semantic chunking with overlap."""
        char_target = target_size * 4
        char_overlap = overlap * 4

        chunks: list[dict[str, Any]] = []
        paragraphs = text.split("\n\n")
        current_chunk = ""
        chunk_start = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) > char_target and current_chunk:
                chunks.append(
                    {"text": current_chunk.strip(), "metadata": {"start_char": chunk_start}}
                )
                overlap_start = max(0, len(current_chunk) - char_overlap)
                current_chunk = current_chunk[overlap_start:] + "\n\n" + para
                chunk_start += overlap_start
            else:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para

        if current_chunk.strip():
            chunks.append({"text": current_chunk.strip(), "metadata": {"start_char": chunk_start}})

        return chunks
