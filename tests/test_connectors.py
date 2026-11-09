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
