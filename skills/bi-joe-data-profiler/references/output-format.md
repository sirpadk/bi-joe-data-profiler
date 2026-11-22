# Output format (schema version 2)

This is the contract for the wiki. The engine produces it, and the manual method must
match it, so that people, tools and other AI agents can rely on the same structure.

```
<out>/
  index.md                    landing page
  data-stories/<slug>.md      one per table; slug = lowercase ASCII, non-alphanumerics → "-"
  beam-annotations.md         BEAM✲ reference page, copied unchanged from the skill's assets/
  how-to-read.md              reading guide, copied unchanged from the skill's assets/
  _bijoe/profile.json         facts, including measured relationships and keys (a "keys" block per table)
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
schema_version: 2
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
schema_version: 2
dataset: "<name>"
table: "<table name>"
grain: "One row per ..."
sampled_rows: <int>
columns: <int>
description_source: "system_metadata" | "user_documentation" | "inferred" | "pending"
confidence: "high" | "medium" | "low" | null
generated_at: "<ISO 8601 UTC>"
```

## Layout Principles
- **Plan for 100 tables.** The landing page stays high-level. Per-table detail lives on the data stories.
- **Title Case** for every heading, title, table label and column header. Names that come from
  the data (table names, column names, BEAM✲ codes) are never changed. The dataset name the user gave is shown in Title Case in page titles and links, and stays as given in the metadata.
- **Paired information is a simple two-column HTML table with inline CSS**, one row per
  property, label in the first cell (`<th scope="row">`) and value in the second. There is no
  header row, so there is no empty row. Markdown is not processed inside HTML, so the links
  and bold text in those cells are HTML (`<a href>`, `<b>`, `<i>`, `<code>`).
- Inline CSS is stripped by some viewers (GitHub). The tables still show there, only unstyled.

## Landing Page Sections (in Order)
1. `# <Dataset>: Data Profile`
2. `## At a Glance`: a property table with About (the dataset summary), Source, Tables,
   Sampled Rows, Profiled, Purpose, and How to Read (links to `how-to-read.md` and `beam-annotations.md`)
3. `## Data Stories`: an italic one-line explanation of what a data story is, then a Markdown table
   with columns Table (link), BEAM✲ (table codes), Grain, Description (the same description as
   the data story), Sampled Rows, Columns
4. `## Data Model`: a table-level Mermaid `flowchart LR` drawn from the measured
   relationships, with plain lines (`---`), no cardinality and no column names
5. `## Metadata`: the metadata block

## Data Story Sections (in Order)
1. Links back to the overview, the BEAM✲ page and `how-to-read.md`, then `# <table name>`
2. A property table: **Description** (first), Grain, BEAM✲ (suggested table codes), Why [code],
   Source (the measured `{Source}`), Sampled Rows, Columns, Description Source, Confidence.
   There is no separate Definition and no "Based on" list.
3. `## Columns`: an HTML matrix following the Modelstormer layout. **Every real column is a
   column.** The two label columns on the left stay frozen on sideways scroll and never wrap.
   The group names are rotated and span their rows. In order:
   - **Column Name** (header row), then **Data Type** (code and plain word) and **BEAM✲**
     (measured codes in plain text, AI-suggested codes in *italics*), each with its label
     across both left columns
   - **Data Profiling Results**: Sample Count, Missing, Unique Values, Min Value, Min Count,
     Max Value, Max Count, Min Length, Max Length (counts shown as "n (pct%)")
   - **Variation**: Typical (the most common value), Different (a rare value), Repeat (a
     repeated value ×count, or "no repeats"), Missing (empty ×n, or placeholders such as
     N/A), Range (min → max), Change ("—", since a single snapshot can't show change)
   - **Sample Data**: 5 random rows from the profiled data (reservoir sampling with a fixed
     seed, so the same rows come back on every run), the second label column left blank.
     The Variation values and the Sample Data are hidden when the profile is made with
     `--no-values`.
4. `## Relationships (Measured)`: `N/A` when the table has no measured relationships.
   Otherwise a Mermaid `flowchart LR`: the current table is a box listing its column names,
   left aligned (`<div style='text-align:left'>` in the label), joined by plain lines to plain
   boxes (name only) for each table it is linked to. Above 20 columns the box lists
   the relationship columns and the table's key columns (PK, BK, NK) first, fills the remaining
   places up to 20 with the earliest other columns, shows them in table order and puts a
   `...` line wherever columns were skipped. If the priority columns alone exceed 20, all of
   them are shown.
5. `## Additional Context (Written by AI)`: only if `ai_notes` is set
6. `## Open Questions for the Data Owner`: only if there are any
7. `## Metadata`: the metadata block. For a data story it holds `grain`, `beam_table_codes`,
   `beam_source`, `beam_reasons` (why each BEAM✲ suggestion was made), `evidence` (the facts
   behind the description) and `relationships` (with the measured coverage).

## Static pages
`beam-annotations.md` and `how-to-read.md` are copied unchanged from the skill's
`assets/` folder into every wiki.

## descriptions.json

```json
{
  "dataset": {"summary": "", "source": "pending", "evidence": []},
  "tables": {
    "<table>": {
      "description": "",
      "grain": "",
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

## Theme

`profile.json` has `settings.theme` (`light-gray`, `light-blue` or `dark`). Every HTML table is
written with that theme's colours inline (see `scripts/bijoe/themes.py`), because GitHub strips
style blocks. Change it with `render --theme <name>`. A wiki has one theme at a time. The theme
affects colours only, never the content or the layout.

## Personal Data

The engine detects personal data by column name (English and Danish) and by the shape of the
values, and masks it before anything is written. For a masked column, `profile.json` has a
`pii` object (`class` and `reason`), no `top_values`, `rare_value`, `min`/`max`/`mean` or
`min_value`/`max_value` (birth dates keep the years only), and `sample_rows` hold `••••`. Counts,
missing values, distinct counts and lengths are kept. `settings.mask` records columns masked with
`--mask Table.Column`. `bijoe check` scans every page and JSON file for emails, national ID numbers,
IBANs and card numbers, and reports an error if it finds one.

## Distributions

Each column in `profile.json` may have a `distribution` object. `kind` is `numeric` (round-edged bins),
`discrete` (one bar per value), `time` (bins by day, month, quarter, year or decade, with `unit`),
`categories` (most frequent values, small groups folded into "Other") or `none` (personal data:
only `top_share_pct`, never a value). It has `bins` (`label`, `from`, `to`, `count`, `pct`, and the
flags `gap`, `outlier` or `other_group`), `shape`, `skewness`, `median`, `q1`, `q3`, `iqr`,
`outliers` (`below`, `above` and the Tukey fences), `gap_runs`, `gap_bins`, `top_share_pct` and
`sampled`. Unique keys, identifiers, free text and columns with no spread have no distribution.
The columns matrix draws it in the Distribution group: Histogram, Shape, Median, Spread,
Outliers and Gaps.
