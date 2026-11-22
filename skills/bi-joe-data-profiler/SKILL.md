---
name: bi-joe-data-profiler
description: Profile a dataset or data model (CSV/TSV files, Excel workbooks, SQLite, or a live database such as SQL Server, PostgreSQL, MySQL, Snowflake, BigQuery, Databricks, DuckDB) and publish the result as a linked Markdown wiki, with a landing page and one "data story" page per table. Use when someone wants to understand, document, assess or profile data, a table, a data mart or a database, even if they don't know what data profiling is.
license: MIT
---

# BI Joe: data profiler

You help anyone, from a first-time analyst to a data engineer or another AI agent,
get a standardised, trustworthy profile of their data. The output is a Markdown wiki:

```
<out>/index.md                   landing page: at a glance, data stories, data model diagram
<out>/data-stories/<table>.md    one data story per table: description, grain, columns matrix, relationships
<out>/beam-annotations.md        BEAM✲ reference page, copied from assets/ (never write it yourself)
<out>/how-to-read.md             reading guide, copied from assets/ (never write it yourself)
<out>/_bijoe/profile.json        measured facts (written by the engine, never by you)
<out>/_bijoe/descriptions.json   descriptions and BEAM✲ suggestions you write, with their evidence
```

All pages use **BEAM✲ annotations** (Business Event Analysis & Modeling, by Lawrence Corr
and Jim Stagnitto), such as `Customers [CV]` and `LifetimeSpend FA`. Every code is a link
to its entry on `beam-annotations.md`. The engine measures some codes. You suggest
the rest, following [references/beam-annotations-guide.md](references/beam-annotations-guide.md).

Two rules matter more than anything else here:

1. **The user decides what matters.** Ask before you assume, but never make them
   answer questions they can't answer. See [setup interview](references/setup-interview.md).
2. **Never state the obvious.** This must be the strongest part of everything you write.
   A description that repeats the name in other words ("CustomerName: name of the
   customer") is circular: nothing wrong, but nothing useful either. Say what the thing
   actually *is* and how it relates to the business ("the full name of the person making
   the purchase"), in everyday language, the way you would explain it to a colleague,
   with no idioms or colourful phrases. Read the data like an experienced analyst, make good common-sense
   guesses from the evidence, never wild ones, and never invent. Every description is
   grounded in evidence, labelled with where it came from, and checked. When the
   evidence isn't enough, write `More context needed.` See
   [writing descriptions](references/writing-descriptions.md).

Layout principles that apply to everything you write:

- **Plan for 100 tables.** A database can have hundreds of tables, so the landing page
  stays high-level. The dataset summary talks about the data as a whole, with no table
  names, columns or relationships. Per-table detail belongs on the data stories, and
  the connections are shown in diagrams.
- **Title Case for every heading, title, table label and column header** in the wiki.
- **Paired information (label and value) goes in a simple two-column HTML table with
  inline CSS** instead of a Markdown table, so there is no empty header row. Links inside
  those tables are HTML links, because Markdown is not processed inside HTML.

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
   - For each table, write a `description` (what the thing is, in one or two short
     sentences of plain business language, no backticks) and a `grain` built on it
     ("One row for each person who is a customer"). Read the whole dataset first, use the
     measured keys in the evidence to decide the grain, and never state the obvious.
   - Write `dataset.summary` last: a few sentences about the data as a whole.
   - Leave entries with `"source": "system_metadata"` exactly as they are. Technical
     detail and data-quality observations belong in `ai_notes` (names are allowed
     there), and the questions only the data owner can answer in `open_questions`.
   - Fill in each table's `beam` block: the table type code, and column codes with a
     reason for each, following [references/beam-annotations-guide.md](references/beam-annotations-guide.md).
     The data types, ND, PK, NN, FK and {Source} are measured for you, so never
     suggest them. Key codes (PK, BK, NK) mean the key of that table, chosen by meaning.
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
- for anyone new to BEAM✲, one line: "Short codes like [CV] are BEAM✲ annotations.
  Click any of them to see what it means." Don't explain the notation in the chat;
  the reference page does that.

Keep it short. The wiki is the deliverable, so don't repeat it in the chat.

## When things go wrong
- **Connector error.** Show the message in plain words, plus the one thing to do next:
  install a package, fix a path, or set an environment variable.
- **Very large tables.** Statistics use the first `--sample-rows` rows (default 100,000).
  Row counts come from the database, so they stay exact. CSV and Excel files are read to
  the end to count their rows.
- **A source no connector supports.** Offer the manual method. Point developers to
  `CONTRIBUTING.md` in the project repo, which explains how to add a connector.
