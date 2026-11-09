"""Any database SQLAlchemy can reach: PostgreSQL, MySQL, SQL Server / Azure SQL,
Snowflake, BigQuery, Databricks, DuckDB, Oracle...

Install SQLAlchemy plus the driver for your database, for example:
    PostgreSQL   pip install sqlalchemy psycopg[binary]       postgresql+psycopg://user@host/db
    MySQL        pip install sqlalchemy pymysql               mysql+pymysql://user@host/db
    SQL Server   pip install sqlalchemy pyodbc                mssql+pyodbc://user@dsn
    Snowflake    pip install snowflake-sqlalchemy             snowflake://user@account/db/schema
    BigQuery     pip install sqlalchemy-bigquery              bigquery://project/dataset
    Databricks   pip install databricks-sqlalchemy            databricks://token:...@host?http_path=...
    DuckDB       pip install duckdb-engine                    duckdb:///path/file.duckdb

Table and column comments stored in the database (COMMENT ON, MS_Description, ...) are
read through SQLAlchemy's inspector and passed on as system metadata.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Iterator, List, Optional, Sequence

from . import register
from .base import ColumnInfo, Connector, ConnectorError, TableInfo

_URL_RE = re.compile(r"^[a-z][a-z0-9+_.-]*://", re.IGNORECASE)


@register
class SqlAlchemyConnector(Connector):
    name = "sqlalchemy"
    label = (
        "Any database with a SQLAlchemy URL: PostgreSQL, MySQL, SQL Server, Snowflake, "
        "BigQuery, Databricks, DuckDB... (needs the database's driver)"
    )
    source_type = "database"
    requires = ("sqlalchemy",)
    install_hint = "sqlalchemy  (plus your database driver, e.g. psycopg, pymysql, pyodbc)"
    priority = 1000  # generic fallback: specific connectors win

    @classmethod
    def can_handle(cls, source: str) -> bool:
        return bool(_URL_RE.match(source))

    def __init__(self, source: str, **options: Any) -> None:
        super().__init__(source, **options)
        import sqlalchemy as sa

        self._sa = sa
        self.schema: Optional[str] = options.get("schema")
        try:
            self._engine = sa.create_engine(source)
            self._insp = sa.inspect(self._engine)
        except Exception as exc:
            raise ConnectorError(f"Could not connect: {type(exc).__name__}: {exc}") from exc
        self._tables: Dict[str, Any] = {}

    def _table(self, table: str):
        if table not in self._tables:
            self._tables[table] = self._sa.Table(
                table, self._sa.MetaData(), autoload_with=self._engine, schema=self.schema
            )
        return self._tables[table]

    def list_tables(self) -> List[str]:
        return list(self._insp.get_table_names(schema=self.schema))

    def describe_table(self, table: str) -> TableInfo:
        insp, schema = self._insp, self.schema
        try:
            pk = set(insp.get_pk_constraint(table, schema=schema).get("constrained_columns") or [])
        except Exception:
            pk = set()
        try:
            comment = (insp.get_table_comment(table, schema=schema) or {}).get("text")
        except Exception:  # NotImplementedError on dialects without comments
            comment = None
        columns = []
        for col in insp.get_columns(table, schema=schema):
            try:
                declared = str(col["type"])
            except Exception:
                declared = type(col["type"]).__name__
            columns.append(
                ColumnInfo(
                    name=col["name"],
                    declared_type=declared,
                    nullable=col.get("nullable"),
                    primary_key=col["name"] in pk,
                    comment=col.get("comment"),
                )
            )
        sa = self._sa
        with self._engine.connect() as conn:
            count = conn.execute(sa.select(sa.func.count()).select_from(self._table(table))).scalar()
        details = {"schema": schema} if schema else {}
        return TableInfo(name=table, columns=columns, comment=comment or None, row_count=count, details=details)

    def iter_rows(self, table: str, limit: Optional[int] = None) -> Iterator[Sequence[Any]]:
        stmt = self._sa.select(self._table(table))
        if limit is not None:
            stmt = stmt.limit(limit)
        with self._engine.connect() as conn:
            result = conn.execution_options(stream_results=True).execute(stmt)
            for row in result:
                yield tuple(row)

    def display_source(self) -> str:
        try:
            return self._sa.engine.make_url(self.source).render_as_string(hide_password=True)
        except Exception:
            return re.sub(r"(://[^:/@]+):[^@]*@", r"\1:***@", self.source)

    def close(self) -> None:
        self._engine.dispose()
