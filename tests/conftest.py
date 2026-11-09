import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def shop_csv(tmp_path: Path) -> Path:
    d = tmp_path / "shop"
    d.mkdir()
    (d / "customers.csv").write_text(
        "cust_id,name,country,signup_date,zip\n"
        "1,Ann,DK,2024-01-03,0800\n"
        "2,Bo,SE,2024-02-10,2100\n"
        "3,Cy,,2024-03-01,0900\n"
        "4,Di,DK,2024-04-05, 0800\n",
        encoding="utf-8",
    )
    (d / "orders.csv").write_text(
        "order_id;cust_id;amount;status\n"
        "100;1;19.95;shipped\n"
        "101;2;5;open\n"
        "102;1;abc;shipped\n"
        "102;1;abc;shipped\n",
        encoding="utf-8",
    )
    return d


@pytest.fixture
def shop_sqlite(tmp_path: Path) -> Path:
    p = tmp_path / "shop.db"
    con = sqlite3.connect(p)
    con.executescript(
        """
        CREATE TABLE customers (cust_id INTEGER PRIMARY KEY, name TEXT NOT NULL, created_at TEXT);
        INSERT INTO customers VALUES (1, 'Ann', '2024-01-03 10:00:00'), (2, 'Bo', NULL), (3, 'Cy', '2024-05-01 08:30:00');
        CREATE TABLE "order lines" (id INTEGER, cust_id INTEGER, price REAL);
        INSERT INTO "order lines" VALUES (1, 1, 9.5), (2, 1, 3.25), (3, 3, NULL);
        """
    )
    con.commit()
    con.close()
    return p
