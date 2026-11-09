# Output format (schema version 1)

This is the contract for the wiki. The engine produces it, and the manual method must
match it, so that people, tools and other AI agents can rely on the same structure.

```
<out>/
  index.md                    landing page
  data-stories/<slug>.md      one per table; slug = lowercase ASCII, non-alphanumerics → "-"
  beam-annotations.md         BEAM✲ reference page, copied unchanged from the skill's assets/
  how-to-read.md              reading guide, copied unchanged from the skill's assets/
  _bijoe/profile.json         facts, including measured relationships
  _bijoe/descriptions.json    descriptions + provenance
```

All links are relative. Story pages link back to `../index.md`, and the index links to
`data-stories/<slug>.md`.

Every BEAM✲ code is a link to its anchor on `beam-annotations.md`. Table codes use
`#t-<code>`, column codes `#c-<code>` and W-types `#w-<who|what|...>`, with the
special anchors `c-unavailable` (struck-through codes), `c-dim`, `c-uom`, `c-suspect`,
`c-important`, `t-source` and `c-source`. Brackets in link text are escaped:
`[\[CV\]](../beam-annotations.md#t-cv)`.

## Metadata block

Every page **ends** with a metadata section, so people see the content first and a
machine can still read the page without parsing the prose. The section is a horizontal
rule, the heading `## Metadata`, one italic line, and a fenced `yaml` block:

````markdown
---

## Metadata

_Machine-readable facts about this page, for tools and AI agents._

```yaml
bijoe: "data-story"
...
```
````

To read it, take the last ```` ```yaml ```` block under `## Metadata`. The fields are:

`index.md`
```yaml
bijoe: "data-profile-index"
schema_version: 1
dataset: "<name>"
source: "<source, never with secrets>"
source_type: "files" | "database"
connector: "<connector name>"
tables: <int>
sampled_rows: <int>
relationships: <int>
generated_at: "<ISO 8601 UTC>"
generator: "bi-joe-data-profiler <version>"
```

`data-stories/<slug>.md`
```yaml
bijoe: "data-story"
schema_version: 1
dataset: "<name>"
table: "<table name>"
grain: "One row per ..."
sampled_rows: <int>
columns: <int>
description_source: "system_metadata" | "user_documentation" | "inferred" | "pending"
confidence: "high" | "medium" | "low" | null
generated_at: "<ISO 8601 UTC>"
```

## Layout principles
- **Plan for 100 tables.** The landing page stays high-level. Per-table detail lives on the data stories.
- **Paired information is a two-column property table:** `| | |` / `|---|---|`, with the
  label in bold in the first column.

## Landing page sections (in order)
1. `# <dataset>: data profile`
2. `## At a glance`: a property table with About (the dataset summary), Source, Tables,
   Sampled rows, Profiled, Purpose, and How to read (links to `how-to-read.md` and `beam-annotations.md`)
3. `## Data stories`: an italic one-line explanation of what a data story is, then a table
   with columns Table (link), BEAM✲ (table codes), Grain, Description (the short
   `definition`), Sampled rows, Columns
4. `## Data model`: a table-level Mermaid `flowchart LR` drawn from the measured
   relationships, with plain lines (`---`), no cardinality and no column names
5. `## Metadata`: the metadata block

## Data story sections (in order)
1. Links back to the overview, the BEAM✲ page and `how-to-read.md`, then `# <table name>`
2. A property table: Grain, Definition, BEAM✲ (suggested table codes), Why [code],
   Source (the measured `{Source}`), Sampled rows, Columns, Description source, Confidence
3. `## Description`: the description, then a "Based on" list of evidence
4. `### Additional context (written by AI)`: only if `ai_notes` is set
5. `### Open questions for the data owner`: only if there are any
6. `## Columns`: a matrix, following the Modelstormer layout. **Every real column is a
   column**, its name in the header row, and the rows are:
   - **Data type**: the data type code and a plain word
   - **BEAM✲**: measured codes in plain text, AI-suggested codes in *italics*
   - **Example data**:
     - Typical: the most common value
     - Different: a rare value
     - Repeat: a repeated value ×count, or "no repeats"
     - Missing: how missing values show up (empty ×n, or placeholders such as N/A)
     - Range: min → max
     - Change: "—", since a single snapshot can't show change
   - **Data profiling results**: Sample Count, Missing, Unique Values, Min Value,
     Min Count, Max Value, Max Count, Min Length, Max Length (counts shown as "n (pct%)")

   This is followed by `### Why the suggestions` as a property table.
7. `## Sample rows`: 5 random rows from the profiled data (reservoir sampling with a fixed
   seed, so the same rows come back on every run). They're hidden, like the example
   data, when the profile is made with `--no-values`.
8. `## Relationships (measured)`: only if there are any
9. `## Metadata`: the metadata block (also has `grain`, `beam_table_codes` and `beam_source`)

## Static pages
`beam-annotations.md` and `how-to-read.md` are copied unchanged from the skill's
`assets/` folder into every wiki.

## descriptions.json

```json
{
  "dataset": {"summary": "", "source": "pending", "evidence": []},
  "tables": {
    "<table>": {
      "grain": "",
      "definition": "",
      "description": "",
      "source": "pending",
      "confidence": null,
      "evidence": [],
      "open_questions": [],
      "ai_notes": "",
      "beam": {
        "table": [],
        "table_why": "",
        "columns": {"<column>": {"codes": [], "why": ""}}
      }
    }
  }
}
```
