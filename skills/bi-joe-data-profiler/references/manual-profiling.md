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
   - Copy `assets/beam-annotations.md` from the skill folder into the wiki folder, unchanged.
   - Then write `index.md` and `data-stories/<slug>.md` by hand, following the templates.
     Link every BEAM✲ code to its anchor, e.g. `[\[CV\]](../beam-annotations.md#t-cv)` or
     `[FA](../beam-annotations.md#c-fa)`. Without the engine, data types and `ND` are only as
     good as the rows you read, so mark the column table *approximate*.
4. **Be honest about the method.** On the landing page, add a row to "At a glance":
   `| Method | Manual review of N rows per table by AI; figures are approximate |`.
   Use `confidence: low` or `medium` unless the evidence is unambiguous.

## Never
- Never make up statistics to fill a template field. Leave the field out.
- Never present a sample as the whole table.
