"""Intelligence database service backed by synthetic SQLite data.

Business logic for the ``query_intel_db`` MCP tool. Creates and seeds a small
synthetic SQLite database on first use, and exposes a *keyword* search via
parameterized SQL (no arbitrary SQL execution, no injection surface).
"""

import sqlite3
from pathlib import Path

import structlog

from miltech_demo.schemas import IntelRecord, QueryIntelInput, QueryIntelResult

logger = structlog.get_logger(__name__)

_SCHEMA = """
CREATE TABLE IF NOT EXISTS intel_reports (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    region TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    summary TEXT NOT NULL,
    reported_at TEXT NOT NULL
)
"""

# (title, region, category, severity, summary, reported_at)
_SEED: list[tuple[str, str, str, str, str, str]] = [
    ("Convoy movement detected", "east", "movement", "medium",
     "Light transport convoy moving toward the eastern corridor.", "2026-06-10"),
    ("Border patrol surge", "north", "security", "high",
     "Patrol density increased after unauthorized crossing reports.", "2026-06-11"),
    ("Rail disruption resolved", "west", "logistics", "low",
     "Minor rail disruption on western supply lines resolved in 48h.", "2026-06-12"),
    ("Unidentified aerial activity", "south", "air", "high",
     "Probable reconnaissance flights detected near the southern coast.", "2026-06-13"),
    ("Fuel stock replenished", "west", "logistics", "low",
     "Fuel and ammunition stocks restored to sustainable levels.", "2026-06-14"),
    ("Night corridor traffic", "east", "movement", "medium",
     "Increased nighttime traffic observed along the eastern corridor.", "2026-06-15"),
]


class IntelDatabase:
    """Manages the synthetic intel SQLite database."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self._db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def initialize(self) -> None:
        """Create the schema and seed synthetic rows if the table is empty."""
        with self._connect() as connection:
            connection.execute(_SCHEMA)
            (count,) = connection.execute("SELECT COUNT(*) FROM intel_reports").fetchone()
            if count == 0:
                connection.executemany(
                    "INSERT INTO intel_reports "
                    "(title, region, category, severity, summary, reported_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)",
                    _SEED,
                )
                logger.info("intel_db_seeded", rows=len(_SEED), path=str(self._db_path))

    def query(self, params: QueryIntelInput) -> QueryIntelResult:
        """Keyword search across title/region/category/summary (parameterized)."""
        like = f"%{params.query}%"
        sql = (
            "SELECT id, title, region, category, severity, summary, reported_at "
            "FROM intel_reports "
            "WHERE title LIKE ? OR region LIKE ? OR category LIKE ? OR summary LIKE ? "
            "ORDER BY reported_at DESC LIMIT ?"
        )
        with self._connect() as connection:
            cursor = connection.execute(sql, (like, like, like, like, params.limit))
            rows = [
                IntelRecord(
                    id=row["id"],
                    title=row["title"],
                    region=row["region"],
                    category=row["category"],
                    severity=row["severity"],
                    summary=row["summary"],
                    reported_at=row["reported_at"],
                )
                for row in cursor.fetchall()
            ]
        return QueryIntelResult(query=params.query, rows=rows, count=len(rows))
