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
