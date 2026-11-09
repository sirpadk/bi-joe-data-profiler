"""Template for a new BI Joe connector. Copy, rename, and fill in the TODOs.

Inside this repo:  save as skills/bi-joe-data-profiler/scripts/bijoe/connectors/<name>.py
                   and import it in connectors/__init__.py::_ensure_loaded().
As a package:      keep it in your own package and declare an entry point
                   under "bijoe.connectors" (see CONTRIBUTING.md).
"""

from __future__ import annotations

from typing import Any, Iterator, List, Optional, Sequence

from bijoe.connectors import ColumnInfo, Connector, ConnectorError, TableInfo, register


@register
class ExampleConnector(Connector):
    name = "example"                      # TODO: short id for --connector
    label = "Example source (describe what the user passes as <source>)"
    source_type = "database"              # "files" or "database"
    requires = ("example_driver",)        # TODO: importable modules needed
    install_hint = "example-driver"       # TODO: what to pip install
    priority = 50                         # lower = tried earlier during auto-detection

    @classmethod
    def can_handle(cls, source: str) -> bool:
        return source.startswith("example://")  # TODO

    def __init__(self, source: str, **options: Any) -> None:
        super().__init__(source, **options)
        import example_driver  # optional dependency: import here, not at the top

        try:
            self._conn = example_driver.connect(source, read_only=True)
        except Exception as exc:
            raise ConnectorError(f"Could not connect: {exc}") from exc

    def list_tables(self) -> List[str]:
        return self._conn.tables()  # TODO

    def describe_table(self, table: str) -> TableInfo:
        cols = [
            ColumnInfo(name=c.name, declared_type=c.type, nullable=c.nullable,
                       primary_key=c.is_pk, comment=c.description)
            for c in self._conn.columns(table)  # TODO
        ]
        return TableInfo(
            name=table,
            columns=cols,
            comment=self._conn.table_description(table),  # the source's own description, or None
            row_count=self._conn.count(table),            # or None if counting is expensive
        )

    def iter_rows(self, table: str, limit: Optional[int] = None) -> Iterator[Sequence[Any]]:
        yield from self._conn.select_all(table, limit=limit)  # TODO: must respect limit

    def display_source(self) -> str:
        return "example://host/db"  # TODO: never include passwords or tokens

    def close(self) -> None:
        self._conn.close()
