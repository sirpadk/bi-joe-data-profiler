# How to read this wiki

[← Back to the overview](index.md)

This wiki is a profile of a dataset: a factual summary of what is in each table, written
so that people and AI agents can both use it.

## The pages

| Page | What it holds |
|---|---|
| Overview (`index.md`) | The dataset at a glance, every data story, and a diagram of how the tables connect |
| Data story (`data-stories/…`) | One table: what one row is, what it means, its columns, and anything to watch out for |
| [BEAM✲ annotations](beam-annotations.md) | What every short code like **[CV]** or **ND** means |

## Where descriptions come from

Every description says where it comes from:

| Source | Meaning |
|---|---|
| **system_metadata** | Taken word for word from the description stored in the source system. |
| **user_documentation** | Taken from documentation provided by the data owner. |
| **inferred** | Written by AI from the table's name, columns and values. Check it before you rely on it. |

When the evidence isn't enough, the wiki says **"More context needed."** rather than guessing.

## Measured and suggested

| Kind | Meaning |
|---|---|
| **Measured** | Comes straight from the data: counts, data types, uniqueness, links between tables. |
| **Suggested** | AI judgement based on the measured facts, always with a reason. Check it before you rely on it. |

## Sampled rows

A profile is always based on a **sample**. A file extract is normally a subset of a real
database, and very large tables are read only up to a set number of rows. "Sampled rows"
is the number of rows the profile is based on, not necessarily the size of the real table.

## For tools and AI agents

Every page ends with a **Metadata** section holding a `yaml` block. The measured facts
behind the wiki are in `_bijoe/profile.json`, and the written descriptions are in
`_bijoe/descriptions.json`.

<!-- bijoe: how-to-read v1. This file is copied as-is into every BI Joe wiki; edit it in skills/bi-joe-data-profiler/assets/. -->
