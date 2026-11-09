# Shoe company: data profile

Reference data for a shoe retailer whose stores all trade as StepUp: three current value [\[CV\]](beam-annotations.md#t-cv) dimensions holding 200 customers, 60 products and 15 stores, and no business events. `Customers` links to `Stores` through `PreferredStoreID`, while no other sheet refers to `Products`. With no orders or sales in the workbook, dashboards can show customer, product and store attributes and the per-customer totals, but not sales over time, by product or by store.

> Summary written by AI from the profile below. Check it before you rely on it.

## At a glance

| | |
|---|---|
| Source | shoe_company.xlsx (excel) |
| Tables | 3 |
| Total rows | 275 |
| Profiled | 2026-11-09 15:33 UTC |
| Purpose | Build reports and dashboards |

## Data stories

One page per table.

| Table | BEAM✲ | Rows | Columns | Description |
|---|---|---:|---:|---|
| [Customers](data-stories/customers.md) | [\[CV\]](beam-annotations.md#t-cv) | 200 | 17 | One row per customer, identified by `CustomerID`, with contact details, demographics and loyalty status (`LoyaltyTier`). |
| [Products](data-stories/products.md) | [\[CV\]](beam-annotations.md#t-cv) | 60 | 14 | One row per product, identified by `ProductID` and a unique `SKU`, covering 8 brands and 8 categories. |
| [Stores](data-stories/stores.md) | [\[CV\]](beam-annotations.md#t-cv) | 15 | 12 | One row per store, identified by `StoreID`, with location, manager, size and `StoreType` (`Outlet`, `Flagship`, `Kiosk` or `Standard`). |

## How the tables connect (measured)

- [Customers](data-stories/customers.md) `PreferredStoreID` → [Stores](data-stories/stores.md) `StoreID` (100% of values found) [FK](beam-annotations.md#c-fk)

## How to read this wiki

Every description says where it comes from:

- **system_metadata**: Taken word for word from the description stored in the source system.
- **user_documentation**: Taken from documentation provided by the data owner.
- **inferred**: Written by AI from the table's name, columns and values. Check it before you rely on it.

Short codes like [\[CV\]](beam-annotations.md#t-cv) or [ND](beam-annotations.md#c-nd) are **BEAM✲ annotations**. Click any code, or see [all BEAM✲ annotations](beam-annotations.md).

The measured facts behind this wiki are in [`_bijoe/profile.json`](_bijoe/profile.json).

---

## Metadata

_Machine-readable facts about this page, for tools and AI agents._

```yaml
bijoe: "data-profile-index"
schema_version: 1
dataset: "Shoe company"
source: "shoe_company.xlsx"
source_type: "files"
connector: "excel"
tables: 3
total_rows: 275
relationships: 1
generated_at: "2026-11-09T15:33:46+00:00"
generator: "bi-joe-data-profiler 0.1.0"
```
