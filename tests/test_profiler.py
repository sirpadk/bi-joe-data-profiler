import datetime as dt

from bijoe.connectors import open_connector
from bijoe.profiler import ColumnStats, profile_source


def _cols(table):
    return {c["name"]: c for c in table["columns"]}


def test_csv_folder_types_and_flags(shop_csv):
    with open_connector(str(shop_csv)) as conn:
        assert conn.name == "csv"
        tables = {t["name"]: t for t in profile_source(conn)}
    assert set(tables) == {"customers", "orders"}

    cust = _cols(tables["customers"])
    assert cust["cust_id"]["inferred_type"] == "integer"
    assert cust["cust_id"]["all_values_unique"] is True
    assert cust["country"]["missing_count"] == 1
    assert cust["signup_date"]["inferred_type"] == "date"
    assert cust["signup_date"]["min"] == "2024-01-03"
    assert cust["zip"]["leading_zero_count"] == 3
    assert cust["zip"]["whitespace_padded_count"] == 1

    orders = tables["orders"]
    assert orders["details"]["delimiter"] == ";"
    assert orders["duplicate_rows"] == 1
    amount = _cols(orders)["amount"]
    assert amount["inferred_type"] == "text"
    assert amount["value_kinds"] == {"decimal": 1, "integer": 1, "text": 2}


def test_native_values_and_sampling():
    c = ColumnStats("x", 1)
    for v in [1, 2.5, None, float("nan")]:
        c.add(v)
    r = c.result()
    assert r["inferred_type"] == "decimal" and r["null_count"] == 2 and r["max"] == 2.5

    d = ColumnStats("d", 1)
    d.add(dt.date(2024, 1, 1))
    d.add(dt.datetime(2024, 2, 1, 12, 0))
    assert d.result()["inferred_type"] == "datetime"


def test_sqlite_counts_and_sample(shop_sqlite):
    with open_connector(str(shop_sqlite)) as conn:
        assert conn.name == "sqlite"
        tables = {t["name"]: t for t in profile_source(conn, sample_rows=2)}
    cust = tables["customers"]
    assert cust["row_count"] == 3 and cust["profiled_rows"] == 2 and cust["sampled"] is True
    assert _cols(cust)["cust_id"]["primary_key"] is True
    assert "order lines" in tables


def test_table_filter(shop_csv):
    with open_connector(str(shop_csv)) as conn:
        tables = profile_source(conn, tables=["ORDERS"])
    assert [t["name"] for t in tables] == ["orders"]


def test_no_values(shop_csv):
    with open_connector(str(shop_csv)) as conn:
        tables = profile_source(conn, include_values=False)
    assert all("top_values" not in c for t in tables for c in t["columns"])
