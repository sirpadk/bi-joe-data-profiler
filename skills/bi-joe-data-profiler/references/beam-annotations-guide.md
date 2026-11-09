# Suggesting BEAM✲ annotations

Every wiki uses BEAM✲ codes. Each code links to `beam-annotations.md`, the reference page
copied from `assets/` into every wiki. You don't write that page. You choose which codes
apply, record them in `descriptions.json`, and the renderer turns every code into a link.

## Who sets which codes

| Kind | Codes | Who |
|---|---|---|
| Measured | data types (`C`*n*, `T`*n*, `N`*p.s*, `I`, `D`, `DT`, `B`), `ND`, `NN`, `PK`, `FK`, `RK`, table `{Source}` | **The engine only.** They appear in `bijoe evidence` under "BEAM measured". Never suggest these yourself: `bijoe check` rejects them. |
| Suggested | table type codes, `BK`, `NK`, `MD`, `FV`, `CV`, `HV`, `PV`, `DC`, `X`, `DD`, `GD`, `FA`, `SA`, `NA`, `DF`, `MV`, `ML`, W-types, `[Dimension]` roles, `[unit]`, `?`, `!` | **You**, with a reason for every one |

Where they go in `descriptions.json` for each table:

```json
"beam": {
  "table": ["CV"],
  "table_why": "One row per `CustomerID` with no validity dates or version columns, so only current values are kept.",
  "columns": {
    "CustomerID": {"codes": ["BK", "MD"], "why": "The source system's own identifier for each customer."},
    "BirthDate":  {"codes": ["FV"], "why": "A person's date of birth should not change."}
  }
}
```

Leave out any column you have nothing to suggest for. Don't annotate every column just
to fill the table.

## Table codes

First decide whether the table records **things** (customers, products, stores) or
**business events** (orders, payments, shipments).

- **Things → a dimension.** The signs are a unique identifier and descriptive columns
  (names, categories, addresses).
  - **[CV]** is the default for a source extract: one row per key, and no
    effective/end-date, version or "current" columns. You're describing what the data
    *holds*, not a warehouse design decision.
  - **[HV]** only if the data really keeps history: the same business key repeats, with
    validity dates or a current flag.
  - **[RP]** if measured relationships show two or more columns in other tables pointing
    to this one in different roles (e.g. `BillToCustomerID` and `ShipToCustomerID`).
  - **[RU]**, **[SD]**, **[ML]**, **[HM]**, **[MV]** and **[PD]** only with clear
    structural evidence. Name that evidence in `table_why`.
- **Events → an event code.** The signs are a when-date, and amounts or quantities, with
  many rows per customer or product.
  - **[DE]**: one date, and the row is finished once it happens (a sale, a payment).
  - **[EE]**: several milestone dates for one process (ordered, shipped, delivered),
    where later milestones are often still empty.
  - **[RE]**: a snapshot or period date, where each key repeats once per period with a
    level or balance.
- **[TF]**, **[AS]**, **[PS]**, **[AG]** and **[DF]** are for tables that are *already*
  warehouse fact tables. Look for names like `fact_` or `f_`, or surrogate keys
  everywhere. Don't use them for source extracts.

## Column codes

| Code | Suggest when | Evidence to cite |
|---|---|---|
| **BK** | The column is the source system's own identifier for the row's thing | Measured `ND`, nothing missing, and an ID- or code-like name and values |
| **NK** | People use the identifier in the real world (SKU, ISBN, licence plate) | Name and values, e.g. `SKU-639131` |
| **MD** | The business would need it filled in for every row (identifiers, names, key dates) | Its role in the table. If the data has gaps it is **shown struck through as ~~MD~~ automatically**, so suggest MD for what *should* be true. |
| **FV** | The value shouldn't change for a member (birth date, launch date, opening date) | The meaning of the name |
| **CV / HV / PV** | **Only if the user said** how they want changes handled. This is a business decision, not something the data shows. Otherwise ask, via `open_questions`. | The user's own words |
| **DC / X*n*** | A type column decides which other columns apply | Columns that are empty for some type values and filled for others |
| **DD** | An event table holds a transaction number with no table of its own | No measured relationship from it |
| **GD** | Event tables only: the details that together make a row unique | Measured `ND`, or uniqueness of the combination |
| **FA** | An amount or count that can be summed across everything (revenue, quantity) | A numeric type and its meaning. Needs one unit. |
| **SA** | A level or balance that can't be summed over time (stock level, account balance) | The meaning, e.g. `StockQty` is stock on hand |
| **NA** | Unit prices, percentages, rates, ratios, temperatures | The meaning. Unit prices are always NA. |
| **DF=*formula*** | The value can be calculated from other columns in the same table | Only if you checked it, or the user said so. Otherwise put it in `open_questions`. |
| **[who] … [how]** | Event tables: which W each detail answers | The meaning of the name |
| **[Dimension]** | A column points to another table in a role, e.g. `PreferredStoreID [Stores]` | A **measured** relationship. Use the exact table name. |
| **[unit]** | The unit is known, e.g. `[USD]` or `[days]` | Only if names, values or documentation state it. **Never assume a currency.** If it's unknown, mark the column `?` and ask. |
| **!** | The column is central to the user's stated purpose or focus | The purpose recorded at the top of `bijoe evidence`. Use at most about 3 per table. |
| **?** | Its meaning or quality is unclear | Add an `open_questions` entry that names the column. `bijoe check` warns if you don't. |

## Writing codes in prose

In descriptions, `table_why`, the reasons and open questions, you may write table codes
and W-types in brackets, e.g. "a current value [CV] dimension" or "the [when] of the
order". The renderer turns them into links. Don't put bare column codes like FA or MD in
prose: they belong in the column table.

## Pitfalls

- A table being a *dimension* doesn't make every number in it a fact. Totals stored on
  a customer, such as `LifetimeSpend`, are facts (**FA**), but say in the reason that
  they're stored totals, not events.
- `ND` on a small table can be chance. Don't suggest `BK` just because a column happens
  to be unique (e.g. `SquareFeet`).
- Keep it proportionate. A newcomer is better served by five well-chosen, explained
  codes than by thirty.
