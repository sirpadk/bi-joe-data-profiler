# Setup interview

The aim is to learn what *this* person needs, so the profile covers what matters to them
and nothing else. You also need them to feel capable, not tested. A good interview takes
under two minutes and often needs only one or two questions.

## Principles

1. **Detect first, ask second.** Never ask for something you can see for yourself: the
   file type, the sheet names, which tables exist, whether a path exists. Look first,
   then confirm in one line ("I can see 3 CSV files: customers, orders, products").
2. **Ask at most two or three questions at a time.** Use plain words. Put the default in
   brackets so "ok" is always a valid answer.
3. **Always offer a way out.** End the first round with something like: *"Not sure?
   Just say 'use the defaults' and I'll make sensible choices you can change later."*
4. **Explain any term in the same breath.** For example: "profile (a factual summary of
   what's in each table)", or "sample (the first 100,000 rows, used to keep it fast)".
   Never say "cardinality", "grain" or "referential integrity" to someone who hasn't
   used those words first.
5. **Mirror their level.** Read how they write:
   - **Newcomer** ("I got this Excel file and need to understand it"): reassure them,
     use no jargon, ask about their goal, and choose the rest yourself.
   - **Analyst** ("assess the sales mart before I build a dashboard"): ask about scope
     and purpose, and mention the options in brief.
   - **Engineer** ("profile the staging schema, skip the audit tables, no PII values"):
     confirm the settings in one line and get going. Don't over-ask.
   - **Another AI agent / automated call** (a clear brief, or nobody answering): ask
     nothing. Use the brief plus the defaults, and list the assumptions you made in your
     hand-over.
6. **Their words, not your categories.** Record their answers as they said them, using
   `--purpose`, `--audience` and `--focus`. The answers shape how you write the
   descriptions.
7. **Never ask for secrets in the chat.** For databases, see "Credentials" in SKILL.md.

## What to find out

Ask only what you can't detect, and stop as soon as you know enough.

| # | Topic | Ask when | Plain-language question | Default | Goes to |
|---|---|---|---|---|---|
| 1 | Source | Not given, or ambiguous | "Where's the data? A file, a folder of files, or a database you can connect to?" | none (required) | `<source>` |
| 2 | Purpose | Almost always (one line) | "What do you want to use this data for? It helps me point out what matters." | "general understanding" | `--purpose` |
| 3 | Scope | More than ~10 tables, or they mention a subset | "Should I look at all N tables, or only some?" | all | `--tables` |
| 4 | Sensitivity | The data may contain people, money or health data | "Is there personal or confidential data in here? If so, I won't copy any example values into the report." | include values unless the user hints at sensitivity | `--no-values` |
| 5 | Audience | They mention others will read it | "Who else will read this?" | the user | `--audience` |
| 6 | Focus | Analyst or engineer, or they mention a concern | "Anything you're especially worried about or curious about?" | none | `--focus` |
| 7 | Existing docs | Always offer, never insist | "Do you have any documentation or a data dictionary? If so, I'll use it instead of guessing." | none | `user_documentation` descriptions |
| 8 | Output folder | Rarely; only if it matters to them | "Where should I save the wiki?" | `./bijoe-profile/<dataset>` | `--out` |

Topics 1 and 2 cover most conversations. Bring in the others only when the situation calls
for them.

## Example openings

**Newcomer**
> Happy to help. I'll go through the file and write up what's in each table, in plain
> language. Two quick things first:
> 1. What do you want to use this data for? (A rough idea is fine.)
> 2. Does it contain personal details like names or emails? If so, I won't copy any
>    examples into the report.
>
> Or just say "go" and I'll use sensible defaults.

**Engineer**
> I'll profile all 14 tables in `staging` (first 100k rows each, exact row counts), and
> include example values. Shall I skip the `audit_*` tables or keep the values out?
> Otherwise I'll start.

## After the interview
Repeat the plan back in one sentence, then run the profiler. If something they said changes
later ("oh, only the sales tables"), re-run `profile` with new settings. Descriptions that
are already written are kept.
