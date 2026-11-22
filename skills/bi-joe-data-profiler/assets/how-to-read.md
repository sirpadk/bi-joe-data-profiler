# How to Read This Wiki

[← Back to the Overview](index.md)

This wiki is a profile of a dataset: a factual summary of what is in each table, written
so that people and AI agents can both use it.

## The Pages

<table style="border-collapse:collapse;margin:8px 0;">
<tr><th align="left" style="text-align:left;padding:6px 16px 6px 0;border-bottom:2px solid rgba(128,128,128,.5);">Page</th><th align="left" style="text-align:left;padding:6px 0;border-bottom:2px solid rgba(128,128,128,.5);">What It Holds</th></tr>
<tr><td style="vertical-align:top;white-space:nowrap;font-weight:600;padding:6px 16px 6px 0;border-bottom:1px solid rgba(128,128,128,.4);">Overview (<code>index.md</code>)</td><td style="vertical-align:top;padding:6px 0;border-bottom:1px solid rgba(128,128,128,.4);">The dataset at a glance, every data story, and a diagram of how the tables connect</td></tr>
<tr><td style="vertical-align:top;white-space:nowrap;font-weight:600;padding:6px 16px 6px 0;border-bottom:1px solid rgba(128,128,128,.4);">Data Story (<code>data-stories/…</code>)</td><td style="vertical-align:top;padding:6px 0;border-bottom:1px solid rgba(128,128,128,.4);">One table: what the thing is, what one row is, its columns with statistics and sample data, how it connects to other tables, and anything to watch out for</td></tr>
<tr><td style="vertical-align:top;white-space:nowrap;font-weight:600;padding:6px 16px 6px 0;border-bottom:1px solid rgba(128,128,128,.4);"><a href="beam-annotations.md">BEAM✲ Annotations</a></td><td style="vertical-align:top;padding:6px 0;border-bottom:1px solid rgba(128,128,128,.4);">What every short code like <b>[CV]</b> or <b>ND</b> means</td></tr>
</table>

## Where Descriptions Come From

Every data story says where its description comes from:

<table style="border-collapse:collapse;margin:8px 0;">
<tr><th align="left" style="text-align:left;padding:6px 16px 6px 0;border-bottom:2px solid rgba(128,128,128,.5);">Source</th><th align="left" style="text-align:left;padding:6px 0;border-bottom:2px solid rgba(128,128,128,.5);">Meaning</th></tr>
<tr><td style="vertical-align:top;white-space:nowrap;font-weight:600;padding:6px 16px 6px 0;border-bottom:1px solid rgba(128,128,128,.4);">system_metadata</td><td style="vertical-align:top;padding:6px 0;border-bottom:1px solid rgba(128,128,128,.4);">Taken word for word from the description stored in the source system.</td></tr>
<tr><td style="vertical-align:top;white-space:nowrap;font-weight:600;padding:6px 16px 6px 0;border-bottom:1px solid rgba(128,128,128,.4);">user_documentation</td><td style="vertical-align:top;padding:6px 0;border-bottom:1px solid rgba(128,128,128,.4);">Taken from documentation provided by the data owner.</td></tr>
<tr><td style="vertical-align:top;white-space:nowrap;font-weight:600;padding:6px 16px 6px 0;border-bottom:1px solid rgba(128,128,128,.4);">inferred</td><td style="vertical-align:top;padding:6px 0;border-bottom:1px solid rgba(128,128,128,.4);">Written by AI from the table's name, columns and values. Check it before you rely on it.</td></tr>
</table>

When the evidence isn't enough, the wiki says **"More context needed."** rather than guessing.

## Measured and Suggested

<table style="border-collapse:collapse;margin:8px 0;">
<tr><th align="left" style="text-align:left;padding:6px 16px 6px 0;border-bottom:2px solid rgba(128,128,128,.5);">Kind</th><th align="left" style="text-align:left;padding:6px 0;border-bottom:2px solid rgba(128,128,128,.5);">Meaning</th></tr>
<tr><td style="vertical-align:top;white-space:nowrap;font-weight:600;padding:6px 16px 6px 0;border-bottom:1px solid rgba(128,128,128,.4);">Measured</td><td style="vertical-align:top;padding:6px 0;border-bottom:1px solid rgba(128,128,128,.4);">Comes straight from the data: counts, data types, uniqueness, links between tables.</td></tr>
<tr><td style="vertical-align:top;white-space:nowrap;font-weight:600;padding:6px 16px 6px 0;border-bottom:1px solid rgba(128,128,128,.4);">Suggested</td><td style="vertical-align:top;padding:6px 0;border-bottom:1px solid rgba(128,128,128,.4);">AI judgement based on the measured facts. Shown in <i>italics</i>. Check it before you rely on it.</td></tr>
</table>

## The Columns Table

Each real column is a column in the table. The rows describe it in three groups:

- **Data Profiling Results:** measured counts and extremes, such as missing values, unique values and the smallest and largest value.
- **Variation:** how the values differ: a typical value, a different one, a repeated one, how missing values show up, the range, and change over time (which a single snapshot of the data can't show).
- **Sample Data:** five random rows from the data.

The two label columns on the left stay in place when you scroll sideways.

## Sampled Rows

A profile is always based on a **sample**. A file extract is normally a subset of a real
database, and very large tables are read only up to a set number of rows. "Sampled Rows"
is the number of rows the profile is based on, not necessarily the size of the real table.

## For Tools and AI Agents

Every page ends with a **Metadata** section holding a `yaml` block. In a data story it
also holds the evidence behind the description, the reasons for the BEAM✲ suggestions and
the measured relationships. The measured facts behind the wiki are in `_bijoe/profile.json`,
and the written descriptions are in `_bijoe/descriptions.json`.

<!-- bijoe: how-to-read v2. This file is copied as-is into every BI Joe wiki; edit it in skills/bi-joe-data-profiler/assets/. -->
