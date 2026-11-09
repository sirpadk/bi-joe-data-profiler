# Output format (schema version 1)

This is the contract for the wiki. The engine produces it, and the manual method must
match it, so that people, tools and other AI agents can rely on the same structure.

```
<out>/
  index.md                    landing page
  data-stories/<slug>.md      one per table; slug = lowercase ASCII, non-alphanumerics → "-"
  _bijoe/profile.json         facts
  _bijoe/descriptions.json    descriptions + provenance
```

All links are relative. Story pages link back to `../index.md`, and the index links to
`data-stories/<slug>.md`.

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
3. `## Data stories`: a table with columns Table (link), Rows, Columns, and the first
   sentence of the Description
4. `## How to read the descriptions`: what each source label means
5. `## Metadata`: the metadata block

## Data story sections (in order)
1. Back link, then `# <table name>`
2. `## Description`, followed by:
   - the description itself
   - a "Where this comes from" provenance quote, with the confidence and a "Based on"
     list of evidence
3. `### Additional context (written by AI)`: only if `ai_notes` is set
4. `### Open questions for the data owner`: only if there are any
5. `## Metadata`: the metadata block

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
      "ai_notes": ""
    }
  }
}
```
