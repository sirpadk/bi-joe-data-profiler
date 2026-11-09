# BI Joe: data profiler

An AI skill that turns any dataset into a clear, standardised profile. No data-profiling
experience is needed.

Give it a CSV file, an Excel workbook, a SQLite file, or a live database. It asks you a
few questions, adapted to how much you already know, then publishes a **Markdown wiki**
that both people and AI agents can read:

```
bijoe-profile/
  index.md                 landing page: summary + links to every table
  data-stories/
    customers.md           one "data story" per table
    orders.md
  _bijoe/
    profile.json           measured facts
    descriptions.json      descriptions, with where each one came from
```

Each data story gives the table's name and a description:
- If the source system already stores a description, it is used **word for word**.
- If not, the AI writes one **from evidence it can point to**: column names, types,
  ranges and values. It labels the description with a confidence level and lists any
  open questions for the data owner.
- A built-in checker flags descriptions that are invented or that only state the obvious.

**See a real example:** [`examples/shoe_company`](examples/shoe_company/index.md) was
built from [`sample/shoe_company.xlsx`](sample/shoe_company.xlsx).

> Status: early MVP. Coming next: column-level stories, data-quality findings,
> relationships between tables, and schema-only (DDL) input.

## Use it with Claude

Copy or symlink `skills/bi-joe-data-profiler` into your skills folder:

| Where | Path |
|---|---|
| Claude Code (personal) | `~/.claude/skills/bi-joe-data-profiler` |
| Claude Code (one project) | `<project>/.claude/skills/bi-joe-data-profiler` |
| Claude.ai / Claude Desktop | Zip the folder and upload it under *Settings → Capabilities → Skills* |

Then just ask: *"Profile the data in `C:\exports\sales`."*

## Use it with other AI agents

The skill is plain Markdown plus a Python script, so any agent that can read files and
run commands can use it. Point your agent at [`AGENTS.md`](AGENTS.md), or copy the skill
folder to wherever your tool loads skills from. If the agent can't run code, the skill
includes a manual method that produces the same wiki.

## Use the engine directly

Requires Python 3.9 or newer. CSV and SQLite need nothing else.

```bash
python skills/bi-joe-data-profiler/scripts/run_bijoe.py profile ./my-data --out ./bijoe-profile
python skills/bi-joe-data-profiler/scripts/run_bijoe.py evidence ./bijoe-profile   # facts for writing descriptions
# fill in ./bijoe-profile/_bijoe/descriptions.json
python skills/bi-joe-data-profiler/scripts/run_bijoe.py check ./bijoe-profile
python skills/bi-joe-data-profiler/scripts/run_bijoe.py render ./bijoe-profile
```

Or install it to get the `bijoe` command: `pip install -e .[excel,sql]`.

| Source | Example | Extra install |
|---|---|---|
| CSV/TSV file or folder | `./exports` | none |
| Excel | `sales.xlsx` | `openpyxl` |
| SQLite | `shop.db` | none |
| PostgreSQL | `'postgresql+psycopg://joe:${PGPASSWORD}@host/db'` | `sqlalchemy psycopg[binary]` |
| SQL Server / Azure SQL | `'mssql+pyodbc://joe:${MSSQL_PWD}@my-dsn'` | `sqlalchemy pyodbc` |
| MySQL | `'mysql+pymysql://joe:${MYSQL_PWD}@host/db'` | `sqlalchemy pymysql` |
| Snowflake | `'snowflake://joe:${SF_PWD}@account/db/schema'` | `snowflake-sqlalchemy` |
| BigQuery | `bigquery://project/dataset` | `sqlalchemy-bigquery` |
| Databricks | `'databricks://token:${DATABRICKS_TOKEN}@host?http_path=...'` | `databricks-sqlalchemy` |
| DuckDB | `duckdb:///file.duckdb` | `duckdb-engine` |

Put passwords in environment variables, as in the examples. `${VAR}` is expanded at run
time, and passwords are hidden in everything BI Joe writes. Wrap the URL in single quotes
so your shell doesn't expand the variable first.

## Add a data connector

Connectors are small plugins: three methods, usually under 100 lines. You can add one to
this repo or publish it as your own package. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
