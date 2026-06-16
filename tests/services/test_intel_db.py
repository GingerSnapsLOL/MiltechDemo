from pathlib import Path

import pytest

from miltech_demo.schemas import QueryIntelInput
from miltech_demo.services.intel_db import IntelDatabase


@pytest.fixture
def db(tmp_path: Path) -> IntelDatabase:
    database = IntelDatabase(tmp_path / "intel.db")
    database.initialize()
    return database


def test_query_returns_typed_rows(db: IntelDatabase) -> None:
    result = db.query(QueryIntelInput(query="corridor"))

    assert result.count > 0
    assert all(row.region for row in result.rows)
    assert all(isinstance(row.id, int) for row in result.rows)


def test_query_respects_limit(db: IntelDatabase) -> None:
    result = db.query(QueryIntelInput(query="east", limit=1))
    assert result.count <= 1


def test_query_no_match(db: IntelDatabase) -> None:
    result = db.query(QueryIntelInput(query="zzzznomatch"))
    assert result.count == 0


def test_initialize_is_idempotent(tmp_path: Path) -> None:
    database = IntelDatabase(tmp_path / "intel.db")
    database.initialize()
    database.initialize()  # second call must not duplicate rows
    result = database.query(QueryIntelInput(query="corridor"))
    # The two seeded corridor rows, not four.
    assert result.count == 2


def test_query_does_not_execute_sql(db: IntelDatabase) -> None:
    # A SQL-injection-style payload is treated as a literal search term, not SQL.
    result = db.query(QueryIntelInput(query="'; DROP TABLE intel_reports; --"))
    assert result.count == 0
    # Table still intact and queryable afterwards.
    assert db.query(QueryIntelInput(query="corridor")).count == 2
