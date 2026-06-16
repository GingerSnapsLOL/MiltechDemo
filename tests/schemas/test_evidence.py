import pytest
from pydantic import ValidationError

from miltech_demo.schemas import Evidence


def test_evidence_minimal_construction() -> None:
    ev = Evidence(document_id="doc-1", snippet="text", relevance_score=0.5)

    assert ev.id
    assert ev.chunk_id is None
    assert ev.rationale is None


@pytest.mark.parametrize("score", [-0.1, 1.1])
def test_evidence_rejects_out_of_range_score(score: float) -> None:
    with pytest.raises(ValidationError):
        Evidence(document_id="doc-1", snippet="text", relevance_score=score)


def test_evidence_rejects_empty_snippet() -> None:
    with pytest.raises(ValidationError):
        Evidence(document_id="doc-1", snippet="", relevance_score=0.5)


def test_evidence_round_trip_serialization() -> None:
    ev = Evidence(
        document_id="doc-1",
        chunk_id="chunk-0",
        snippet="text",
        relevance_score=0.9,
        rationale="because",
    )

    assert Evidence.model_validate_json(ev.model_dump_json()) == ev


def test_evidence_schema_contains_examples() -> None:
    assert "examples" in Evidence.model_json_schema()
