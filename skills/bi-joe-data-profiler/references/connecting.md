# Connecting to a Source

Everything starts with one command:

```
python <skill-dir>/scripts/run_bijoe.py profile "<source>" --out "<out-dir>" [options]
```

`<skill-dir>` is the folder that holds `SKILL.md`. The `<source>` depends on what the user has.
Run `python <skill-dir>/scripts/run_bijoe.py connectors` to see which sources work right now.
Anything marked `[needs: ...]` needs a package first. **Ask the user before installing anything.**

## Rules That Apply to Every Source

- **Read-only.** BI Joe only reads. It never changes the source. A read-only login is best.
- **Tables only.** Views, stored procedures and functions are never read.
- **Passwords.** Never ask the user to type a password into the chat, and never write one in a
  command. Ask them to put it in an environment variable, then refer to it as `${NAME}` in the URL.
  Put the URL in single quotes so the shell does not expand it first. The engine expands it at
  run time and hides passwords in everything it writes.
- **Personal data is masked by the engine**, so you never see it (see `SKILL.md`).
- **Sensitive data?** Add `--no-values`. No example values are recorded at all.
- **Big tables.** Statistics use the first 100,000 rows of each table (`--sample-rows N` changes
  it). Row counts stay exact for databases.
- **A part of a database.** `--tables a,b,c` limits the tables. `--schema` limits the schemas (below).

## Files

| Source | Command | Needs |
|---|---|---|
| One CSV or TSV file | `profile "C:\data\sales.csv" --out out` | nothing |
| A folder of CSV files (one table each) | `profile "C:\data\exports" --out out` | nothing |
| Excel workbook (one table per sheet) | `profile "C:\data\book.xlsx" --out out` | `pip install openpyxl` |
| SQLite file | `profile "C:\data\shop.db" --out out` | nothing |

Notes: the CSV encoding and the delimiter (comma, semicolon, tab or pipe) are detected. In Excel, the
first non-empty row of each sheet is read as the column names.

## SQL Server and Azure SQL

Needs `pip install sqlalchemy pyodbc` and a Microsoft ODBC driver (use *ODBC Driver 18 for SQL
Server*; 17 also works). Check what is installed:

```
python <skill-dir>/scripts/make_url.py drivers
```

If it lists nothing, the user must install the driver from Microsoft (search "Download ODBC Driver
for SQL Server") and you must ask them to do that.

Build the URL with the helper. It handles named instances (`host\INSTANCE`), the encoding and the
certificate setting, so nobody has to write a URL by hand.

**Windows login** (nothing to type, runs as the current Windows user):

```
python <skill-dir>/scripts/make_url.py sqlserver --server "host\INSTANCE" --database MyDb --windows-auth
```

**SQL login** (the user puts the password in an environment variable first, for example
`$env:MSSQL_PWD = "..."` in PowerShell):

```
python <skill-dir>/scripts/make_url.py sqlserver --server myserver.database.windows.net --database MyDb --user joe --password-env MSSQL_PWD
```

The helper prints a URL. Use it as the source, in single quotes:

```
python <skill-dir>/scripts/run_bijoe.py profile '<the printed URL>' --schema all --out out --name MyDb
```

- **Schemas.** Without `--schema`, only the default schema (usually `dbo`) is read. Many databases
  keep their tables in several schemas (AdventureWorks has five). Use `--schema all` for every
  non-system schema, or `--schema Sales,Production` for some. With several schemas, tables are
  named `Schema.Table`.
- **Descriptions already in the database** (the `MS_Description` extended property) are read and
  used word for word.
- **One database per run.** To profile three databases, run three times with different `--out` folders.
- **Certificate errors** ("certificate verify failed"): the helper already trusts the server
  certificate. For a server with a proper certificate, add `--no-trust-cert`.
- **"Data source name not found" or "driver not found":** the ODBC driver is missing or the name is
  wrong. Run the `drivers` command above.
- **Login failed:** check the login can read the database (`db_datareader` is enough).
- **Cannot reach the server:** firewall, VPN or the wrong instance name. For a named instance the
  SQL Server Browser service must be running, or add the port: `--server "host,1433"`.

## PostgreSQL

`pip install sqlalchemy "psycopg[binary]"`

```
python <skill-dir>/scripts/run_bijoe.py profile 'postgresql+psycopg://joe:${PGPASSWORD}@host:5432/mydb' --schema public --out out
```

Use `--schema all` to read every schema. Comments set with `COMMENT ON` are used word for word.

## MySQL and MariaDB

`pip install sqlalchemy pymysql`

```
python <skill-dir>/scripts/run_bijoe.py profile 'mysql+pymysql://joe:${MYSQL_PWD}@host:3306/mydb' --out out
```

In MySQL a "database" and a "schema" are the same thing, so the database in the URL is the one read.

## Snowflake

`pip install snowflake-sqlalchemy`

```
python <skill-dir>/scripts/run_bijoe.py profile 'snowflake://joe:${SF_PWD}@myaccount/MYDB/PUBLIC?warehouse=MYWH&role=MYROLE' --out out
```

The account is the part before `.snowflakecomputing.com`, for example `xy12345.eu-west-1`.

## Google BigQuery

`pip install sqlalchemy-bigquery`. Sign in first with `gcloud auth application-default login`
(or set `GOOGLE_APPLICATION_CREDENTIALS` to a service-account key file).

```
python <skill-dir>/scripts/run_bijoe.py profile 'bigquery://my-project/my_dataset' --out out
```

## Databricks

`pip install databricks-sqlalchemy`. The user needs a personal access token in an environment
variable, plus the server host name and the HTTP path of a SQL warehouse.

```
python <skill-dir>/scripts/run_bijoe.py profile 'databricks://token:${DATABRICKS_TOKEN}@myhost.cloud.databricks.com?http_path=/sql/1.0/warehouses/abc123&catalog=main&schema=default' --out out
```

## DuckDB

`pip install duckdb-engine`

```
python <skill-dir>/scripts/run_bijoe.py profile 'duckdb:///C:/data/analytics.duckdb' --out out
```

## Oracle and Everything Else SQLAlchemy Knows

Any database that SQLAlchemy has a driver for works through the same connector. Install the driver,
build the URL the way that driver documents it, and pass it as the source. For example Oracle:
`pip install sqlalchemy oracledb`, then `'oracle+oracledb://joe:${ORA_PWD}@host:1521/?service_name=ORCL'`.

## A Source Nothing Supports

1. **Export to CSV.** Most tools can. Profile the folder of CSV files.
2. **Write a connector.** Three small methods. See `CONTRIBUTING.md` in the project repository and
   the template `docs/connector_template.py`.
3. **No code at all.** Use the manual method in `manual-profiling.md`.

## What Was Tested

CSV, Excel, SQLite and SQL Server (Windows login, named instance, several schemas) have been run
against real data. The other databases are supported through the same connector but have not yet been tested
against live servers. If one fails, show the user the exact error and the one thing to do next.
