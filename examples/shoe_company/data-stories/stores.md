[← Shoe company overview](../index.md) · [BEAM✲ annotations](../beam-annotations.md) · [How to read this wiki](../how-to-read.md)

# Stores

| | |
|---|---|
| **Grain** | One row per store |
| **Definition** | A store is a physical StepUp shop (an outlet, flagship, kiosk or standard store), identified by `StoreID`. |
| **BEAM✲** | [\[CV\]](../beam-annotations.md#t-cv) _(suggested by AI)_ |
| **Why [\[CV\]](../beam-annotations.md#t-cv)** | One row per `StoreID` (unique in all 15 rows), with descriptive attributes and no validity dates or version columns. |
| **Source** | [{shoe_company.xlsx: Stores}](../beam-annotations.md#t-source) _(measured)_ |
| **Sampled rows** | 15 |
| **Columns** | 12 |
| **Description source** | Written by AI from the data. Check before relying on it. |
| **Confidence** | high |

## Description

One row per store, identified by `StoreID`, with location, manager, size and `StoreType` (`Outlet`, `Flagship`, `Kiosk` or `Standard`). Stores opened between 2010-10-14 and 2024-02-28, in 9 cities across 8 states, and every store is the preferred store of at least one customer. Two different stores share the name `StepUp Northpoint Houston` (an outlet and a standard store at different addresses), so label stores by `StoreID`, or by name plus address.

**Based on:**

- `StoreID` unique and never missing across 15 rows
- `OpenDate` min 2010-10-14, max 2024-02-28
- `City` 9 distinct, `State` 8 distinct
- `StoreType` values: `Outlet` (6), `Flagship` (4), `Kiosk` (3), `Standard` (2)
- `StoreName` 14 distinct in 15 rows; S007 and S008 share a name (checked separately)
- All 15 `StoreID` values appear in `Customers.PreferredStoreID` (measured relationship)
- Every store has an address, `SquareFeet` and `Employees`, so it is a physical location

### Open questions for the data owner

- Is the shared `StoreName` `StepUp Northpoint Houston` intentional (two stores in one mall) or a data entry error?

## Columns

| | **StoreID** | **StoreName** | **Address** | **City** | **State** | **ZipCode** | **Phone** | **Manager** | **OpenDate** | **StoreType** | **SquareFeet** | **Employees** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Data type** | [C4](../beam-annotations.md#c-c) text | [C26](../beam-annotations.md#c-c) text | [C12](../beam-annotations.md#c-c) text | [C8](../beam-annotations.md#c-c) text | [C2](../beam-annotations.md#c-c) text | [I](../beam-annotations.md#c-i) whole number | [C14](../beam-annotations.md#c-c) text | [C17](../beam-annotations.md#c-c) text | [D](../beam-annotations.md#c-d) date | [C8](../beam-annotations.md#c-c) text | [I](../beam-annotations.md#c-i) whole number | [I](../beam-annotations.md#c-i) whole number |
| **BEAM✲** | [ND](../beam-annotations.md#c-nd) *[BK](../beam-annotations.md#c-bk)* *[MD](../beam-annotations.md#c-md)* | *[?](../beam-annotations.md#c-suspect)* | [ND](../beam-annotations.md#c-nd) |  |  | [ND](../beam-annotations.md#c-nd) | [ND](../beam-annotations.md#c-nd) | [ND](../beam-annotations.md#c-nd) | *[FV](../beam-annotations.md#c-fv)* | *[!](../beam-annotations.md#c-important)* | [ND](../beam-annotations.md#c-nd) *[\[sq ft\]](../beam-annotations.md#c-uom)* |  |
| **Example data** |  |  |  |  |  |  |  |  |  |  |  |  |
| Typical | S001 | StepUp Northpoint Houston | 35 Cedar Ln | Houston | TX | 42098 | (555) 328-3286 | Ava Brown | 2010-10-14 | Outlet | 1044 | 15 |
| Different | S002 | StepUp Airport Houston | 133 Pine St | Atlanta | CO | 10425 | (555) 165-6539 | Ariel King | 2021-04-15 | Standard | 853 | 10 |
| Repeat | no repeats | StepUp Northpoint Houston ×2 | no repeats | Phoenix ×3 | AZ ×3 | no repeats | no repeats | no repeats | no repeats | Flagship ×4 | no repeats | 15 ×2 |
| Missing | — | — | — | — | — | — | — | — | — | — | — | — |
| Range | S001 → S015 | StepUp Airport Houston → StepUp Westside Phoenix | 133 Pine St → 903 River Rd | Atlanta → Portland | AZ → TX | 10425 → 94259 | (555) 165-6539 → (555) 941-1525 | Ariel King → Zoe Smith | 2010-10-14 → 2024-02-28 | Flagship → Standard | 853 → 5745 | 8 → 40 |
| Change | — | — | — | — | — | — | — | — | — | — | — | — |
| **Data profiling results** |  |  |  |  |  |  |  |  |  |  |  |  |
| Sample Count | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 | 15 |
| Missing | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| Unique Values | 15 (100%) | 14 (93.3%) | 15 (100%) | 9 (60%) | 8 (53.3%) | 15 (100%) | 15 (100%) | 15 (100%) | 15 (100%) | 4 (26.7%) | 15 (100%) | 14 (93.3%) |
| Min Value | S001 | StepUp Airport Houston | 133 Pine St | Atlanta | AZ | 10425 | (555) 165-6539 | Ariel King | 2010-10-14 | Flagship | 853 | 8 |
| Min Count | 1 (6.67%) | 1 (6.67%) | 1 (6.67%) | 1 (6.67%) | 3 (20%) | 1 (6.67%) | 1 (6.67%) | 1 (6.67%) | 1 (6.67%) | 4 (26.7%) | 1 (6.67%) | 1 (6.67%) |
| Max Value | S015 | StepUp Westside Phoenix | 903 River Rd | Portland | TX | 94259 | (555) 941-1525 | Zoe Smith | 2024-02-28 | Standard | 5745 | 40 |
| Max Count | 1 (6.67%) | 1 (6.67%) | 1 (6.67%) | 2 (13.3%) | 5 (33.3%) | 1 (6.67%) | 1 (6.67%) | 1 (6.67%) | 1 (6.67%) | 2 (13.3%) | 1 (6.67%) | 1 (6.67%) |
| Min Length | 4 | 18 | 11 | 5 | 2 | — | 14 | 9 | — | 5 | — | — |
| Max Length | 4 | 26 | 12 | 8 | 2 | — | 14 | 17 | — | 8 | — | — |

_BEAM✲ codes in plain text are measured from the data; codes in italics are suggested by AI, with the reasons below. Change can't be seen in a single snapshot of the data._ [What do the codes mean?](../beam-annotations.md)

### Why the suggestions

| | |
|---|---|
| **StoreID [BK](../beam-annotations.md#c-bk) [MD](../beam-annotations.md#c-md)** | The source's identifier for each store, S001 to S015, and the target of `Customers.PreferredStoreID`. |
| **StoreName [?](../beam-annotations.md#c-suspect)** | Not unique: two different stores share one name. |
| **OpenDate [FV](../beam-annotations.md#c-fv)** | A store opens once, so the date should not change. |
| **StoreType [!](../beam-annotations.md#c-important)** | Four store formats (`Outlet`, `Flagship`, `Kiosk`, `Standard`): a natural way to compare stores. |
| **SquareFeet [\[sq ft\]](../beam-annotations.md#c-uom)** | The column name states the unit. |

## Sample rows

_5 random rows from the profiled data._

| **StoreID** | **StoreName** | **Address** | **City** | **State** | **ZipCode** | **Phone** | **Manager** | **OpenDate** | **StoreType** | **SquareFeet** | **Employees** |
|---|---|---|---|---|---|---|---|---|---|---|---|
| S002 | StepUp Airport Houston | 527 River Rd | Houston | TX | 13478 | (555) 674-4257 | Ethan Walker | 2021-04-15 | Outlet | 853 | 15 |
| S004 | StepUp Southside New York | 480 Hill St | New York | NY | 26361 | (555) 487-2291 | Sofia Levi | 2019-10-07 | Flagship | 1175 | 19 |
| S005 | StepUp Mall Phoenix | 885 Pine St | Phoenix | AZ | 23238 | (555) 489-5554 | Daniel Walker | 2019-03-12 | Outlet | 2516 | 22 |
| S012 | StepUp Harbor Chicago | 790 Maple Dr | Chicago | IL | 80697 | (555) 897-9689 | Zoe Smith | 2018-08-01 | Flagship | 3773 | 24 |
| S015 | StepUp Riverside Miami | 133 Pine St | Miami | FL | 39451 | (555) 165-6539 | James Lee | 2015-10-08 | Flagship | 1381 | 8 |

## Relationships (measured)

- Referenced by [Customers](customers.md) `PreferredStoreID` → `StoreID` (100% of values found)

---

## Metadata

_Machine-readable facts about this page, for tools and AI agents._

```yaml
bijoe: "data-story"
schema_version: 1
dataset: "Shoe company"
table: "Stores"
grain: "One row per store"
sampled_rows: 15
columns: 12
description_source: "inferred"
confidence: "high"
beam_table_codes:
  - "[CV]"
beam_source: "{shoe_company.xlsx: Stores}"
generated_at: "2026-11-09T16:24:24+00:00"
```
