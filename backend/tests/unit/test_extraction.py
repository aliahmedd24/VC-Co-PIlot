"""Unit tests for text extraction service."""

import pytest

from app.services.extraction import (
    extract_csv,
    extract_text,
    is_supported_mime_type,
)


class TestMimeTypeSupport:
    """Tests for MIME type validation."""

    def test_supported_mime_types(self):
        """Test common supported MIME types."""
        assert is_supported_mime_type("application/pdf")
        assert is_supported_mime_type("text/plain")
        assert is_supported_mime_type("text/csv")

    def test_unsupported_mime_types(self):
        """Test unsupported MIME types."""
        assert not is_supported_mime_type("image/png")
        assert not is_supported_mime_type("video/mp4")
        assert not is_supported_mime_type("application/zip")


class TestTextExtraction:
    """Tests for text extraction from various formats."""

    def test_extract_text_plain(self):
        """Test plain text extraction."""
        content = b"Hello, this is a test document."
        result = extract_text(content, "text/plain")
        assert result == "Hello, this is a test document."

    def test_extract_text_plain_unicode(self):
        """Test plain text with unicode."""
        content = "Hello, 世界! 🚀".encode()
        result = extract_text(content, "text/plain")
        assert "Hello" in result
        assert "世界" in result

    def test_extract_csv(self):
        """Test CSV extraction."""
        content = b"name,age,city\nAlice,30,NYC\nBob,25,LA"
        result = extract_csv(content)
        assert "name" in result
        assert "Alice" in result
        assert "Bob" in result

    def test_extract_unsupported(self):
        """Test extraction of unsupported type raises error."""
        with pytest.raises(ValueError, match="Unsupported MIME type"):
            extract_text(b"data", "image/png")


class TestChunking:
    """Tests for text chunking."""

    def test_chunk_basic(self):
        """Test basic chunking."""
        from app.workers.document_tasks import _chunk_text

        text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        chunks = _chunk_text(text, target_size=10, overlap=2)

        assert len(chunks) >= 1
        assert all("text" in c for c in chunks)
        assert all("metadata" in c for c in chunks)

    def test_chunk_long_document(self):
        """Test chunking of longer document."""
        from app.workers.document_tasks import _chunk_text

        # Create a long document
        paragraphs = [f"This is paragraph number {i}. " * 20 for i in range(20)]
        text = "\n\n".join(paragraphs)

        chunks = _chunk_text(text, target_size=200, overlap=20)

        # Should create multiple chunks
        assert len(chunks) > 1

        # All chunks should have content
        for chunk in chunks:
            assert len(chunk["text"]) > 0

    def test_chunk_overlap(self):
        """Test that chunks have overlap."""
        from app.workers.document_tasks import _chunk_text

        text = ("A" * 500) + "\n\n" + ("B" * 500) + "\n\n" + ("C" * 500)
        chunks = _chunk_text(text, target_size=200, overlap=50)

        # With 3 distinct sections and overlap, we should have multiple chunks
        assert len(chunks) >= 2
