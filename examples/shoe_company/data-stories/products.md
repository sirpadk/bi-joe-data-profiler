[← Shoe company overview](../index.md) · [BEAM✲ annotations](../beam-annotations.md)

# Products

**BEAM✲:** [\[CV\]](../beam-annotations.md#t-cv) _(suggested by AI)_ · [{shoe_company.xlsx: Products}](../beam-annotations.md#t-source) _(measured)_

## Description

One row per product, identified by `ProductID` and a unique `SKU`, covering 8 brands and 8 categories. `UnitPrice` is above `UnitCost` for every product, so margin can be calculated per product. Product names are not unique: `Velora Glide Boots` is three products in different colours, so count and filter by `ProductID`, not by name.

> **Where this comes from:** Written by AI from the table's name, columns and values. Check it before you rely on it. Confidence: **high**.
>
> **Based on:**
> - `ProductID` and `SKU` both unique and never missing across 60 rows
> - `Brand` 8 distinct values, `Category` 8 distinct values
> - `UnitPrice` > `UnitCost` in all 60 rows (checked separately); price 22.99-227.99, cost 8.23-117.92
> - `ProductName` 58 distinct in 60 rows; `Velora Glide Boots` appears 3 times (Grey, Green, Blue)
>
> **Why [\[CV\]](../beam-annotations.md#t-cv):** One row per `ProductID` (unique in all 60 rows), with descriptive attributes and no validity dates or version columns.

### Open questions for the data owner

- One active product has a `LaunchDate` of 2026-11-19, after the profile date. Is that a planned launch or an error?
- Should inactive products (`IsActive` = `False`, 6 products) appear in reports?
- What currency are `UnitPrice` and `UnitCost` in, and is `UnitPrice` before or after tax?

## Columns

| Column | Type | Measured | Suggested | Missing | Distinct | Examples |
|---|---|---|---|---:|---:|---|
| ProductID | [C5](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) | [BK](../beam-annotations.md#c-bk) [MD](../beam-annotations.md#c-md) | 0% | 60 | P0001, P0002, P0003 |
| SKU | [C10](../beam-annotations.md#c-c) text | [ND](../beam-annotations.md#c-nd) | [NK](../beam-annotations.md#c-nk) [MD](../beam-annotations.md#c-md) | 0% | 60 | SKU-639131, SKU-299659, SKU-522179 |
| ProductName | [C27](../beam-annotations.md#c-c) text |  |  | 0% | 58 | Velora Glide Boots, Velora Pulse Sandals, Luma Glide Kids |
| Brand | [C10](../beam-annotations.md#c-c) text |  |  | 0% | 8 | Luma, Northfield, TerraTrek |
| Category | [C10](../beam-annotations.md#c-c) text |  | [!](../beam-annotations.md#c-important) | 0% | 8 | Sandals, Kids, Running |
| Gender | [C6](../beam-annotations.md#c-c) text |  |  | 0% | 4 | Women, Unisex, Men |
| Color | [C5](../beam-annotations.md#c-c) text |  |  | 0% | 9 | White, Green, Grey |
| Material | [C9](../beam-annotations.md#c-c) text |  |  | 0% | 6 | Rubber, Leather, Suede |
| SizeRange | [C4](../beam-annotations.md#c-c) text |  |  | 0% | 3 | 7-14, 6-12, 1-7 |
| UnitPrice | [N5.2](../beam-annotations.md#c-n) number |  | [NA](../beam-annotations.md#c-na) [?](../beam-annotations.md#c-suspect) | 0% | 51 | 143.99, 32.99, 40.99 |
| UnitCost | [N5.2](../beam-annotations.md#c-n) number |  | [NA](../beam-annotations.md#c-na) | 0% | 60 | 8.23, 17.32, 85.82 |
| StockQty | [I](../beam-annotations.md#c-i) whole number |  | [SA](../beam-annotations.md#c-sa) | 0% | 56 | 61, 460, 446 |
| LaunchDate | [D](../beam-annotations.md#c-d) date |  | [FV](../beam-annotations.md#c-fv) [?](../beam-annotations.md#c-suspect) | 0% | 57 | 2024-10-08, 2023-06-11, 2026-03-16 |
| IsActive | yes/no |  |  | 0% | 2 | True, False |

**Measured** codes come from the data. **Suggested** codes are AI judgement, with the reasons below. [What do the codes mean?](../beam-annotations.md)

**Why the suggestions:**

- **ProductID** [BK](../beam-annotations.md#c-bk) [MD](../beam-annotations.md#c-md): The source's identifier for each product: unique, never missing, `P0001`-style codes.
- **SKU** [NK](../beam-annotations.md#c-nk) [MD](../beam-annotations.md#c-md): Unique `SKU-639131`-style codes; a SKU is the identifier people use on shelves and boxes.
- **Category** [!](../beam-annotations.md#c-important): Eight categories: the natural first grouping for product dashboards.
- **UnitPrice** [NA](../beam-annotations.md#c-na) [?](../beam-annotations.md#c-suspect): A unit price can't be summed; use average, min or max. Its currency is unknown.
- **UnitCost** [NA](../beam-annotations.md#c-na): A cost per unit can't be summed, for the same reason as the price.
- **StockQty** [SA](../beam-annotations.md#c-sa): A stock level: it can be summed across products, but not over time.
- **LaunchDate** [FV](../beam-annotations.md#c-fv) [?](../beam-annotations.md#c-suspect): A launch date should not change, but one value lies in the future.

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
beam_table_codes:
  - "[CV]"
beam_source: "{shoe_company.xlsx: Products}"
generated_at: "2026-11-09T15:33:46+00:00"
```
