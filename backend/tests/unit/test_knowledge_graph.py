"""Unit tests for Knowledge Graph operations."""


from app.models.kg_entity import KGEntityType


class MockSession:
    """Mock async session for unit testing without database."""

    def __init__(self):
        self.entities: dict[str, dict] = {}
        self.relations: list[dict] = []
        self.evidence: list[dict] = []

    async def flush(self):
        pass

    async def execute(self, stmt):
        # Return mock result
        return MockResult([])

    def add(self, obj):
        if hasattr(obj, "__tablename__"):
            if obj.__tablename__ == "kg_entities":
                self.entities[obj.id] = obj
            elif obj.__tablename__ == "kg_relations":
                self.relations.append(obj)
            elif obj.__tablename__ == "kg_evidence":
                self.evidence.append(obj)


class MockResult:
    def __init__(self, items):
        self._items = items

    def scalar_one_or_none(self):
        return self._items[0] if self._items else None

    def scalars(self):
        return MockScalars(self._items)


class MockScalars:
    def __init__(self, items):
        self._items = items

    def all(self):
        return self._items


# Direct tests of EntityExtractor (doesn't need database)


def test_entity_extractor_keyword_match():
    """Test keyword-based entity extraction."""
    from app.core.brain.kg.entity_extractor import EntityExtractor

    extractor = EntityExtractor(use_llm=False)
    text = "Our target market is B2B SaaS with TAM of $50B. Our main competitor is Salesforce."

    # Run sync version for testing
    entities = extractor._extract_with_keywords(text)

    assert len(entities) >= 2
    types = [e.type for e in entities]
    assert KGEntityType.MARKET in types
    assert KGEntityType.COMPETITOR in types


def test_entity_extractor_no_matches():
    """Test extraction with no matching keywords."""
    from app.core.brain.kg.entity_extractor import EntityExtractor

    extractor = EntityExtractor(use_llm=False)
    text = "This is a generic sentence with no specific keywords."

    entities = extractor._extract_with_keywords(text)
    assert len(entities) == 0


def test_entity_extractor_confidence():
    """Test that keyword extraction has low confidence."""
    from app.core.brain.kg.entity_extractor import EntityExtractor

    extractor = EntityExtractor(use_llm=False)
    text = "The market size is huge."

    entities = extractor._extract_with_keywords(text)

    for entity in entities:
        assert entity.confidence == 0.4  # Keyword match has low confidence


# Tests for text chunking (doesn't need database)


def test_rag_chunker():
    """Test text chunking logic."""
    from app.core.brain.rag.retriever import RAGRetriever

    retriever = RAGRetriever("test-venture", None)  # type: ignore

    text = """First paragraph with some content.

Second paragraph with more content.

Third paragraph that is a bit longer and contains more information about the topic at hand.

Fourth paragraph to test the chunking behavior."""

    chunks = retriever._chunk_text(text, target_size=50, overlap=10)

    assert len(chunks) >= 1
    for chunk in chunks:
        assert "text" in chunk
        assert "metadata" in chunk
        assert len(chunk["text"]) > 0


def test_rag_chunker_empty():
    """Test chunking empty text."""
    from app.core.brain.rag.retriever import RAGRetriever

    retriever = RAGRetriever("test-venture", None)  # type: ignore

    chunks = retriever._chunk_text("")
    assert chunks == []


def test_rag_chunker_single_paragraph():
    """Test chunking with a single paragraph."""
    from app.core.brain.rag.retriever import RAGRetriever

    retriever = RAGRetriever("test-venture", None)  # type: ignore

    text = "Single paragraph with content."
    chunks = retriever._chunk_text(text)

    assert len(chunks) == 1
    assert chunks[0]["text"] == text
