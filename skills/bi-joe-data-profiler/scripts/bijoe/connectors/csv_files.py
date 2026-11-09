"""CSV / TSV files: one file, or a folder where every file is a table."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence, Tuple

from . import register
from ._util import unique_names
from .base import ColumnInfo, Connector, ConnectorError, TableInfo

CSV_SUFFIXES = {".csv", ".tsv", ".txt"}
_SAMPLE_BYTES = 1 << 16


def detect_encoding(path: Path) -> str:
    with path.open("rb") as fh:
        raw = fh.read(_SAMPLE_BYTES)
    if raw.startswith(b"\xef\xbb\xbf"):
        return "utf-8-sig"
    try:
        raw.decode("utf-8")
        return "utf-8"
    except UnicodeDecodeError as exc:
        if exc.start >= len(raw) - 3:  # sample cut in the middle of a character
            return "utf-8"
    try:
        raw.decode("cp1252")
        return "cp1252"
    except UnicodeDecodeError:
        return "latin-1"


@register
class CsvConnector(Connector):
    name = "csv"
    label = "CSV/TSV files: a single file, or a folder where each file is one table"
    source_type = "files"
    priority = 20

    @classmethod
    def can_handle(cls, source: str) -> bool:
        p = Path(source)
        if p.is_file():
            return p.suffix.lower() in CSV_SUFFIXES
        if p.is_dir():
            return any(f.is_file() and f.suffix.lower() in CSV_SUFFIXES for f in p.iterdir())
        return False

    def __init__(self, source: str, **options: Any) -> None:
        super().__init__(source, **options)
        p = Path(source)
        if p.is_file():
            files = [p]
        elif p.is_dir():
            files = sorted(f for f in p.iterdir() if f.is_file() and f.suffix.lower() in CSV_SUFFIXES)
        else:
            raise ConnectorError(f"Path not found: {source}")
        if not files:
            raise ConnectorError(f"No .csv/.tsv/.txt files in {source}")
        self._files: Dict[str, Path] = {}
        for f in files:
            name, n = f.stem, 2
            while name in self._files:
                name = f"{f.stem}_{n}"
                n += 1
            self._files[name] = f
        self._formats: Dict[str, Tuple[str, Any]] = {}

    def _format(self, table: str) -> Tuple[str, Any]:
        if table not in self._formats:
            path = self._files[table]
            encoding = detect_encoding(path)
            if path.suffix.lower() == ".tsv":
                dialect: Any = csv.excel_tab
            else:
                with path.open(encoding=encoding, newline="", errors="replace") as fh:
                    sample = fh.read(_SAMPLE_BYTES)
                try:
                    dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
                except csv.Error:
                    dialect = csv.excel
            self._formats[table] = (encoding, dialect)
        return self._formats[table]

    def _reader(self, table: str):
        encoding, dialect = self._format(table)
        fh = self._files[table].open(encoding=encoding, newline="", errors="replace")
        return fh, csv.reader(fh, dialect)

    def list_tables(self) -> List[str]:
        return list(self._files)

    def describe_table(self, table: str) -> TableInfo:
        fh, reader = self._reader(table)
        with fh:
            header = next(reader, [])
        encoding, dialect = self._format(table)
        return TableInfo(
            name=table,
            columns=[ColumnInfo(n) for n in unique_names(header)],
            details={
                "file": self._files[table].name,
                "encoding": encoding,
                "delimiter": dialect.delimiter,
            },
        )

    def iter_rows(self, table: str, limit: Optional[int] = None) -> Iterator[Sequence[Any]]:
        fh, reader = self._reader(table)
        with fh:
            next(reader, None)  # header
            count = 0
            for row in reader:
                if not row:
                    continue  # blank line
                if limit is not None and count >= limit:
                    break
                count += 1
                yield row

    def display_source(self) -> str:
        p = Path(self.source)
        if p.is_file():
            return p.name
        return f"{p.resolve().name}/ ({len(self._files)} files)"
