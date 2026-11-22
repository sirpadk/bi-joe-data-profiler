# BI Joe: data profiler

An AI skill that turns any dataset or database into a clear, standardised profile: a **Markdown wiki**
with a landing page and one *data story* per table. No data-profiling experience is needed.

> **Status: alpha (0.1.0a1).** It works end to end on CSV, Excel, SQLite and SQL Server. The other
> databases are supported through the same connector but have not yet been tested against live servers.
> Expect rough edges and changes to the output format.

**In this guide:**
[What you get](#what-you-get) ·
[Sample reports](#sample-reports) ·
[What you need](#what-you-need) ·
[Install](#install) ·
[Get started](#get-started-in-five-minutes) ·
[How a session goes](#how-a-session-goes) ·
[Connect to your data](#connect-to-your-data) ·
[Read the result](#read-the-result) ·
[Privacy](#privacy) ·
[Commands and options](#commands-and-options) ·
[Add a connector](#add-a-connector) ·
[Troubleshooting](#troubleshooting)

---

## What you get

Point the skill at a CSV file, an Excel workbook, a SQLite file or a live database. An AI agent asks a
few short questions, runs the bundled engine, and writes a wiki that people and other AI agents can read:

```
bijoe-profile/
  index.md                 landing page: at a glance, a list of all tables, a diagram of how they connect
  data-stories/
    customers.md           one data story per table
    orders.md
  beam-annotations.md      reference page for the short codes used everywhere
  how-to-read.md           reading guide
  _bijoe/
    profile.json           measured facts
    descriptions.json      descriptions, with where each one came from
```

Each **data story** shows:

- A **description** and the **grain** (what one row is). If the database already stores a description,
  it is used **word for word**. If not, the AI writes one from evidence it can point to and says how
  sure it is.
- A **columns matrix**, one column per real column: data type, measured statistics (missing values,
  unique values, smallest and largest value and how often they occur), variation, a small **histogram**
  with its shape, outliers and gaps, and five random sample rows.
- **Relationships** to other tables, measured from the data and drawn as a diagram.
- **Open questions** for the data owner, for everything the data cannot answer.

Other things you get:

- **[BEAM✲](https://modelstorming.com) annotations** such as `Customers [CV]`, `UnitPrice NA` or
  `PreferredStoreID FK`. Plain codes are measured from the data. Codes in *italics* are suggested by the
  AI, with a reason. Hover over any code or measure for an explanation, or click it.
- **Personal data is masked** by the engine, so neither you nor the AI ever sees names, emails, phone
  numbers, national ID numbers and similar values.
- **Three colour themes**: light gray, light blue and dark.
- **A built-in checker** that flags descriptions that are invented, vague or only repeat the name.

**See real reports:** [Sample reports](#sample-reports).

## Sample reports

Three finished reports, made by the skill from the data in `sample/` and from a SQL Server sample database.

| Report | Built from | Tables | |
|---|---|---|---|
| **Shoe Company** | an Excel workbook, [`sample/shoe_company.xlsx`](sample/shoe_company.xlsx) | 4 | [Open online](https://sirpadk.github.io/bi-joe-data-profiler/viewer.html#examples/shoe_company/index.md) · [files on GitHub](examples/shoe_company/index.md) |
| **Danish Insurance Company** | 10 CSV files, [`sample/insurance_dk`](sample/insurance_dk) (dark theme) | 10 | [Open online](https://sirpadk.github.io/bi-joe-data-profiler/viewer.html#examples/insurance_dk/index.md) · [files on GitHub](examples/insurance_dk/index.md) |
| **AdventureWorks2025** | Microsoft's SQL Server sample database, written by a fresh agent from the skill alone | 71 | [Open online](https://sirpadk.github.io/bi-joe-data-profiler/viewer.html#examples/adventureworks2025/index.md) · [files on GitHub](examples/adventureworks2025/index.md) |

- **Open online** shows the report the way it is meant to look: colours, histograms, hover help and diagrams.
  It is a small viewer page (`viewer.html`) served by GitHub Pages. Start at the
  [sample reports page](https://sirpadk.github.io/bi-joe-data-profiler/).
- **Files on GitHub** is the same Markdown, browsed in the repository. GitHub draws the Mermaid diagrams but
  removes inline colours, so the tables appear without their theme. That is a GitHub limit, not a bug in the report.
- The data is made up, or Microsoft's public sample data. Personal data is masked by the engine, and the machine
  name in the connection was replaced with `localhost`.
- To see one locally: `python -m http.server` in the project folder, then open
  `http://localhost:8000/viewer.html#examples/shoe_company/index.md`.

## What you need

| You need | Why |
|---|---|
| **An AI assistant that can read files and run commands.** [Claude Code](https://claude.com/claude-code) or the Claude desktop app is the easiest. Other agents work too. | The AI does the reasoning: descriptions, grains and annotations. |
| **Python 3.9 or newer** (`python --version`) | The engine that measures the data. It uses only the standard library. |
| **Access to your data** | A file, or a database login. A read-only login is best. |

Optional packages, installed only when you need them (the AI asks first):

| For | Install |
|---|---|
| Excel files | `pip install openpyxl` |
| Any database | `pip install sqlalchemy`, plus the driver for your database (see [Connect to your data](#connect-to-your-data)) |

## Install

You install the skill by copying one folder, `skills/bi-joe-data-profiler`, to where your assistant looks
for skills. The folder is self-contained: it holds the instructions, the engine and everything the
agent needs.

**1. Download the project.**

```bash
git clone https://github.com/sirpadk/bi-joe-data-profiler
```

(Or use *Code → Download ZIP* on GitHub and unzip it.)

**2. Copy the skill into your assistant.**

*Claude Code, for all your projects:*

```powershell
# Windows (PowerShell), from inside the downloaded folder
New-Item -ItemType Directory -Force "$HOME\.claude\skills" | Out-Null
Copy-Item -Recurse -Force skills\bi-joe-data-profiler "$HOME\.claude\skills\"
```

```bash
# macOS or Linux, from inside the downloaded folder
mkdir -p ~/.claude/skills && cp -r skills/bi-joe-data-profiler ~/.claude/skills/
```

*Claude Code, for one project only:* copy the folder to `<your project>/.claude/skills/bi-joe-data-profiler`.

*Claude desktop app or claude.ai:* zip the `bi-joe-data-profiler` folder (the zip must contain that
folder with `SKILL.md` inside) and upload it under **Settings → Capabilities → Skills**. The menu
names can change, so look for the Skills section. The skill needs a Claude that can run code on your
machine (Claude Code, or the desktop app's code features) to reach local files and databases. The chat
on claude.ai usually cannot reach a database on your own network.

*Another AI agent (Codex, Cursor, Copilot, Gemini, a custom agent):* the skill is plain Markdown plus
a Python script. Copy the folder wherever your tool loads instructions from, or simply tell the agent
to read [`AGENTS.md`](AGENTS.md) in the project. If the agent cannot run code, the skill contains a
[manual method](skills/bi-joe-data-profiler/references/manual-profiling.md) that produces the same wiki.

**3. Check that it is there.** Start a new session and ask: *"Which skills do you have?"* The
**bi-joe-data-profiler** skill should be listed. If it is not, check that the folder is exactly
`.claude/skills/bi-joe-data-profiler/SKILL.md`, then start a new session.

**To update**, copy the folder again over the old one. **To remove**, delete the folder.

## Get started in five minutes

Try it on the sample insurance data that comes with the project (10 CSV files, nothing to install):

1. Open your assistant **inside the project folder** (or any folder: just give it the full path).
2. Say: **"Profile the data in `sample/insurance_dk` with the BI Joe skill."**
3. Answer the two or three questions it asks. Short answers are fine, and "no idea" is a good answer.
4. Wait while it measures the data and writes the descriptions. For 10 tables it takes a few minutes.
5. Open the link it gives you to `index.md`.

That is the whole workflow. For your own data, only step 2 changes.

**No AI at all?** You can run the engine yourself. It measures everything and builds the wiki; the
descriptions stay marked *pending* until someone writes them:

```bash
python skills/bi-joe-data-profiler/scripts/run_bijoe.py profile sample/insurance_dk --out my-first-profile
```

## How a session goes

You are in charge of what matters. The agent follows the skill's workflow:

1. **A short interview.** It asks what the profile is for, who will read it, and what matters most, in
   everyday words and adapted to how much you know. You can answer in one line or skip. If you tell it
   up front what you want, it asks nothing.
2. **It runs the engine.** The engine reads your data (read-only) and writes the measured facts.
3. **It writes the descriptions.** For each table: what it is, in plain language, and the grain. It
   uses the measured keys, relationships and distributions as evidence, labels each description with
   where it came from, and never invents. When the evidence is not enough it writes *More context needed.*
4. **It checks its own work.** The checker has to be clean before the wiki is built.
5. **It hands over** a link to the wiki, how many tables it profiled, how many descriptions came from
   the database itself, and the open questions to ask the data owner.

**What you do:** say what to profile, answer the questions, and give the agent what it asks for
(a file path, a server name, a login). **Never type a password into the chat.** Put it in an
environment variable and tell the agent the variable's name.

Tell the agent what you want to change at any time: *"use the dark theme"*, *"only the Sales and
Production tables"*, *"the data is sensitive"*, *"focus on customer data"*.

## Connect to your data

Tell the agent what you have. It follows [`references/connecting.md`](skills/bi-joe-data-profiler/references/connecting.md)
in the skill. This table shows what each source needs. The recipes below are the same ones the agent uses.

| Source | You give | Extra install | Tested |
|---|---|---|---|
| CSV or TSV file, or a folder of them | the path | none | yes |
| Excel (`.xlsx`) | the path | `pip install openpyxl` | yes |
| SQLite | the file path | none | yes |
| SQL Server, Azure SQL | server, database, login | `pip install sqlalchemy pyodbc` + ODBC driver | yes |
| PostgreSQL | host, database, login | `pip install sqlalchemy "psycopg[binary]"` | not yet |
| MySQL, MariaDB | host, database, login | `pip install sqlalchemy pymysql` | not yet |
| Snowflake | account, database, login | `pip install snowflake-sqlalchemy` | not yet |
| BigQuery | project, dataset | `pip install sqlalchemy-bigquery` | not yet |
| Databricks | host, HTTP path, token | `pip install databricks-sqlalchemy` | not yet |
| DuckDB | the file path | `pip install duckdb-engine` | not yet |
| Oracle and anything else SQLAlchemy supports | a SQLAlchemy URL | the database's driver | not yet |
| Something not listed | [export to CSV](#if-your-source-is-not-listed), or [add a connector](#add-a-connector) | | |

**Rules for every source:** BI Joe only **reads**. It profiles **tables only**: views, stored
procedures and functions are never read. Statistics use the first 100,000 rows of each table
(`--sample-rows` changes this) and row counts stay exact. Passwords go in environment variables.

In the commands below, `profile` is short for
`python skills/bi-joe-data-profiler/scripts/run_bijoe.py profile`.
If you installed the skill in `~/.claude/skills`, that script is in
`~/.claude/skills/bi-joe-data-profiler/scripts/`.

### CSV, Excel and SQLite

```bash
profile "C:\data\sales.csv" --out out           # one CSV file = one table
profile "C:\data\exports" --out out             # a folder: every CSV is a table
profile "C:\data\book.xlsx" --out out           # every sheet is a table (needs openpyxl)
profile "C:\data\shop.db" --out out             # SQLite
```

The CSV encoding and delimiter (comma, semicolon, tab or pipe) are detected. In Excel the first
non-empty row of a sheet is the header.

### SQL Server and Azure SQL

Needs `pip install sqlalchemy pyodbc` and a Microsoft ODBC driver
(*ODBC Driver 18 for SQL Server*, or 17). Check the drivers Python can see:

```bash
python skills/bi-joe-data-profiler/scripts/make_url.py drivers
```

The helper `make_url.py` builds the connection URL, including named instances and encoding.

```bash
# Windows login (no password needed)
python skills/bi-joe-data-profiler/scripts/make_url.py sqlserver --server "myhost\SQLEXPRESS" --database Sales --windows-auth

# SQL login: put the password in an environment variable first, then pass only its NAME
#   PowerShell:  $env:MSSQL_PWD = "..."          bash:  export MSSQL_PWD=...
python skills/bi-joe-data-profiler/scripts/make_url.py sqlserver --server myserver.database.windows.net --database Sales --user joe --password-env MSSQL_PWD
```

Use the URL it prints, in single quotes:

```bash
profile '<the printed URL>' --schema all --out out --name Sales
```

- `--schema all` reads every non-system schema, `--schema Sales,Production` only those. Without it, only
  the default schema (`dbo`) is read. Tables are then named `Schema.Table`.
- Descriptions stored in the database (the `MS_Description` property) are used word for word.
- For several databases, run once per database with a different `--out`.

### PostgreSQL

```bash
pip install sqlalchemy "psycopg[binary]"
export PGPASSWORD=...        # PowerShell: $env:PGPASSWORD = "..."
profile 'postgresql+psycopg://joe:${PGPASSWORD}@host:5432/mydb' --schema public --out out
```

`--schema all` reads every schema. `COMMENT ON` descriptions are used word for word.

### MySQL and MariaDB

```bash
pip install sqlalchemy pymysql
profile 'mysql+pymysql://joe:${MYSQL_PWD}@host:3306/mydb' --out out
```

### Snowflake

```bash
pip install snowflake-sqlalchemy
profile 'snowflake://joe:${SF_PWD}@myaccount/MYDB/PUBLIC?warehouse=MYWH&role=MYROLE' --out out
```

### Google BigQuery

Sign in first with `gcloud auth application-default login` (or set `GOOGLE_APPLICATION_CREDENTIALS`).

```bash
pip install sqlalchemy-bigquery
profile 'bigquery://my-project/my_dataset' --out out
```

### Databricks

```bash
pip install databricks-sqlalchemy
profile 'databricks://token:${DATABRICKS_TOKEN}@myhost.cloud.databricks.com?http_path=/sql/1.0/warehouses/abc123&catalog=main&schema=default' --out out
```

### DuckDB

```bash
pip install duckdb-engine
profile 'duckdb:///C:/data/analytics.duckdb' --out out
```

### Oracle and other databases

Any database with a SQLAlchemy driver works through the same connector. Install the driver, build the URL
the way the driver documents it, and pass it as the source, for example
`'oracle+oracledb://joe:${ORA_PWD}@host:1521/?service_name=ORCL'` after `pip install oracledb`.

### If your source is not listed

1. **Export to CSV.** Most tools can. Profile the folder of CSV files.
2. **Add a connector** (next section). It takes three small methods.
3. **No code at all:** the skill includes a
   [manual method](skills/bi-joe-data-profiler/references/manual-profiling.md).

Run `python skills/bi-joe-data-profiler/scripts/run_bijoe.py connectors` to see which sources work
on your machine right now, and which need a package.

## Read the result

Open `index.md` in the output folder.

- **GitHub** renders everything, including the diagrams.
- **VS Code:** use the Markdown preview. The diagrams need a Mermaid extension, such as
  *Markdown Preview Mermaid Support*.
- **Other viewers:** the pages use HTML tables with inline colours, and Mermaid for the diagrams. A viewer
  that does not draw Mermaid shows the diagram as text; everything else still works.

**Start with** the landing page ("At a Glance", the table list with the grain of each table, and the
diagram of how the tables connect). Then open the data stories of the tables you care about.
Hover over any BEAM✲ code or any row label (Min Count, Shape, Outliers...) for a plain explanation.
[`how-to-read.md`](skills/bi-joe-data-profiler/assets/how-to-read.md) in the wiki explains the page layout.

**Themes.** The wiki has one colour theme, chosen when it is built: `light-gray` (default),
`light-blue` or `dark`. Ask the agent, or run:

```bash
python skills/bi-joe-data-profiler/scripts/run_bijoe.py render out --theme dark
```

## Privacy

- The engine reads the raw values **in memory only**. Personal data (names, emails, phone numbers, addresses,
  national ID numbers such as CPR and SSN, birth dates, bank and card numbers, password hashes) is detected by
  column name (English and Danish) and by the shape of the values, and **masked before anything is
  written**. The AI never sees it, and it never reaches the wiki or the JSON files. Counts, gaps and lengths are
  still measured. Birth dates show only the years.
- A column the engine missed can be masked with `--mask Table.Column`. `check` scans the finished wiki and
  fails if it finds an email, a national ID number, an IBAN or a card number.
- `--no-values` records **no** example values at all, for data that is sensitive in other ways.
- Detection is a heuristic. Review the wiki before you share it.

## Commands and options

The engine is one script with five commands. The agent runs them for you.

| Command | What it does |
|---|---|
| `profile <source> --out <dir>` | measures the source and writes the wiki, with descriptions marked *pending* |
| `evidence <dir>` | prints the measured facts for writing descriptions (`--table <name>` for one table) |
| `check <dir>` | checks `descriptions.json` for invented, vague or obvious text, and scans for personal data |
| `render <dir>` | rebuilds the pages after the descriptions change (`--theme <name>` to switch the colours) |
| `connectors` | lists the available sources |

Options for `profile`:

| Option | Meaning |
|---|---|
| `--out <dir>` | where to write the wiki (default `bijoe-profile`) |
| `--name <text>` | the dataset name shown in the wiki |
| `--tables a,b,c` | only these tables |
| `--schema <s>` | for databases: one schema, a comma-separated list, or `all` |
| `--sample-rows <n>` | rows per table used for the statistics (default 100000) |
| `--no-values` | record no example values (sensitive data) |
| `--mask Table.Column,...` | also mask these columns as personal data |
| `--theme <name>` | `light-gray`, `light-blue` or `dark` |
| `--purpose`, `--audience`, `--focus` | your answers to the interview, in your own words |
| `--connector <name>` | force a connector instead of auto-detecting |

To get a `bijoe` command, install the project: `pip install -e ".[excel,sql]"`.

## Add a connector

A connector is a small plugin: three methods, usually under 100 lines. It only fetches data, so every
source gets exactly the same profile.

1. Copy [`docs/connector_template.py`](docs/connector_template.py) and fill in the TODOs:
   `list_tables()`, `describe_table(name)` and `iter_rows(name, limit)`.
2. Either add it to this repo, or publish it as your own package with an entry point that BI Joe picks up
   automatically:

   ```toml
   [project.entry-points."bijoe.connectors"]
   oracle = "bijoe_oracle:OracleConnector"
   ```

3. Run `python skills/bi-joe-data-profiler/scripts/run_bijoe.py connectors` to check that it is listed.

[CONTRIBUTING.md](CONTRIBUTING.md) has the rules (read-only, pass through the source's own descriptions,
no secrets in the displayed source) and a step-by-step walk-through.

## Troubleshooting

| What you see | What to do |
|---|---|
| `python` is not found | Install Python 3.9 or newer, and tick "Add Python to PATH". On macOS and Linux try `python3`. |
| `needs: openpyxl` or `needs: sqlalchemy` | Run the `pip install` shown for your source in [Connect to your data](#connect-to-your-data). |
| SQL Server: *driver not found* or *Data source name not found* | Install *ODBC Driver 18 for SQL Server* from Microsoft. Check with `make_url.py drivers`. |
| SQL Server: *certificate verify failed* | Build the URL with `make_url.py`: it trusts the server certificate by default. |
| SQL Server: *login failed* | The login needs to read the database (`db_datareader` is enough). With a Windows login, run the tool as that user. |
| SQL Server: cannot reach the server | Firewall, VPN or a wrong instance name. For a named instance the SQL Server Browser service must run, or use `--server "host,1433"`. |
| SQL Server: only a few tables are found | The tables are in other schemas. Add `--schema all`. |
| *The environment variable X is not set* | Set the variable in the same terminal the agent runs in, then run again. |
| The database is empty | BI Joe profiles tables only. Views, stored procedures and functions are never read. |
| Profiling is slow on a big database | Use `--tables` for the ones you need, or lower `--sample-rows`. |
| Diagrams show as text | Your viewer does not draw Mermaid. Use GitHub, or add a Mermaid extension to VS Code. |
| The agent invents details | Run `check` and fix the warnings. Descriptions are labelled with their source and confidence. |

If something fails, show the agent the exact error. The skill tells it to explain in plain words and give
you the one thing to do next.

## Project layout

```
skills/bi-joe-data-profiler/   the skill: SKILL.md, references/, assets/, scripts/ (the engine)
AGENTS.md                      instructions for other AI agents
docs/connector_template.py     starting point for a new connector
examples/                      three finished reports (shoe company, insurance, AdventureWorks)
viewer.html, index.html        the online viewer for the sample reports (GitHub Pages)
sample/                        test data: shoe company (Excel), Danish insurance company (CSV)
tests/                         the test suite
```

To work on the code: `python -m venv .venv`, then `.venv/Scripts/pip install -e .[dev,excel,sql]` and `pytest`.
See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT
