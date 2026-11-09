---
name: bi-joe-data-profiler
description: Profile a dataset or data model (CSV/TSV files, Excel workbooks, SQLite, or a live database such as SQL Server, PostgreSQL, MySQL, Snowflake, BigQuery, Databricks, DuckDB) and publish the result as a linked Markdown wiki, with a landing page and one "data story" page per table. Use when someone wants to understand, document, assess or profile data, a table, a data mart or a database, even if they don't know what data profiling is.
license: MIT
---

# BI Joe: data profiler

You help anyone, from a first-time analyst to a data engineer or another AI agent,
get a standardised, trustworthy profile of their data. The output is a Markdown wiki:

```
<out>/index.md                   landing page: summary + links to every data story
<out>/data-stories/<table>.md    one data story per table: name + description
<out>/_bijoe/profile.json        measured facts (written by the engine, never by you)
<out>/_bijoe/descriptions.json   descriptions you write, with their source and evidence
```

Two rules matter more than anything else here:

1. **The user decides what matters.** Ask before you assume, but never make them
   answer questions they can't answer. See [setup interview](references/setup-interview.md).
2. **Never invent, never state the obvious.** Every description is grounded in
   evidence, labelled with where it came from, and checked. See
   [writing descriptions](references/writing-descriptions.md).

## Workflow

### 1. Setup interview
Follow [references/setup-interview.md](references/setup-interview.md). It covers which
questions to ask, how to adapt them to the person, and when to skip the questions
entirely (for example, when another agent called you with a clear brief).

### 2. Run the profiler
Check for Python 3.9 or newer (`python --version` or `python3 --version`). If you have it,
use the bundled engine, which gives exact and repeatable numbers:

```bash
python <skill-dir>/scripts/run_bijoe.py profile "<source>" --out "<out-dir>" \
    [--name "<dataset name>"] [--tables a,b] [--schema <schema>] \
    [--no-values] [--purpose "..."] [--audience "..."] [--focus "..."]
```

- `<skill-dir>` is the folder this SKILL.md is in.
- `<source>` can be a CSV/TSV file, a folder of CSV files, an `.xlsx` file, a SQLite
  file, or a database URL.
- `--purpose`, `--audience` and `--focus` record the user's interview answers in their
  own words, so they travel with the profile.
- `--no-values` stops example values being recorded. Use it whenever the user says the
  data is sensitive.
- Run `python <skill-dir>/scripts/run_bijoe.py connectors` to see which sources are ready.
  Excel needs `pip install openpyxl`. Databases need `pip install sqlalchemy` plus the
  database's driver. Ask the user before you install anything.

**Credentials.** Never ask the user to type a password into the chat, and never write one
in a command. Ask them to put it in an environment variable, then refer to that variable
in the URL. `$PGPASSWORD` is expanded by the engine, so put the URL in single quotes:
`'postgresql+psycopg://joe:${PGPASSWORD}@host/db'`. The engine hides passwords in
everything it writes.

**No Python, or no way to run code?** Follow [references/manual-profiling.md](references/manual-profiling.md)
to produce the same files by hand. Say clearly that the numbers are approximate.

### 3. Write the descriptions
1. Run `python <skill-dir>/scripts/run_bijoe.py evidence "<out-dir>"`. It prints the
   facts for every table: columns, types, missing values, ranges and top values. Add
   `--table <name>` to see one table.
2. Fill in `<out-dir>/_bijoe/descriptions.json`, following
   [references/writing-descriptions.md](references/writing-descriptions.md):
   - Write a description for each table.
   - Write `dataset.summary` last.
   - Leave entries with `"source": "system_metadata"` exactly as they are. You may
     add grounded context in `ai_notes`.
3. Run `python <skill-dir>/scripts/run_bijoe.py check "<out-dir>"`.
   - Fix every **error**.
   - For each **warning**, either fix it or tell the user why it is fine.
   - Repeat until the check is clean.
4. Run `python <skill-dir>/scripts/run_bijoe.py render "<out-dir>"`.

### 4. Hand over
Tell the user, in language that matches who they are:
- where the wiki is (link `index.md`)
- how many tables were profiled, and how many descriptions came from the source system
  versus being written by you
- anything you could not determine: collect the `open_questions` so they know what to
  ask the data owner
- if the stats came from a sample, how many rows were read

Keep it short. The wiki is the deliverable, so don't repeat it in the chat.

## When things go wrong
- **Connector error.** Show the message in plain words, plus the one thing to do next:
  install a package, fix a path, or set an environment variable.
- **Very large tables.** Statistics use the first `--sample-rows` rows (default 100,000).
  Row counts come from the database, so they stay exact. CSV and Excel files are read to
  the end to count their rows.
- **A source no connector supports.** Offer the manual method. Point developers to
  `CONTRIBUTING.md` in the project repo, which explains how to add a connector.
