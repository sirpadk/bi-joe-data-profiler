# Profiling without the engine

Use this when Python is not available or you can't run code. The goal is the **same wiki
layout and the same honesty rules**, with the limitation stated openly.

## What to do

1. **Read the structure.** For each table, get the column names. Use the CSV header, the
   first row of the sheet, `CREATE TABLE` statements, or a schema export.
   - If you only have a schema (DDL, a column list, a diagram) and no data, you can still
     write data stories. Base them on names, types, keys, constraints and comments, and
     say "based on structure only, no data seen".
2. **Look at the data you can see.** For each table:
   - Count the rows if you can. If you can't, say "unknown".
   - Note the type each column looks like.
   - Note obvious gaps (empty cells), example values, and the first and last dates.
   - Read at most a few hundred rows per table, and say how many you read.
3. **Write the files** described in [output-format.md](output-format.md):
   - `_bijoe/descriptions.json` uses the same format and the same rules as in
     [writing-descriptions.md](writing-descriptions.md).
   - `_bijoe/profile.json` must hold only what you actually observed. Add
     `"profiled_by": "manual"`, and add `"approximate": true` to every number you didn't
     count exactly.
   - Copy `assets/beam-annotations.md` and `assets/how-to-read.md` from the skill folder into the wiki folder, unchanged.
   - Then write `index.md` and `data-stories/<slug>.md` by hand, following the layout in
     [output-format.md](output-format.md): Title Case headings, paired information in simple
     two-column HTML tables with inline CSS (links inside them written as HTML), the columns
     matrix as an HTML table, and Mermaid diagrams for the relationships. Link every BEAM✲
     code to its anchor, e.g. `[\[CV\]](../beam-annotations.md#t-cv)` in Markdown or
     `<a href="../beam-annotations.md#t-cv">[CV]</a>` in HTML. Without the engine, data types
     and `ND` are only as good as the rows you read, so say the column matrix is *approximate*.
4. **Be honest about the method.** On the landing page, add a row to the "At a Glance"
   table: Method, "Manual review of N rows per table by AI; figures are approximate".
   Use `confidence: low` or `medium` unless the evidence is unambiguous.

## Never
- Never make up statistics to fill a template field. Leave the field out.
- Never present a sample as the whole table.

## Keys (Do This by Hand Too)

For each table, check which column, or which small combination of columns, is unique across
all rows (count distinct values against the row count). Also check how identifier-like
columns in the same table map onto each other (for example a customer number and a tax
number): one value should map to one value if they name the same thing. Use the result to
decide the grain, and say it is approximate if you only looked at part of the data.
