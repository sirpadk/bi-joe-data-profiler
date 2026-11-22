"""A stub connector for the progress and timing tests: configurable tables, rows and a table that fails."""
from typing import Any, Iterator, List, Optional, Sequence

from bijoe.connectors import ColumnInfo, Connector, TableInfo, register


@register
class ProgressStub(Connector):
    name = "stubprog"
    label = "test only"
    source_type = "database"

    TABLES: List[str] = ["alpha", "beta", "gamma"]
    FAIL_ON: Optional[str] = None
    FAIL_EXC: Any = RuntimeError
    FAIL_MSG: str = "boom"
    VALUE: Any = "plain"

    @classmethod
    def can_handle(cls, source: str) -> bool:
        return source.startswith("stubprog://")

    def list_tables(self) -> List[str]:
        return list(self.TABLES)

    def describe_table(self, table: str) -> TableInfo:
        return TableInfo(table, [ColumnInfo("id", "INT", primary_key=True), ColumnInfo("label", "TEXT")], None, 3)

    def iter_rows(self, table: str, limit: Optional[int] = None) -> Iterator[Sequence[Any]]:
        if self.FAIL_ON == table:
            raise self.FAIL_EXC(self.FAIL_MSG)
        yield from [(1, self.VALUE), (2, self.VALUE), (3, self.VALUE)][:limit]

    def display_source(self) -> str:
        return "stubprog://x"
