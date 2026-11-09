[← Shoe company overview](../index.md)

# Customers

## Description

One row per customer, identified by `CustomerID`, with contact details, demographics and loyalty status (`LoyaltyTier`). Each customer has a home store in `PreferredStoreID`, and every value matches a `Stores.StoreID`. Sign-ups run from 2018-01-26 to 2026-09-17. `TotalOrders` and `LifetimeSpend` are totals stored per customer; with no order table in the workbook, they cannot be split by date, product or store.

> **Where this comes from:** Written by AI from the table's name, columns and values. Check it before you rely on it. Confidence: **high**.
>
> **Based on:**
> - `CustomerID` unique and never missing across 200 rows
> - `PreferredStoreID` has 15 distinct values, all found in `Stores.StoreID` (checked separately)
> - `SignupDate` min 2018-01-26, max 2026-09-17
> - `TotalOrders` integer 1-40; `LifetimeSpend` decimal 32.68-3950.48
> - `LoyaltyTier` values: `Gold` (59), `Platinum` (49), `Bronze` (47), `Silver` (45)

### Open questions for the data owner

- On what date were `TotalOrders` and `LifetimeSpend` last calculated?
- Does `LifetimeSpend` include tax and returns?
- `Seattle` is the most common customer city (27) but has no store. Are these online customers?

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
generated_at: "2026-11-09T15:09:51+00:00"
```
