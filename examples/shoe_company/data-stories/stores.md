[← Shoe company overview](../index.md)

# Stores

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
> - All 15 `StoreID` values appear in `Customers.PreferredStoreID` (checked separately)

### Open questions for the data owner

- Is the shared name `StepUp Northpoint Houston` intentional (two stores in one mall) or a data entry error?

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
generated_at: "2026-11-09T15:09:51+00:00"
```
