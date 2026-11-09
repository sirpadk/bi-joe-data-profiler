[← Shoe company overview](../index.md)

# Products

## Description

One row per product, identified by `ProductID` and a unique `SKU`, covering 8 brands and 8 categories. `UnitPrice` is above `UnitCost` for every product, so margin can be calculated per product. Product names are not unique: `Velora Glide Boots` is three products in different colours, so count and filter by `ProductID`, not by name.

> **Where this comes from:** Written by AI from the table's name, columns and values. Check it before you rely on it. Confidence: **high**.
>
> **Based on:**
> - `ProductID` and `SKU` both unique and never missing across 60 rows
> - `Brand` 8 distinct values, `Category` 8 distinct values
> - `UnitPrice` > `UnitCost` in all 60 rows (checked separately); price 22.99-227.99, cost 8.23-117.92
> - `ProductName` 58 distinct in 60 rows; `Velora Glide Boots` appears 3 times (Grey, Green, Blue)

### Open questions for the data owner

- One active product has a `LaunchDate` of 2026-11-19, after the profile date. Is that a planned launch or an error?
- Should inactive products (`IsActive` = `False`, 6 products) appear in reports?

---

## Metadata

_Machine-readable facts about this page, for tools and AI agents._

```yaml
bijoe: "data-story"
schema_version: 1
dataset: "Shoe company"
table: "Products"
rows: 60
columns: 14
description_source: "inferred"
confidence: "high"
generated_at: "2026-11-09T15:09:51+00:00"
```
