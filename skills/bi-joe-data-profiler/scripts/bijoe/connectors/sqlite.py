"""SQLite database files, using only the Python standard library. Opened read-only."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Iterator, List, Optional, Sequence

from . import register
from .base import ColumnInfo, Connector, ConnectorError, TableInfo

SQLITE_SUFFIXES = {".db", ".sqlite", ".sqlite3"}
_PREFIX = "sqlite:///"


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


@register
class SqliteConnector(Connector):
    name = "sqlite"
    label = "SQLite database file (.db/.sqlite/.sqlite3, or sqlite:///path)"
    source_type = "database"
    priority = 10

    @classmethod
    def can_handle(cls, source: str) -> bool:
        if source.lower().startswith(_PREFIX):
            return True
        p = Path(source)
        return p.is_file() and p.suffix.lower() in SQLITE_SUFFIXES

    def __init__(self, source: str, **options: Any) -> None:
        super().__init__(source, **options)
        path = source[len(_PREFIX):] if source.lower().startswith(_PREFIX) else source
        p = Path(path)
        if not p.is_file():
            raise ConnectorError(f"SQLite file not found: {path}")
        self._path = p
        self._con = sqlite3.connect(p.resolve().as_uri() + "?mode=ro", uri=True)

    def list_tables(self) -> List[str]:
        rows = self._con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [r[0] for r in rows]

    def describe_table(self, table: str) -> TableInfo:
        info = self._con.execute(f"PRAGMA table_info({_quote(table)})").fetchall()
        columns = [
            ColumnInfo(
                name=row[1],
                declared_type=row[2] or None,
                nullable=not bool(row[3]),
                primary_key=bool(row[5]),
            )
            for row in info
        ]
        count = self._con.execute(f"SELECT COUNT(*) FROM {_quote(table)}").fetchone()[0]
        return TableInfo(name=table, columns=columns, row_count=count)

    def iter_rows(self, table: str, limit: Optional[int] = None) -> Iterator[Sequence[Any]]:
        sql = f"SELECT * FROM {_quote(table)}"
        params: tuple = ()
        if limit is not None:
            sql += " LIMIT ?"
            params = (limit,)
        yield from self._con.execute(sql, params)

    def display_source(self) -> str:
        return self._path.name

    def close(self) -> None:
        self._con.close()
