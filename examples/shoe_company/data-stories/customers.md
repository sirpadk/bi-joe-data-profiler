[← Shoe company overview](../index.md) · [BEAM✲ annotations](../beam-annotations.md) · [How to read this wiki](../how-to-read.md)

# Customers

| | |
|---|---|
| **Grain** | One row per customer |
| **Definition** | A customer is a person who has made one or more purchases from the company, identified by `CustomerID`. |
| **BEAM✲** | [\[CV\]](../beam-annotations.md#t-cv) _(suggested by AI)_ |
| **Why [\[CV\]](../beam-annotations.md#t-cv)** | One row per `CustomerID` (unique in all 200 rows), with descriptive columns and no validity dates, version numbers or current-flag columns, so the sheet holds only current values. |
| **Source** | [{shoe_company.xlsx: Customers}](../beam-annotations.md#t-source) _(measured)_ |
| **Sampled rows** | 200 |
| **Columns** | 17 |
| **Description source** | Written by AI from the data. Check before relying on it. |
| **Confidence** | high |

## Description

One row per customer, identified by `CustomerID`, with contact details, demographics and loyalty status (`LoyaltyTier`). Each customer has a home store in `PreferredStoreID`, and every value matches a `Stores.StoreID`. Sign-ups run from 2018-01-26 to 2026-09-17. `TotalOrders` and `LifetimeSpend` are totals stored per customer; with no order table in the workbook, they cannot be split by date, product or store.

**Based on:**

- `CustomerID` unique and never missing across 200 rows
- `PreferredStoreID` has 15 distinct values, all found in `Stores.StoreID` (measured relationship)
- `SignupDate` min 2018-01-26, max 2026-09-17
- `TotalOrders` integer 1-40; `LifetimeSpend` decimal 32.68-3950.48
- `LoyaltyTier` values: `Gold` (59), `Platinum` (49), `Bronze` (47), `Silver` (45)
- `FirstName`, `LastName`, `BirthDate` and `Gender` (`M`, `F`, `Other`) describe people
- `TotalOrders` minimum is 1

### Open questions for the data owner

- On what date were `TotalOrders` and `LifetimeSpend` last calculated?
- Does `LifetimeSpend` include tax and returns, and what currency is it in?
- `Seattle` is the most common customer city (27) but has no store. Are these online customers?

## Columns

| | **CustomerID** | **FirstName** | **LastName** | **Email** | **Phone** | **Gender** | **BirthDate** | **Address** | **City** | **State** | **ZipCode** | **SignupDate** | **LoyaltyTier** | **PreferredStoreID** | **TotalOrders** | **LifetimeSpend** | **EmailOptIn** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Data type** | [C6](../beam-annotations.md#c-c) text | [C9](../beam-annotations.md#c-c) text | [C8](../beam-annotations.md#c-c) text | [C31](../beam-annotations.md#c-c) text | [C14](../beam-annotations.md#c-c) text | [C5](../beam-annotations.md#c-c) text | [D](../beam-annotations.md#c-d) date | [C13](../beam-annotations.md#c-c) text | [C11](../beam-annotations.md#c-c) text | [C2](../beam-annotations.md#c-c) text | [I](../beam-annotations.md#c-i) whole number | [D](../beam-annotations.md#c-d) date | [C8](../beam-annotations.md#c-c) text | [C4](../beam-annotations.md#c-c) text | [I](../beam-annotations.md#c-i) whole number | [N6.2](../beam-annotations.md#c-n) number | yes/no |
| **BEAM✲** | [ND](../beam-annotations.md#c-nd) *[BK](../beam-annotations.md#c-bk)* *[MD](../beam-annotations.md#c-md)* |  |  | [ND](../beam-annotations.md#c-nd) | [ND](../beam-annotations.md#c-nd) |  | *[FV](../beam-annotations.md#c-fv)* | [ND](../beam-annotations.md#c-nd) |  |  | [ND](../beam-annotations.md#c-nd) | *[FV](../beam-annotations.md#c-fv)* | *[!](../beam-annotations.md#c-important)* | [FK](../beam-annotations.md#c-fk) *[\[Stores\]](../beam-annotations.md#c-dim)* | *[FA](../beam-annotations.md#c-fa)* *[?](../beam-annotations.md#c-suspect)* | *[FA](../beam-annotations.md#c-fa)* *[?](../beam-annotations.md#c-suspect)* |  |
| **Example data** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Typical | C00001 | Olivia | Lopez | olivia.thomas69@mail.test | (555) 453-6446 | M | 1979-07-20 | 7470 Elm St | Seattle | TX | 34727 | 2026-09-15 | Gold | S010 | 34 | 957.24 | True |
| Different | C00002 | Sofia | Clark | ariel.brown50@mail.test | (555) 104-5076 | Other | 1955-05-14 | 1009 Oak Ave | Houston | CA | 10089 | 2018-01-26 | Silver | S004 | 37 | 1000.87 | False |
| Repeat | no repeats | Linda ×10 | Martinez ×14 | no repeats | no repeats | F ×65 | 1979-07-20 ×2 | no repeats | Chicago ×22 | WA ×27 | no repeats | 2023-01-26 ×2 | Platinum ×49 | S005 ×19 | 35 ×8 | no repeats | False ×73 |
| Missing | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Range | C00001 → C00200 | Ariel → Zoe | Anderson → Young | ariel.brown50@mail.test → zoe.williams30@sample.org | (555) 104-5076 → (555) 998-4522 | F → Other | 1955-05-14 → 2008-08-26 | 1009 Oak Ave → 9894 Main St | Atlanta → Seattle | AZ → WA | 10089 → 99881 | 2018-01-26 → 2026-09-17 | Bronze → Silver | S001 → S015 | 1 → 40 | 32.68 → 3950.48 | False → True |
| Change | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **Data profiling results** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Sample Count | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 | 200 |
| Missing | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| Unique Values | 200 (100%) | 30 (15%) | 24 (12%) | 200 (100%) | 200 (100%) | 3 (1.5%) | 199 (99.5%) | 200 (100%) | 12 (6%) | 11 (5.5%) | 200 (100%) | 194 (97%) | 4 (2%) | 15 (7.5%) | 40 (20%) | 200 (100%) | 2 (1%) |
| Min Value | C00001 | Ariel | Anderson | ariel.brown50@mail.test | (555) 104-5076 | F | 1955-05-14 | 1009 Oak Ave | Atlanta | AZ | 10089 | 2018-01-26 | Bronze | S001 | 1 | 32.68 | False |
| Min Count | 1 (0.5%) | 9 (4.5%) | 10 (5%) | 1 (0.5%) | 1 (0.5%) | 65 (32.5%) | 1 (0.5%) | 1 (0.5%) | 21 (10.5%) | 16 (8%) | 1 (0.5%) | 1 (0.5%) | 47 (23.5%) | 17 (8.5%) | 6 (3%) | 1 (0.5%) | 73 (36.5%) |
| Max Value | C00200 | Zoe | Young | zoe.williams30@sample.org | (555) 998-4522 | Other | 2008-08-26 | 9894 Main St | Seattle | WA | 99881 | 2026-09-17 | Silver | S015 | 40 | 3950.48 | True |
| Max Count | 1 (0.5%) | 4 (2%) | 7 (3.5%) | 1 (0.5%) | 1 (0.5%) | 63 (31.5%) | 1 (0.5%) | 1 (0.5%) | 27 (13.5%) | 27 (13.5%) | 1 (0.5%) | 1 (0.5%) | 45 (22.5%) | 14 (7%) | 5 (2.5%) | 1 (0.5%) | 127 (63.5%) |
| Min Length | 6 | 3 | 3 | 21 | 14 | 1 | — | 10 | 5 | 2 | — | — | 4 | 4 | — | — | — |
| Max Length | 6 | 9 | 8 | 31 | 14 | 5 | — | 13 | 11 | 2 | — | — | 8 | 4 | — | — | — |

_BEAM✲ codes in plain text are measured from the data; codes in italics are suggested by AI, with the reasons below. Change can't be seen in a single snapshot of the data._ [What do the codes mean?](../beam-annotations.md)

### Why the suggestions

| | |
|---|---|
| **CustomerID [BK](../beam-annotations.md#c-bk) [MD](../beam-annotations.md#c-md)** | The source's own identifier for each customer: unique, never missing, `C00001`-style codes. |
| **BirthDate [FV](../beam-annotations.md#c-fv)** | A person's date of birth should not change; corrections overwrite it. |
| **SignupDate [FV](../beam-annotations.md#c-fv)** | Signing up happens once, so the date should not change. |
| **LoyaltyTier [!](../beam-annotations.md#c-important)** | Four tiers (`Gold`, `Platinum`, `Bronze`, `Silver`): the main way to segment customers in a dashboard. |
| **PreferredStoreID [\[Stores\]](../beam-annotations.md#c-dim)** | Plays the role of 'preferred store' of the `Stores` dimension; every value matches `Stores.StoreID`. |
| **TotalOrders [FA](../beam-annotations.md#c-fa) [?](../beam-annotations.md#c-suspect)** | A count that sums correctly across customers, but it is a stored total, not individual orders, and its as-of date is unknown. |
| **LifetimeSpend [FA](../beam-annotations.md#c-fa) [?](../beam-annotations.md#c-suspect)** | An amount that sums across customers. A stored total whose currency, as-of date and treatment of tax and returns are unknown. |

## Sample rows

_5 random rows from the profiled data._

| **CustomerID** | **FirstName** | **LastName** | **Email** | **Phone** | **Gender** | **BirthDate** | **Address** | **City** | **State** | **ZipCode** | **SignupDate** | **LoyaltyTier** | **PreferredStoreID** | **TotalOrders** | **LifetimeSpend** | **EmailOptIn** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| C00021 | Yael | Lopez | yael.lopez55@sample.org | (555) 152-5712 | Other | 1974-06-04 | 9478 Hill St | Austin | TX | 37884 | 2026-06-01 | Silver | S011 | 31 | 920.25 | False |
| C00113 | Omar | Walker | omar.walker88@mail.test | (555) 525-8272 | F | 1965-02-19 | 515 Pine St | Boston | MA | 48284 | 2022-08-03 | Bronze | S005 | 15 | 2164.31 | False |
| C00137 | Ethan | Lopez | ethan.lopez11@sample.org | (555) 197-9280 | M | 1995-07-03 | 9707 River Rd | Boston | MA | 18163 | 2026-05-22 | Platinum | S011 | 9 | 969.98 | False |
| C00176 | Elizabeth | Taylor | elizabeth.taylor77@sampl… | (555) 445-8105 | Other | 1963-06-16 | 5895 Pine St | Portland | OR | 31611 | 2023-11-02 | Platinum | S001 | 15 | 920.56 | True |
| C00199 | Mary | Jones | mary.jones7@sample.org | (555) 730-5934 | F | 2005-10-18 | 5876 Oak Ave | Seattle | WA | 51662 | 2024-09-10 | Silver | S003 | 34 | 300.66 | True |

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
grain: "One row per customer"
sampled_rows: 200
columns: 17
description_source: "inferred"
confidence: "high"
beam_table_codes:
  - "[CV]"
beam_source: "{shoe_company.xlsx: Customers}"
generated_at: "2026-11-09T16:24:24+00:00"
```
