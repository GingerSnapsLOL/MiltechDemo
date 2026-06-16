import pytest
from pydantic import ValidationError

from miltech_demo.schemas import Classification, Evidence, IntelligenceReport


def test_report_minimal_construction() -> None:
    report = IntelligenceReport(query="q", summary="s", confidence=0.5)

    assert report.id
    assert report.findings == []
    assert report.evidence == []
    assert report.classification is Classification.UNCLASSIFIED
    assert report.trace_id is None


@pytest.mark.parametrize("confidence", [-0.1, 1.1])
def test_report_rejects_out_of_range_confidence(confidence: float) -> None:
    with pytest.raises(ValidationError):
        IntelligenceReport(query="q", summary="s", confidence=confidence)


def test_report_nests_evidence_and_round_trips() -> None:
    report = IntelligenceReport(
        query="q",
        summary="s",
        findings=["finding one"],
        evidence=[Evidence(document_id="doc-1", snippet="text", relevance_score=0.9)],
        confidence=0.8,
        classification=Classification.SECRET,
        trace_id="trace-1",
    )

    restored = IntelligenceReport.model_validate_json(report.model_dump_json())

    assert restored == report
    assert isinstance(restored.evidence[0], Evidence)


def test_report_schema_contains_examples() -> None:
    assert "examples" in IntelligenceReport.model_json_schema()
