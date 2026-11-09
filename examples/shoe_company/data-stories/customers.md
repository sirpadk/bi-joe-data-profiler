[← Shoe company overview](../index.md) · [BEAM✲ annotations](../beam-annotations.md)

# Customers

**BEAM✲:** [\[CV\]](../beam-annotations.md#t-cv) _(suggested by AI)_ · [{shoe_company.xlsx: Customers}](../beam-annotations.md#t-source) _(measured)_

## Description

One row per customer, identified by `CustomerID`, with contact details, demographics and loyalty status (`LoyaltyTier`). Each customer has a home store in `PreferredStoreID`, and every value matches a `Stores.StoreID`. Sign-ups run from 2018-01-26 to 2026-09-17. `TotalOrders` and `LifetimeSpend` are totals stored per customer; with no order table in the workbook, they cannot be split by date, product or store.

> **Where this comes from:** Written by AI from the table's name, columns and values. Check it before you rely on it. Confidence: **high**.
>
> **Based on:**
> - `CustomerID` unique and never missing across 200 rows
> - `PreferredStoreID` has 15 distinct values, all found in `Stores.StoreID` (measured relationship)
> - `SignupDate` min 2018-01-26, max 2026-09-17
> - `TotalOrders` integer 1-40; `LifetimeSpend` decimal 32.68-3950.48
> - `LoyaltyTier` values: `Gold` (59), `Platinum` (49), `Bronze` (47), `Silver` (45)
>
> **Why [\[CV\]](../beam-annotations.md#t-cv):** One row per `CustomerID` (unique in all 200 rows), with descriptive columns and no validity dates, version numbers or current-flag columns, so the sheet holds only current values.

### Open questions for the data owner

- On what date were `TotalOrders` and `LifetimeSpend` last calculated?
- Does `LifetimeSpend` include tax and returns, and what currency is it in?
- `Seattle` is the most common customer city (27) but has no store. Are these online customers?

## Columns

| Column | Type | Measured | Suggested | Missing | Distinct | Examples |
|---|---|---|---|---:|---:|---|
| CustomerID | [C6](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) | [BK](../beam-annotations.md#c-bk) [MD](../beam-annotations.md#c-md) | 0% | 200 | C00001, C00002, C00003 |
| FirstName | [C9](../beam-annotations.md#c-c) text |  |  | 0% | 30 | Olivia, Linda, Mary |
| LastName | [C8](../beam-annotations.md#c-c) text |  |  | 0% | 24 | Lopez, Martinez, Taylor |
| Email | [C31](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) |  | 0% | 200 | olivia.thomas69@mail.test, mary.martinez91@mail.test, robert.anderson10@mail.t… |
| Phone | [C14](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) |  | 0% | 200 | (555) 453-6446, (555) 495-3492, (555) 900-5342 |
| Gender | [C5](../beam-annotations.md#c-c) text |  |  | 0% | 3 | M, F, Other |
| BirthDate | [D](../beam-annotations.md#c-d) date |  | [FV](../beam-annotations.md#c-fv) | 0% | 199 | 1979-07-20, 2003-09-13, 1957-03-17 |
| Address | [C13](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) |  | 0% | 200 | 7470 Elm St, 9679 Elm St, 1325 Elm St |
| City | [C11](../beam-annotations.md#c-c) text |  |  | 0% | 12 | Seattle, Chicago, Portland |
| State | [C2](../beam-annotations.md#c-c) text |  |  | 0% | 11 | TX, WA, IL |
| ZipCode | [I](../beam-annotations.md#c-i) whole number | [ND](../beam-annotations.md#c-nd) |  | 0% | 200 | 34727, 23154, 98389 |
| SignupDate | [D](../beam-annotations.md#c-d) date |  | [FV](../beam-annotations.md#c-fv) | 0% | 194 | 2026-09-15, 2023-01-26, 2022-02-15 |
| LoyaltyTier | [C8](../beam-annotations.md#c-c) text |  | [!](../beam-annotations.md#c-important) | 0% | 4 | Gold, Platinum, Bronze |
| PreferredStoreID | [C4](../beam-annotations.md#c-c) text | [FK](../beam-annotations.md#c-fk) | [\[Stores\]](../beam-annotations.md#c-dim) | 0% | 15 | S010, S005, S001 |
| TotalOrders | [I](../beam-annotations.md#c-i) whole number |  | [FA](../beam-annotations.md#c-fa) [?](../beam-annotations.md#c-suspect) | 0% | 40 | 34, 35, 7 |
| LifetimeSpend | [N6.2](../beam-annotations.md#c-n) number |  | [FA](../beam-annotations.md#c-fa) [?](../beam-annotations.md#c-suspect) | 0% | 200 | 957.24, 3644.45, 3493.36 |
| EmailOptIn | yes/no |  |  | 0% | 2 | True, False |

**Measured** codes come from the data. **Suggested** codes are AI judgement, with the reasons below. [What do the codes mean?](../beam-annotations.md)

**Why the suggestions:**

- **CustomerID** [BK](../beam-annotations.md#c-bk) [MD](../beam-annotations.md#c-md): The source's own identifier for each customer: unique, never missing, `C00001`-style codes.
- **BirthDate** [FV](../beam-annotations.md#c-fv): A person's date of birth should not change; corrections overwrite it.
- **SignupDate** [FV](../beam-annotations.md#c-fv): Signing up happens once, so the date should not change.
- **LoyaltyTier** [!](../beam-annotations.md#c-important): Four tiers (`Gold`, `Platinum`, `Bronze`, `Silver`): the main way to segment customers in a dashboard.
- **PreferredStoreID** [\[Stores\]](../beam-annotations.md#c-dim): Plays the role of 'preferred store' of the `Stores` dimension; every value matches `Stores.StoreID`.
- **TotalOrders** [FA](../beam-annotations.md#c-fa) [?](../beam-annotations.md#c-suspect): A count that sums correctly across customers, but it is a stored total, not individual orders, and its as-of date is unknown.
- **LifetimeSpend** [FA](../beam-annotations.md#c-fa) [?](../beam-annotations.md#c-suspect): An amount that sums across customers. A stored total whose currency, as-of date and treatment of tax and returns are unknown.

## Relationships (measured)

- `PreferredStoreID` → [Stores](stores.md) `StoreID`: 200 of 200 values found (100%) [FK](../beam-annotations.md#c-fk)

---

## Metadata

_Machine-readable facts about this page, for tools and AI agents._

```yaml
bijoe: "data-story"
schema_version: 1
dataset: "Shoe company"
table: "Customers"
rows: 200
columns: 17
description_source: "inferred"
confidence: "high"
beam_table_codes:
  - "[CV]"
beam_source: "{shoe_company.xlsx: Customers}"
generated_at: "2026-11-09T15:33:46+00:00"
```
