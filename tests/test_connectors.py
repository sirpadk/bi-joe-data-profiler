import pytest

from bijoe.connectors import ConnectorError, available, open_connector, resolve
from bijoe.profiler import profile_source


def test_builtins_registered():
    names = [c.name for c in available()]
    assert names[:3] == ["sqlite", "csv", "excel"] and names[-1] == "sqlalchemy"


def test_unknown_source():
    with pytest.raises(ConnectorError):
        resolve("definitely-not-a-file.xyz")


def test_excel(tmp_path):
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products"
    ws.append([None])  # blank first row: header detection must skip it
    ws.append(["sku", "price", None])
    ws.append(["A1", 9.99])
    ws.append(["B2", 12])
    wb.create_sheet("Empty")
    path = tmp_path / "catalog.xlsx"
    wb.save(path)

    with open_connector(str(path)) as conn:
        assert conn.name == "excel"
        tables = {t["name"]: t for t in profile_source(conn)}
    products = tables["Products"]
    assert products["column_count"] == 2 and products["row_count"] == 2
    assert products["columns"][1]["inferred_type"] == "decimal"
    assert tables["Empty"]["row_count"] == 0


def test_sqlalchemy_generic_and_password_hidden(shop_sqlite):
    pytest.importorskip("sqlalchemy")
    with open_connector(f"sqlite:///{shop_sqlite.as_posix()}", "sqlalchemy") as conn:
        tables = {t["name"]: t for t in profile_source(conn)}
    assert tables["customers"]["row_count"] == 3

    from bijoe.connectors.sqlalchemy_db import SqlAlchemyConnector

    c = SqlAlchemyConnector.__new__(SqlAlchemyConnector)
    import sqlalchemy

    c._sa, c.source = sqlalchemy, "postgresql://joe:s3cret@host/db"
    assert "s3cret" not in c.display_source()


def test_sql_server_url_is_shown_without_secrets():
    from bijoe.connectors.sqlalchemy_db import SqlAlchemyConnector
    from urllib.parse import quote_plus
    odbc = r"DRIVER={ODBC Driver 18 for SQL Server};SERVER=host\inst;DATABASE=pubs;UID=joe;PWD=hunter2;Trusted_Connection=no"
    c = SqlAlchemyConnector.__new__(SqlAlchemyConnector)
    c.source = "mssql+pyodbc:///?odbc_connect=" + quote_plus(odbc)
    shown = c.display_source()
    assert shown == "mssql://host\inst/pubs" and "hunter2" not in shown


def test_make_url_and_env_password_expansion(monkeypatch):
    import subprocess, sys
    from pathlib import Path
    from urllib.parse import unquote_plus
    from bijoe.cli import expand_source
    script = Path(__file__).resolve().parents[1] / "skills" / "bi-joe-data-profiler" / "scripts" / "make_url.py"
    url = subprocess.run([sys.executable, str(script), "sqlserver", "--server", r"host\inst", "--database", "pubs",
                          "--user", "joe", "--password-env", "MSSQL_PWD"], capture_output=True, text=True, check=True).stdout.strip()
    assert url.startswith("mssql+pyodbc:///?odbc_connect=") and "MSSQL_PWD" in unquote_plus(url) and "hunter2" not in url
    monkeypatch.setenv("MSSQL_PWD", "p@ss;w=rd")
    assert "PWD=p@ss;w=rd" in unquote_plus(expand_source(url))
    win = subprocess.run([sys.executable, str(script), "sqlserver", "--server", "h", "--database", "d", "--windows-auth"],
                         capture_output=True, text=True, check=True).stdout
    assert "Trusted_Connection%3Dyes" in win
