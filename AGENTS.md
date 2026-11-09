# Instructions for AI agents

This file covers two cases: an AI agent (Codex, Cursor, Copilot, Gemini, a custom agent
and so on) asked to **profile data with BI Joe**, and an agent working on **this
repository's code**.

## Profiling data

The full instructions are in [`skills/bi-joe-data-profiler/SKILL.md`](skills/bi-joe-data-profiler/SKILL.md).
Ignore its YAML header, then follow the workflow and the guides it links to:

1. [Setup interview](skills/bi-joe-data-profiler/references/setup-interview.md): find out
   what matters to the user, at their level. Ask nothing if you were called with a clear brief.
2. Run the engine: `python skills/bi-joe-data-profiler/scripts/run_bijoe.py profile <source> --out <dir>`
3. [Write the descriptions](skills/bi-joe-data-profiler/references/writing-descriptions.md):
   grounded in evidence, labelled with their source, nothing invented. Add
   [BEAM✲ annotations](skills/bi-joe-data-profiler/references/beam-annotations-guide.md)
   with a reason for each one.
4. Run `check`, then `render`, then hand over the link to `<dir>/index.md`.

If you can't run Python, use the [manual method](skills/bi-joe-data-profiler/references/manual-profiling.md).

## Working on this repo
- The engine is in `skills/bi-joe-data-profiler/scripts/bijoe/`. Its core uses the
  standard library only. Optional dependencies are imported inside the connector that
  needs them.
- To set up and run the tests:
  `python -m venv .venv && .venv/Scripts/pip install -e .[dev,excel,sql]`, then
  `pytest`.
- To add a data source, read [CONTRIBUTING.md](CONTRIBUTING.md).
- Treat the wiki layout and the JSON files as a public contract
  ([output-format.md](skills/bi-joe-data-profiler/references/output-format.md)). If you
  make a breaking change, bump `SCHEMA_VERSION`.
