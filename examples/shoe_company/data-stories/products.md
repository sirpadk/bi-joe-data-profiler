[← Shoe company overview](../index.md) · [BEAM✲ annotations](../beam-annotations.md) · [How to read this wiki](../how-to-read.md)

# Products

| | |
|---|---|
| **Grain** | One row per product |
| **Definition** | A product is a shoe model in one colour that the company sells or has sold, identified by `ProductID` and `SKU`. |
| **BEAM✲** | [\[CV\]](../beam-annotations.md#t-cv) _(suggested by AI)_ |
| **Why [\[CV\]](../beam-annotations.md#t-cv)** | One row per `ProductID` (unique in all 60 rows), with descriptive attributes and no validity dates or version columns. |
| **Source** | [{shoe_company.xlsx: Products}](../beam-annotations.md#t-source) _(measured)_ |
| **Sampled rows** | 60 |
| **Columns** | 14 |
| **Description source** | Written by AI from the data. Check before relying on it. |
| **Confidence** | high |

## Description

One row per product, identified by `ProductID` and a unique `SKU`, covering 8 brands and 8 categories. `UnitPrice` is above `UnitCost` for every product, so margin can be calculated per product. Product names are not unique: `Velora Glide Boots` is three products in different colours, so count and filter by `ProductID`, not by name.

**Based on:**

- `ProductID` and `SKU` both unique and never missing across 60 rows
- `Brand` 8 distinct values, `Category` 8 distinct values
- `UnitPrice` > `UnitCost` in all 60 rows (checked separately); price 22.99-227.99, cost 8.23-117.92
- `ProductName` 58 distinct in 60 rows; `Velora Glide Boots` appears 3 times (Grey, Green, Blue)
- Each row has one `Color`; `Velora Glide Boots` exists as three products in different colours
- `IsActive` is `False` for 6 products

### Open questions for the data owner

- One active product has a `LaunchDate` of 2026-11-19, after the profile date. Is that a planned launch or an error?
- Should inactive products (`IsActive` = `False`, 6 products) appear in reports?
- What currency are `UnitPrice` and `UnitCost` in, and is `UnitPrice` before or after tax?

## Columns

| | **ProductID** | **SKU** | **ProductName** | **Brand** | **Category** | **Gender** | **Color** | **Material** | **SizeRange** | **UnitPrice** | **UnitCost** | **StockQty** | **LaunchDate** | **IsActive** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **Data type** | [C5](../beam-annotations.md#c-c) text | [C10](../beam-annotations.md#c-c) text | [C27](../beam-annotations.md#c-c) text | [C10](../beam-annotations.md#c-c) text | [C10](../beam-annotations.md#c-c) text | [C6](../beam-annotations.md#c-c) text | [C5](../beam-annotations.md#c-c) text | [C9](../beam-annotations.md#c-c) text | [C4](../beam-annotations.md#c-c) text | [N5.2](../beam-annotations.md#c-n) number | [N5.2](../beam-annotations.md#c-n) number | [I](../beam-annotations.md#c-i) whole number | [D](../beam-annotations.md#c-d) date | yes/no |
| **BEAM✲** | [ND](../beam-annotations.md#c-nd) *[BK](../beam-annotations.md#c-bk)* *[MD](../beam-annotations.md#c-md)* | [ND](../beam-annotations.md#c-nd) *[NK](../beam-annotations.md#c-nk)* *[MD](../beam-annotations.md#c-md)* |  |  | *[!](../beam-annotations.md#c-important)* |  |  |  |  | *[NA](../beam-annotations.md#c-na)* *[?](../beam-annotations.md#c-suspect)* | *[NA](../beam-annotations.md#c-na)* | *[SA](../beam-annotations.md#c-sa)* | *[FV](../beam-annotations.md#c-fv)* *[?](../beam-annotations.md#c-suspect)* |  |
| **Example data** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Typical | P0001 | SKU-639131 | Velora Glide Boots | Luma | Sandals | Women | White | Rubber | 7-14 | 143.99 | 8.23 | 61 | 2024-10-08 | True |
| Different | P0002 | SKU-109767 | Kicko Edge Boots | PeakRun | Casual | Kids | Black | Canvas | 1-7 | 102.99 | 105.45 | 108 | 2020-02-23 | False |
| Repeat | no repeats | no repeats | Velora Glide Boots ×3 | Northfield ×9 | Kids ×9 | Unisex ×17 | Green ×9 | Leather ×12 | 6-12 ×19 | 32.99 ×2 | no repeats | 460 ×2 | 2023-06-11 ×2 | False ×6 |
| Missing | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| Range | P0001 → P0060 | SKU-109767 → SKU-994905 | Kicko Edge Boots → Velora Summit Sandals | Kicko → Velora | Basketball → Sandals | Kids → Women | Beige → White | Canvas → Synthetic | 1-7 → 7-14 | 22.99 → 227.99 | 8.23 → 117.92 | 4 → 498 | 2020-02-23 → 2026-11-19 | False → True |
| Change | — | — | — | — | — | — | — | — | — | — | — | — | — | — |
| **Data profiling results** |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
| Sample Count | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 | 60 |
| Missing | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) | 0 (0%) |
| Unique Values | 60 (100%) | 60 (100%) | 58 (96.7%) | 8 (13.3%) | 8 (13.3%) | 4 (6.67%) | 9 (15%) | 6 (10%) | 3 (5%) | 51 (85%) | 60 (100%) | 56 (93.3%) | 57 (95%) | 2 (3.33%) |
| Min Value | P0001 | SKU-109767 | Kicko Edge Boots | Kicko | Basketball | Kids | Beige | Canvas | 1-7 | 22.99 | 8.23 | 4 | 2020-02-23 | False |
| Min Count | 1 (1.67%) | 1 (1.67%) | 1 (1.67%) | 6 (10%) | 6 (10%) | 9 (15%) | 7 (11.7%) | 7 (11.7%) | 9 (15%) | 1 (1.67%) | 1 (1.67%) | 1 (1.67%) | 1 (1.67%) | 6 (10%) |
| Max Value | P0060 | SKU-994905 | Velora Summit Sandals | Velora | Sandals | Women | White | Synthetic | 7-14 | 227.99 | 117.92 | 498 | 2026-11-19 | True |
| Max Count | 1 (1.67%) | 1 (1.67%) | 1 (1.67%) | 7 (11.7%) | 10 (16.7%) | 19 (31.7%) | 13 (21.7%) | 7 (11.7%) | 32 (53.3%) | 1 (1.67%) | 1 (1.67%) | 1 (1.67%) | 1 (1.67%) | 54 (90%) |
| Min Length | 5 | 10 | 14 | 4 | 4 | 3 | 3 | 4 | 3 | — | — | — | — | — |
| Max Length | 5 | 10 | 27 | 10 | 10 | 6 | 5 | 9 | 4 | — | — | — | — | — |

_BEAM✲ codes in plain text are measured from the data; codes in italics are suggested by AI, with the reasons below. Change can't be seen in a single snapshot of the data._ [What do the codes mean?](../beam-annotations.md)

### Why the suggestions

| | |
|---|---|
| **ProductID [BK](../beam-annotations.md#c-bk) [MD](../beam-annotations.md#c-md)** | The source's identifier for each product: unique, never missing, `P0001`-style codes. |
| **SKU [NK](../beam-annotations.md#c-nk) [MD](../beam-annotations.md#c-md)** | Unique `SKU-639131`-style codes; a SKU is the identifier people use on shelves and boxes. |
| **Category [!](../beam-annotations.md#c-important)** | Eight categories: the natural first grouping for product dashboards. |
| **UnitPrice [NA](../beam-annotations.md#c-na) [?](../beam-annotations.md#c-suspect)** | A unit price can't be summed; use average, min or max. Its currency is unknown. |
| **UnitCost [NA](../beam-annotations.md#c-na)** | A cost per unit can't be summed, for the same reason as the price. |
| **StockQty [SA](../beam-annotations.md#c-sa)** | A stock level: it can be summed across products, but not over time. |
| **LaunchDate [FV](../beam-annotations.md#c-fv) [?](../beam-annotations.md#c-suspect)** | A launch date should not change, but one value lies in the future. |

## Sample rows

_5 random rows from the profiled data._

| **ProductID** | **SKU** | **ProductName** | **Brand** | **Category** | **Gender** | **Color** | **Material** | **SizeRange** | **UnitPrice** | **UnitCost** | **StockQty** | **LaunchDate** | **IsActive** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P0003 | SKU-522179 | Stridex Breeze Running | Stridex | Running | Men | Brown | Leather | 7-14 | 143.99 | 85.82 | 127 | 2021-04-18 | True |
| P0034 | SKU-309044 | UrbanSole Aero Casual | UrbanSole | Casual | Men | Navy | Mesh | 7-14 | 103.99 | 53.34 | 64 | 2023-11-04 | True |
| P0041 | SKU-612311 | Luma Volt Running | Luma | Running | Men | Grey | Rubber | 7-14 | 126.99 | 50.51 | 243 | 2025-12-16 | True |
| P0042 | SKU-421080 | UrbanSole Trail Running | UrbanSole | Running | Unisex | Brown | Suede | 7-14 | 79.99 | 32.43 | 283 | 2024-06-14 | True |
| P0045 | SKU-831295 | TerraTrek Summit Boots | TerraTrek | Boots | Unisex | Blue | Leather | 7-14 | 133.99 | 79.53 | 446 | 2020-10-10 | True |

---

## Metadata

_Machine-readable facts about this page, for tools and AI agents._

```yaml
bijoe: "data-story"
schema_version: 1
dataset: "Shoe company"
table: "Products"
grain: "One row per product"
sampled_rows: 60
columns: 14
description_source: "inferred"
confidence: "high"
beam_table_codes:
  - "[CV]"
beam_source: "{shoe_company.xlsx: Products}"
generated_at: "2026-11-09T16:24:24+00:00"
```
