# Output format (schema version 1)

This is the contract for the wiki. The engine produces it, and the manual method must
match it, so that people, tools and other AI agents can rely on the same structure.

```
<out>/
  index.md                    landing page
  data-stories/<slug>.md      one per table; slug = lowercase ASCII, non-alphanumerics → "-"
  beam-annotations.md         BEAM✲ reference page, copied unchanged from the skill's assets/
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
total_rows: <int>
generated_at: "<ISO 8601 UTC>"
generator: "bi-joe-data-profiler <version>"
```

`data-stories/<slug>.md`
```yaml
bijoe: "data-story"
schema_version: 1
dataset: "<name>"
table: "<table name>"
rows: <int>
columns: <int>
description_source: "system_metadata" | "user_documentation" | "inferred" | "pending"
confidence: "high" | "medium" | "low" | null
generated_at: "<ISO 8601 UTC>"
```

## Landing page sections (in order)
1. `# <dataset>: data profile`, followed by the dataset summary
2. `## At a glance`: source, number of tables, total rows, profiling time, purpose, sampling note
3. `## Data stories`: a table with columns Table (link), BEAM✲ (table codes), Rows,
   Columns, and the first sentence of the Description
4. `## How the tables connect (measured)`: only if relationships were found
5. `## How to read this wiki`: what each source label means, plus a link to the BEAM✲ page
6. `## Metadata`: the metadata block

## Data story sections (in order)
1. Back link and BEAM✲ page link, then `# <table name>`
2. `**BEAM✲:**` line: the suggested table codes and the measured `{Source}`
3. `## Description`, followed by:
   - the description itself
   - a "Where this comes from" provenance quote, with the confidence and a "Based on"
     list of evidence, and "Why [code]" for the table codes
4. `### Additional context (written by AI)`: only if `ai_notes` is set
5. `### Open questions for the data owner`: only if there are any
6. `## Columns`: Column, Type (data type code + plain word), Measured codes, Suggested
   codes, Missing, Distinct, Examples (only if values are allowed), followed by
   "Why the suggestions"
7. `## Relationships (measured)`: only if there are any
8. `## Metadata`: the metadata block (also has `beam_table_codes` and `beam_source`)

## descriptions.json

```json
{
  "dataset": {"summary": "", "source": "pending", "evidence": []},
  "tables": {
    "<table>": {
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
