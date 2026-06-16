import pytest
from pydantic import ValidationError

from miltech_demo.schemas import Classification, Document, DocumentChunk


def test_document_defaults_are_populated() -> None:
    doc = Document(title="t", source="s", content="c")

    assert doc.id
    assert doc.created_at.tzinfo is not None
    assert doc.classification is Classification.UNCLASSIFIED
    assert doc.metadata == {}


def test_documents_get_unique_ids() -> None:
    first = Document(title="t", source="s", content="c")
    second = Document(title="t", source="s", content="c")

    assert first.id != second.id


def test_document_rejects_empty_required_fields() -> None:
    with pytest.raises(ValidationError):
        Document(title="", source="s", content="c")


def test_document_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        Document(title="t", source="s", content="c", unexpected="x")  # type: ignore[call-arg]


def test_document_round_trip_serialization() -> None:
    doc = Document(
        title="t",
        source="s",
        content="c",
        classification=Classification.SECRET,
        metadata={"region": "east"},
    )

    assert Document.model_validate_json(doc.model_dump_json()) == doc


def test_document_schema_contains_examples() -> None:
    assert "examples" in Document.model_json_schema()


def test_document_chunk_rejects_negative_index() -> None:
    with pytest.raises(ValidationError):
        DocumentChunk(document_id="doc-1", index=-1, content="c")


def test_document_chunk_round_trip_serialization() -> None:
    chunk = DocumentChunk(document_id="doc-1", index=0, content="c", token_count=3)

    assert DocumentChunk.model_validate_json(chunk.model_dump_json()) == chunk
