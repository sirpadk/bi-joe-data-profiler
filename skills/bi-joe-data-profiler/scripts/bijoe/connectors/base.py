"""The contract every data connector implements.

A connector knows how to reach one kind of source (CSV files, an Excel workbook,
a database, ...). It answers three questions and nothing more:

1. Which tables are there?            -> list_tables()
2. What does a table look like?        -> describe_table()   (columns, comments, row count)
3. Give me the rows.                   -> iter_rows()

All profiling logic lives elsewhere, so a new connector is usually under 100 lines.
See CONTRIBUTING.md and docs/connector_template.py.
"""

from __future__ import annotations

import importlib.util
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, Dict, Iterator, List, Optional, Sequence


class ConnectorError(Exception):
    """A problem the user can act on (missing file, missing driver, bad URL...)."""


@dataclass
class ColumnInfo:
    name: str
    declared_type: Optional[str] = None  # type as declared by the source, if it has one
    nullable: Optional[bool] = None
    primary_key: bool = False
    comment: Optional[str] = None  # column description stored in the source system


@dataclass
class TableInfo:
    name: str
    columns: List[ColumnInfo]
    comment: Optional[str] = None  # table description stored in the source system
    row_count: Optional[int] = None  # exact count if cheap to get; None = profiler counts while reading
    details: Dict[str, Any] = field(default_factory=dict)  # free-form facts (file name, encoding, schema...)


class Connector(ABC):
    #: short unique id used on the command line (`--connector csv`)
    name: ClassVar[str] = ""
    #: one-line human description shown by `bijoe connectors`
    label: ClassVar[str] = ""
    #: "files" or "database"
    source_type: ClassVar[str] = "files"
    #: importable module names this connector needs (checked before use)
    requires: ClassVar[Sequence[str]] = ()
    #: what to tell the user to pip install when requirements are missing
    install_hint: ClassVar[str] = ""
    #: lower runs first when auto-detecting the connector for a source
    priority: ClassVar[int] = 100

    def __init__(self, source: str, **options: Any) -> None:
        self.source = source
        self.options = options

    # ---- detection -------------------------------------------------------
    @classmethod
    def can_handle(cls, source: str) -> bool:
        """Return True if this connector recognises `source` (a path or URL)."""
        return False

    @classmethod
    def missing_requirements(cls) -> List[str]:
        return [m for m in cls.requires if importlib.util.find_spec(m) is None]

    # ---- the contract ----------------------------------------------------
    @abstractmethod
    def list_tables(self) -> List[str]:
        """Names of the tables (or sheets, or files) available in the source."""

    @abstractmethod
    def describe_table(self, table: str) -> TableInfo:
        """Columns and any metadata the source stores about the table."""

    @abstractmethod
    def iter_rows(self, table: str, limit: Optional[int] = None) -> Iterator[Sequence[Any]]:
        """Yield rows as sequences, in column order. Stop after `limit` rows if given."""

    # ---- optional --------------------------------------------------------
    def display_source(self) -> str:
        """How the source is shown in reports. Must never include secrets."""
        return self.source

    def close(self) -> None:
        pass

    def __enter__(self) -> "Connector":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
