"""Excel workbooks: each sheet is a table, the first non-empty row is the header."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Sequence

from . import register
from ._util import unique_names
from .base import ColumnInfo, Connector, ConnectorError, TableInfo

EXCEL_SUFFIXES = {".xlsx", ".xlsm"}


def _empty(v: Any) -> bool:
    return v is None or (isinstance(v, str) and not v.strip())


@register
class ExcelConnector(Connector):
    name = "excel"
    label = "Excel workbooks (.xlsx/.xlsm): one table per sheet"
    source_type = "files"
    requires = ("openpyxl",)
    install_hint = "openpyxl"
    priority = 30

    @classmethod
    def can_handle(cls, source: str) -> bool:
        p = Path(source)
        return p.is_file() and p.suffix.lower() in EXCEL_SUFFIXES

    def __init__(self, source: str, **options: Any) -> None:
        super().__init__(source, **options)
        if not Path(source).is_file():
            raise ConnectorError(f"File not found: {source}")
        self._wb = None
        self._width: Dict[str, int] = {}

    def _book(self):
        if self._wb is None:
            import openpyxl

            self._wb = openpyxl.load_workbook(self.source, read_only=True, data_only=True)
        return self._wb

    def _rows(self, table: str):
        ws = self._book()[table]
        try:
            ws.reset_dimensions()  # stored dimensions are often wrong in exported files
        except AttributeError:
            pass
        it = ws.iter_rows(values_only=True)
        for row in it:
            if not all(_empty(v) for v in row):
                header = list(row)
                while header and _empty(header[-1]):
                    header.pop()
                return header, it
        return [], iter(())

    def list_tables(self) -> List[str]:
        return [ws.title for ws in self._book().worksheets]

    def describe_table(self, table: str) -> TableInfo:
        header, _ = self._rows(table)
        self._width[table] = len(header)
        return TableInfo(
            name=table,
            columns=[ColumnInfo(n) for n in unique_names(header)],
            details={"file": Path(self.source).name, "sheet": table},
        )

    def iter_rows(self, table: str, limit: Optional[int] = None) -> Iterator[Sequence[Any]]:
        header, it = self._rows(table)
        width = len(header)
        count = 0
        for row in it:
            if all(_empty(v) for v in row):
                continue
            if limit is not None and count >= limit:
                break
            count += 1
            yield row[:width]

    def display_source(self) -> str:
        return Path(self.source).name

    def close(self) -> None:
        if self._wb is not None:
            self._wb.close()
            self._wb = None
