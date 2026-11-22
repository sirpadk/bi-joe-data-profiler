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
        # schema: one name, a comma-separated list, or "all" (every non-system schema). With several
        # schemas the tables are named Schema.Table so equal names in different schemas stay apart.
        self.schema_option: Optional[str] = options.get("schema")
        self._where: Dict[str, Any] = {}  # table name as shown -> (schema, table)
        try:
            self._engine = sa.create_engine(source)
            self._insp = sa.inspect(self._engine)
        except Exception as exc:
            raise ConnectorError(f"Could not connect: {type(exc).__name__}: {exc}") from exc
        self._tables: Dict[str, Any] = {}

    def _schemas(self) -> List[Optional[str]]:
        option = (self.schema_option or "").strip()
        if not option:
            return [None]
        if option.lower() in ("all", "*"):
            skip = {"sys", "information_schema", "guest", "pg_catalog", "pg_toast"}
            names = [n for n in self._insp.get_schema_names()
                     if n.lower() not in skip and not n.lower().startswith(("db_", "pg_temp", "pg_toast_temp"))]
            return names or [None]
        return [n.strip() for n in option.split(",") if n.strip()]

    def _table(self, table: str):
        if table not in self._tables:
            schema, name = self._where.get(table, (None, table))
            self._tables[table] = self._sa.Table(name, self._sa.MetaData(), autoload_with=self._engine, schema=schema)
        return self._tables[table]

    def list_tables(self) -> List[str]:
        schemas = self._schemas()
        out: List[str] = []
        for schema in schemas:
            for name in self._insp.get_table_names(schema=schema):
                shown = f"{schema}.{name}" if len(schemas) > 1 else name
                self._where[shown] = (schema, name)
                out.append(shown)
        return out

    def describe_table(self, table: str) -> TableInfo:
        insp = self._insp
        if not self._where:
            self.list_tables()
        schema, table_name = self._where.get(table, (None, table))
        shown, table = table, table_name
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
            count = conn.execute(sa.select(sa.func.count()).select_from(self._table(shown))).scalar()
        details = {"schema": schema} if schema else {}
        return TableInfo(name=shown, columns=columns, comment=comment or None, row_count=count, details=details)

    def iter_rows(self, table: str, limit: Optional[int] = None) -> Iterator[Sequence[Any]]:
        sa = self._sa
        # Types the driver cannot read (SQL Server hierarchyid, geography, geometry...) are fetched as text.
        columns = [sa.cast(c, sa.String).label(c.name) if isinstance(c.type, sa.types.NullType) else c
                   for c in self._table(table).columns]
        stmt = sa.select(*columns)
        if limit is not None:
            stmt = stmt.limit(limit)
        with self._engine.connect() as conn:
            result = conn.execution_options(stream_results=True).execute(stmt)
            for row in result:
                yield tuple(row)

    def display_source(self) -> str:
        if "odbc_connect=" in self.source:  # SQL Server: show the server and database, never a password
            from urllib.parse import unquote_plus
            text = unquote_plus(self.source.split("odbc_connect=", 1)[1])
            part = lambda key: (re.search(rf"(?i)(?:^|;){key}=([^;]*)", text) or [None, ""])[1].strip("{}")
            server, database = part("SERVER"), part("DATABASE")
            if server:
                return f"mssql://{server}/{database}" if database else f"mssql://{server}"
        try:
            return self._sa.engine.make_url(self.source).render_as_string(hide_password=True)
        except Exception:
            return re.sub(r"(://[^:/@]+):[^@]*@", r"\1:***@", self.source)

    def close(self) -> None:
        self._engine.dispose()
