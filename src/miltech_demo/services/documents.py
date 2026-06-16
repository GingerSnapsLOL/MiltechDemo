"""Document service: loads synthetic markdown reports and searches them.

Business logic for the ``search_documents`` and ``get_document`` MCP tools. Reads
markdown files from a directory, parses them into :class:`Document` models, and
provides deterministic keyword search.
"""

from pathlib import Path

import structlog

from miltech_demo.schemas import (
    Document,
    DocumentHit,
    GetDocumentInput,
    GetDocumentResult,
    SearchDocumentsInput,
    SearchDocumentsResult,
)

logger = structlog.get_logger(__name__)

_SNIPPET_LEN = 160


def _parse_document(path: Path) -> Document:
    """Parse a markdown report file into a Document."""
    text = path.read_text(encoding="utf-8")
    title = path.stem
    source = "markdown"
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
        elif stripped.lower().startswith("source:"):
            source = stripped.split(":", 1)[1].strip() or source
    return Document(id=path.stem, title=title, source=source, content=text)


def _snippet(content: str, terms: list[str]) -> str:
    """Return an excerpt around the first matching term, else the head of the text."""
    lowered = content.lower()
    for term in terms:
        idx = lowered.find(term)
        if idx != -1:
            start = max(0, idx - 40)
            return content[start : start + _SNIPPET_LEN].strip()
    return content[:_SNIPPET_LEN].strip()


class DocumentService:
    """Loads and searches synthetic markdown reports."""

    def __init__(self, reports_dir: Path) -> None:
        self._reports_dir = reports_dir
        self._documents: dict[str, Document] | None = None

    def _load(self) -> dict[str, Document]:
        if self._documents is None:
            documents = {}
            for path in sorted(self._reports_dir.glob("*.md")):
                document = _parse_document(path)
                documents[document.id] = document
            self._documents = documents
            logger.info("documents_loaded", count=len(documents), dir=str(self._reports_dir))
        return self._documents

    def search_documents(self, params: SearchDocumentsInput) -> SearchDocumentsResult:
        """Return documents matching the query terms, ranked by match ratio."""
        terms = [term for term in params.query.lower().split() if term]
        unique_terms = set(terms)
        hits: list[DocumentHit] = []
        for document in self._load().values():
            haystack = f"{document.title}\n{document.content}".lower()
            matched = [term for term in unique_terms if term in haystack]
            if not matched:
                continue
            score = len(matched) / len(unique_terms) if unique_terms else 0.0
            hits.append(
                DocumentHit(
                    id=document.id,
                    title=document.title,
                    source=document.source,
                    snippet=_snippet(document.content, terms),
                    score=round(score, 3),
                )
            )
        hits.sort(key=lambda hit: hit.score, reverse=True)
        hits = hits[: params.limit]
        return SearchDocumentsResult(query=params.query, hits=hits, count=len(hits))

    def get_document(self, params: GetDocumentInput) -> GetDocumentResult:
        """Return a document by id, or ``found=False`` if it does not exist."""
        document = self._load().get(params.document_id)
        return GetDocumentResult(found=document is not None, document=document)
