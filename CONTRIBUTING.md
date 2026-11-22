# Contributing

Thanks for helping. The most useful contributions are **new data connectors**, better
**description guidance**, and **test datasets** with real-world problems.

## Development setup

```bash
git clone https://github.com/sirpadk/bi-joe-data-profiler
cd bi-joe-data-profiler
python -m venv .venv
.venv/Scripts/pip install -e .[dev,excel,sql]     # on macOS/Linux: .venv/bin/pip
pytest
```

## How the engine is put together

```
skills/bi-joe-data-profiler/scripts/bijoe/
  connectors/      one module per kind of source  ← most contributions go here
  profiler.py      turns rows into facts (types, missing values, ranges, top values)
  descriptions.py  descriptions.json format + the honesty checks
  wiki.py          renders the Markdown wiki
  cli.py           command line
```

Connectors only fetch data. They never compute statistics, so every source gets
exactly the same profile.

## Writing a connector

A connector is a subclass of `bijoe.connectors.Connector` with three methods:

| Method | Returns |
|---|---|
| `list_tables()` | the table names |
| `describe_table(name)` | a `TableInfo`: columns (name, declared type, PK, comment), the table comment, and the row count if it is cheap to get |
| `iter_rows(name, limit)` | rows as tuples, in column order |

There are also two class methods:
- `can_handle(source)`: auto-detection.
- `missing_requirements()`: which optional packages are missing. It works automatically
  once you set `requires`.

Start from [`docs/connector_template.py`](docs/connector_template.py).

Rules:
1. **Read-only.** Never change the source.
2. **Pass through the source's own descriptions** (table and column comments) as
   `comment`. BI Joe uses them as authoritative.
3. **No secrets in `display_source()`.** That string ends up in the wiki.
4. **Import optional dependencies inside the connector**, not at module level, and
   list them in `requires` / `install_hint`.
5. **Respect `limit`.** Profiling large tables depends on it.
6. If `describe_table` can't get the row count cheaply, return `row_count=None`. The
   profiler then counts the rows as it reads them.

### A walk-through

1. **Copy the template** `docs/connector_template.py` to `bijoe/connectors/<name>.py` and rename the class.
2. **Say what you accept.** `can_handle(source)` returns `True` for the strings your connector reads,
   for example `source.startswith("oracle://")` or a file suffix. Auto-detection tries the connectors in
   `priority` order (lower first). The generic database connector has priority 1000, so yours wins.
3. **Connect in `__init__`.** Open the connection read-only. Raise `ConnectorError("a plain sentence")` when it
   fails, with the one thing the user should do next. Options from the command line, such as `--schema`,
   arrive in `**options`.
4. **List the tables.** `list_tables()` returns the names to show. Only tables, never views or procedures.
5. **Describe a table.** `describe_table(name)` returns `TableInfo(name, columns, comment, row_count)`. Fill
   `ColumnInfo(name, declared_type, nullable, primary_key, comment)` from the source's own catalogue, and pass
   every description the source stores as `comment`.
6. **Stream the rows.** `iter_rows(name, limit)` yields tuples in column order and stops at `limit`.
   Use a server-side cursor if the driver has one, so a large table is never loaded at once.
7. **Hide secrets.** `display_source()` returns the source without passwords. It is written into the wiki.
8. **Test it** with a tiny local fixture, as in `tests/test_connectors.py`.
   `profile_source(open_connector(...))` should return the table, the columns and the row count.
9. **Check it is listed:** `python skills/bi-joe-data-profiler/scripts/run_bijoe.py connectors`.

### Option A: add it to this repo
1. Add `bijoe/connectors/<name>.py` and decorate the class with `@register`.
2. Import the module in `_ensure_loaded()` in `bijoe/connectors/__init__.py`.
3. Add tests in `tests/` that use a small local fixture. Don't depend on a live server
   in the default test run.
4. Add a row to the sources table in `README.md`.

### Option B: publish it as your own package
Declare an entry point, and BI Joe picks it up automatically:

```toml
# your package's pyproject.toml
[project.entry-points."bijoe.connectors"]
oracle = "bijoe_oracle:OracleConnector"
```

Run `bijoe connectors` to check that it is listed.

## Changing the output

The wiki layout, the metadata block and the JSON files are a public contract (see
[`output-format.md`](skills/bi-joe-data-profiler/references/output-format.md)). Agents
and tools depend on it. If you make a breaking change, bump `SCHEMA_VERSION` in
`bijoe/__init__.py` and describe the change in the PR.

## Changing the skill text

The skill's instructions in `SKILL.md` and `references/` shape how the model behaves.
When you change them, say in the PR what behaviour you saw before and what you expect
after. If you can, include a before/after description generated from a real dataset.
