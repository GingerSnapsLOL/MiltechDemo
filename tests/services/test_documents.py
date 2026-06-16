from miltech_demo.core.config import Settings
from miltech_demo.schemas import GetDocumentInput, SearchDocumentsInput
from miltech_demo.services.documents import DocumentService


def _service() -> DocumentService:
    return DocumentService(Settings().reports_dir)


def test_search_returns_ranked_hits() -> None:
    result = _service().search_documents(SearchDocumentsInput(query="eastern corridor"))

    assert result.count > 0
    assert result.hits[0].score >= result.hits[-1].score
    assert all(0.0 <= hit.score <= 1.0 for hit in result.hits)


def test_search_respects_limit() -> None:
    result = _service().search_documents(SearchDocumentsInput(query="the", limit=1))
    assert result.count <= 1


def test_search_no_match_returns_empty() -> None:
    result = _service().search_documents(SearchDocumentsInput(query="zzzznomatch"))
    assert result.count == 0
    assert result.hits == []


def test_get_document_found() -> None:
    result = _service().get_document(GetDocumentInput(document_id="eastern-corridor"))
    assert result.found is True
    assert result.document is not None
    assert result.document.id == "eastern-corridor"


def test_get_document_not_found() -> None:
    result = _service().get_document(GetDocumentInput(document_id="does-not-exist"))
    assert result.found is False
    assert result.document is None
