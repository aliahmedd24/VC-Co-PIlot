from app.workers.document_tasks import _chunk_text


def test_chunk_text_basic() -> None:
    text = " ".join(["word"] * 1200)
    chunks = _chunk_text(text)
    assert len(chunks) >= 2
    for chunk in chunks:
        words = chunk.split()
        # Each chunk should be at most CHUNK_SIZE + CHUNK_OVERLAP words
        assert len(words) <= 550 + 50


def test_chunk_text_short() -> None:
    text = "This is a short document."
    chunks = _chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == "This is a short document."


def test_chunk_text_paragraph_boundaries() -> None:
    para1 = " ".join(["alpha"] * 400)
    para2 = " ".join(["beta"] * 400)
    text = f"{para1}\n\n{para2}"
    chunks = _chunk_text(text)
    assert len(chunks) >= 2
