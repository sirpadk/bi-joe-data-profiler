[← Shoe company overview](../index.md) · [BEAM✲ annotations](../beam-annotations.md)

# Stores

**BEAM✲:** [\[CV\]](../beam-annotations.md#t-cv) _(suggested by AI)_ · [{shoe_company.xlsx: Stores}](../beam-annotations.md#t-source) _(measured)_

## Description

One row per store, identified by `StoreID`, with location, manager, size and `StoreType` (`Outlet`, `Flagship`, `Kiosk` or `Standard`). Stores opened between 2010-10-14 and 2024-02-28, in 9 cities across 8 states, and every store is the preferred store of at least one customer. Two different stores share the name `StepUp Northpoint Houston` (an outlet and a standard store at different addresses), so label stores by `StoreID`, or by name plus address.

> **Where this comes from:** Written by AI from the table's name, columns and values. Check it before you rely on it. Confidence: **high**.
>
> **Based on:**
> - `StoreID` unique and never missing across 15 rows
> - `OpenDate` min 2010-10-14, max 2024-02-28
> - `City` 9 distinct, `State` 8 distinct
> - `StoreType` values: `Outlet` (6), `Flagship` (4), `Kiosk` (3), `Standard` (2)
> - `StoreName` 14 distinct in 15 rows; S007 and S008 share a name (checked separately)
> - All 15 `StoreID` values appear in `Customers.PreferredStoreID` (measured relationship)
>
> **Why [\[CV\]](../beam-annotations.md#t-cv):** One row per `StoreID` (unique in all 15 rows), with descriptive attributes and no validity dates or version columns.

### Open questions for the data owner

- Is the shared `StoreName` `StepUp Northpoint Houston` intentional (two stores in one mall) or a data entry error?

## Columns

| Column | Type | Measured | Suggested | Missing | Distinct | Examples |
|---|---|---|---|---:|---:|---|
| StoreID | [C4](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) | [BK](../beam-annotations.md#c-bk) [MD](../beam-annotations.md#c-md) | 0% | 15 | S001, S002, S003 |
| StoreName | [C26](../beam-annotations.md#c-c) text |  | [?](../beam-annotations.md#c-suspect) | 0% | 14 | StepUp Northpoint Houston, StepUp Mall Austin, StepUp Airport Houston |
| Address | [C12](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) |  | 0% | 15 | 35 Cedar Ln, 527 River Rd, 358 Cedar Ln |
| City | [C8](../beam-annotations.md#c-c) text |  |  | 0% | 9 | Houston, Phoenix, Portland |
| State | [C2](../beam-annotations.md#c-c) text |  |  | 0% | 8 | TX, AZ, OR |
| ZipCode | [I](../beam-annotations.md#c-i) whole number | [ND](../beam-annotations.md#c-nd) |  | 0% | 15 | 42098, 13478, 30379 |
| Phone | [C14](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) |  | 0% | 15 | (555) 328-3286, (555) 674-4257, (555) 320-6514 |
| Manager | [C17](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) |  | 0% | 15 | Ava Brown, Ethan Walker, Patricia Williams |
| OpenDate | [D](../beam-annotations.md#c-d) date |  | [FV](../beam-annotations.md#c-fv) | 0% | 15 | 2010-10-14, 2021-04-15, 2020-02-12 |
| StoreType | [C8](../beam-annotations.md#c-c) text |  | [!](../beam-annotations.md#c-important) | 0% | 4 | Outlet, Flagship, Kiosk |
| SquareFeet | [I](../beam-annotations.md#c-i) whole number | [ND](../beam-annotations.md#c-nd) | [\[sq ft\]](../beam-annotations.md#c-uom) | 0% | 15 | 1044, 853, 5745 |
| Employees | [I](../beam-annotations.md#c-i) whole number |  |  | 0% | 14 | 15, 10, 21 |

**Measured** codes come from the data. **Suggested** codes are AI judgement, with the reasons below. [What do the codes mean?](../beam-annotations.md)

**Why the suggestions:**

- **StoreID** [BK](../beam-annotations.md#c-bk) [MD](../beam-annotations.md#c-md): The source's identifier for each store, S001 to S015, and the target of `Customers.PreferredStoreID`.
- **StoreName** [?](../beam-annotations.md#c-suspect): Not unique: two different stores share one name.
- **OpenDate** [FV](../beam-annotations.md#c-fv): A store opens once, so the date should not change.
- **StoreType** [!](../beam-annotations.md#c-important): Four store formats (`Outlet`, `Flagship`, `Kiosk`, `Standard`): a natural way to compare stores.
- **SquareFeet** [\[sq ft\]](../beam-annotations.md#c-uom): The column name states the unit.

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
rows: 15
columns: 12
description_source: "inferred"
confidence: "high"
beam_table_codes:
  - "[CV]"
beam_source: "{shoe_company.xlsx: Stores}"
generated_at: "2026-11-09T15:33:46+00:00"
```
