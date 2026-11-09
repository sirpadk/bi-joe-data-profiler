# BEAM✲ annotations

Every short code in this wiki, like **[CV]**, **ND** or **FA**, is a **BEAM✲ annotation**.
BEAM✲ (Business Event Analysis & Modeling) is a notation for describing data in
business terms. Each code packs one fact or design decision into a few letters, so the
pages stay short while staying precise. Click any code in the wiki to jump to its entry here.

[← Back to the overview](index.md)

## How BI Joe uses the codes

| Kind | Who adds it | How to read it |
|---|---|---|
| **Measured** | The profiler, from the data itself | A fact: the data shows it. The data types, uniqueness (**ND**), declared keys (**PK**, **NN**), links between tables (**FK**) and the source (**{Source}**). |
| **Suggested** | The AI, from the evidence | A judgement that someone should check. For example, that a table is a dimension holding current values (**[CV]**), or that a column is an additive fact (**FA**). Every suggestion comes with a reason. |

How the codes are written:
- **Table codes** are in square brackets after the table name, e.g. `Customers [CV]`.
- **Column codes** follow the column name, e.g. `BirthDate FV`.
- A code with ~~strikethrough~~ means the data **does not meet** it, e.g. ~~MD~~ on a column
  that should always be filled in but has gaps.
- Numbers after a code tie related codes together, e.g. `ND1` marks the columns that are
  unique *together*, and `C30` gives a maximum length.

## The 7Ws

BEAM✲ describes every business event by asking who, what, when, where, why, how and how many.
The answers are the event's *details*. The first six usually become dimensions, and
"how many" becomes facts.

| Code | Question | Typical examples |
|---|---|---|
| <a id="w-who"></a>**[who]** | Who is involved? | customer, employee, supplier |
| <a id="w-what"></a>**[what]** | What is it about? | product, service, account |
| <a id="w-when"></a>**[when]** | When did it happen? | order date, ship date |
| <a id="w-where"></a>**[where]** | Where did it happen? | store, warehouse, delivery address |
| <a id="w-why"></a>**[why]** | Why did it happen? | promotion, reason code |
| <a id="w-how"></a>**[how]** | How did it happen? | channel, order number, payment method |
| <a id="w-how-many"></a>**how many** | How much or how many? | quantity, revenue, duration (see [facts](#column-codes-events-and-facts)) |

## Table codes

### Events and fact tables

| Code | Name | What it means | ADWD ch. |
|---|---|---|---|
| <a id="t-de"></a>**[DE]** | Discrete Event | Something that happens at one moment, or over a short time, and is then finished, e.g. a sale or a payment. Becomes a transaction fact table **[TF]**. | |
| <a id="t-re"></a>**[RE]** | Recurring Event | A measurement taken at regular intervals, e.g. daily stock levels or month-end balances. Becomes a periodic snapshot **[PS]**. | 2, 8 |
| <a id="t-ee"></a>**[EE]** | Evolving Event | A process that takes time to complete and passes through milestones, e.g. order → ship → deliver. Becomes an accumulating snapshot **[AS]**. | 2, 4, 8 |
| <a id="t-tf"></a>**[TF]** | Transaction Fact table | The physical table for a discrete event. Rows are usually only ever added. | 5, 8 |
| <a id="t-as"></a>**[AS]** | Accumulating Snapshot | The physical table for an evolving event. Rows are updated as milestones happen, and it usually has several milestone dates. | 8 |
| <a id="t-ps"></a>**[PS]** | Periodic Snapshot | The physical table for a recurring event. It usually holds semi-additive facts (**SA**), such as balances. | 8 |
| <a id="t-ag"></a>**[AG]** | Aggregate | A fact table that summarises another fact table. | 8 |
| <a id="t-df"></a>**[DF]** | Derived Fact table | A fact table built by merging, slicing or pivoting other fact tables. | 8 |
| <a id="t-source"></a>**{Source}** | Data source | The source system table or file the table comes from. | 5 |

### Dimensions

| Code | Name | What it means | ADWD ch. |
|---|---|---|---|
| <a id="t-cv"></a>**[CV]** | Current Value | Keeps only the current value of each attribute. Changes overwrite the old value. Also called a *type 1 slowly changing dimension*. | 4, 5, 6 |
| <a id="t-hv"></a>**[HV]** | Historic Value | Keeps history for at least one attribute, so a change adds a new version of the row. Also called a *type 2 slowly changing dimension*. | 4, 5, 6 |
| <a id="t-rp"></a>**[RP]** | Role-Playing | One dimension used in several roles, e.g. Employee as both salesperson and manager. Calendar is the most common one. | 4 |
| <a id="t-ru"></a>**[RU]** | Rollup | A dimension at a coarser level, derived from a more detailed one, e.g. Month from Calendar. | 4 |
| <a id="t-sd"></a>**[SD]** | Swappable Dimension | One of a set of dimensions that share a key and can stand in for each other, e.g. Business Customer as a subset of Customer. | 6 |
| <a id="t-ml"></a>**[ML]** | Multi-Level | A dimension that also has members for higher levels of its hierarchy, so facts can attach at different levels, e.g. an employee or a whole team. | 6 |
| <a id="t-hm"></a>**[HM]** | Hierarchy Map | A helper table for a hierarchy of varying depth, e.g. a company structure. | 6 |
| <a id="t-mv"></a>**[MV]** | Multi-Valued | A bridge table that links a fact to several values of a dimension at once (many-to-many), often with a weighting factor. | 6, 9 |
| <a id="t-pd"></a>**[PD]** | Pivoted Dimension | Turns several row values into a set of yes/no flag columns, to make combinations easy to select. | 9 |

## Column codes

### General

| Code | Name | What it means | ADWD ch. |
|---|---|---|---|
| <a id="c-md"></a>**MD** | Mandatory | The value should always be there under normal conditions. Shown as ~~MD~~ when the data has gaps. | 2 |
| <a id="c-nn"></a>**NN** | Not Null | The source system does not allow empty values. | 5 |
| <a id="c-nd"></a>**ND**, **ND*n*** | No Duplicates | Every value is different. The numbered form marks columns that are unique *in combination*. In this wiki **measured**: no duplicates were found in the text or whole-number values profiled. Treat it as a candidate key to confirm, not a guaranteed rule. | 9 |
| <a id="c-x"></a>**X*n*** | Exclusive | Only valid for some rows, depending on a defining characteristic (**DC**), e.g. *heel height* only for shoes of type *heels*. | 3, 8 |
| <a id="c-dc"></a>**DC**, **DC*n*,*n*** | Defining Characteristic | Its value decides which exclusive (**X**) columns apply, e.g. *product type*. | 3, 8 |
| <a id="c-w"></a>**[who]** … **[how]** | W-type | Which of the [7Ws](#the-7ws) a detail answers. | 4, 6 |
| <a id="c-dim"></a>**[Dimension]** | Dimension or role | The dimension a detail refers to, e.g. `PreferredStoreID [Stores]` when the preferred store is a *role* of the store dimension. | 4, 6 |
| <a id="c-source"></a>**{Source}** | Data source | The column's name in the source system, when it differs. | 5 |
| <a id="c-unavailable"></a>~~**CODE**~~ | Unavailable or not met | The data doesn't support the code or the column. E.g. ~~MD~~ means the column has gaps, and a struck-through column name means the data isn't available. | 5 |
| <a id="c-suspect"></a>**?** | Suspect | The column still needs clarifying. See the open questions on its page. | |
| <a id="c-important"></a>**!** | Important | A key column for the purpose of this profile. | |

### Data types

All data types are **measured** from the data.

| Code | Name | What it means | ADWD ch. |
|---|---|---|---|
| <a id="c-c"></a>**C*n*** | Character | Short text, with *n* = the longest value seen. | 5 |
| <a id="c-t"></a>**T*n*** | Text | Long free-format text. | 5 |
| <a id="c-n"></a>**N*p*.*s*** | Numeric | A number with decimals: *p* digits in total, *s* of them after the decimal point. | 5 |
| <a id="c-i"></a>**I** | Integer | A whole number. | |
| <a id="c-d"></a>**D**, **D*n*** | Date | A calendar date. Numbers order milestones, e.g. `D1` → `D2`. | 5 |
| <a id="c-dt"></a>**DT**, **DT*n*** | Date/time | A date with a time of day. | 4, 5 |
| <a id="c-b"></a>**B** | Blob | Binary content: documents, images, sound. | 5 |

### Keys

| Code | Name | What it means | ADWD ch. |
|---|---|---|---|
| <a id="c-pk"></a>**PK** | Primary Key | Declared by the source system as the row identifier. | 5 |
| <a id="c-sk"></a>**SK** | Surrogate Key | A meaningless integer key assigned by the data warehouse. | 5 |
| <a id="c-bk"></a>**BK** | Business Key | The source system's own identifier for the thing, e.g. a customer number. | 3, 5 |
| <a id="c-nk"></a>**NK** | Natural Key | An identifier people use in the real world, e.g. a SKU printed on a box. | 5 |
| <a id="c-fk"></a>**FK** | Foreign Key | Points to the key of another table. In this wiki **measured**: every value was found in the other table. | 5 |
| <a id="c-rk"></a>**RK** | Recursive Key | Points to another row in the *same* table, e.g. a parent company. | 6 |

### Dimension attributes

| Code | Name | What it means | ADWD ch. |
|---|---|---|---|
| <a id="c-cv"></a>**CV**, **CV*n*** | Current Value | Only the current value matters. Changes overwrite it ("as is" reporting). | 3, 6 |
| <a id="c-hv"></a>**HV**, **HV*n*** | Historic Value | History matters. Changes keep the old value ("as was" reporting). | 3, 6 |
| <a id="c-fv"></a>**FV** | Fixed Value | Shouldn't change, e.g. a date of birth. Corrections overwrite it. | 3 |
| <a id="c-pv"></a>**PV*n*** | Previous Value | Holds the previous value of the matching **CV*n*** column, e.g. *previous territory*. | 6 |

### Column codes: events and facts

| Code | Name | What it means | ADWD ch. |
|---|---|---|---|
| <a id="c-mv"></a>**MV** | Multi-Value | The detail can hold several values at once and needs a bridge table **[MV]**. | 6, 9 |
| <a id="c-ml"></a>**ML** | Multi-Level | The detail can point at different levels of a hierarchy, e.g. a person or a team. | 6 |
| <a id="c-dd"></a>**DD** | Degenerate Dimension | An identifier kept in the event or fact table itself, with no table of its own, e.g. an order number. | 2, 3, 4, 5 |
| <a id="c-gd"></a>**GD**, **GD*n*** | Granular Dimension | The detail(s) that together define what one row is (the grain). | 2, 8 |
| <a id="c-fa"></a>**FA** | Fully Additive fact | Can be summed across everything, e.g. quantity or revenue. Needs a single unit of measure. | 5, 8 |
| <a id="c-sa"></a>**SA**, **SA*n*** | Semi-Additive fact | Can be summed across some details but not others, e.g. a stock level can't be summed over time. | 8 |
| <a id="c-na"></a>**NA**, **NA*n*** | Non-Additive fact | Can't be summed at all, e.g. unit prices, percentages, temperatures. Use min, max or average. | 8 |
| <a id="c-df"></a>**DF**, **DF=*formula*** | Derived Fact | Can be calculated from other columns in the same table, e.g. `DF=UnitPrice-UnitCost`. | 4 |
| <a id="c-uom"></a>**[*unit*]** | Unit of measure | The unit a fact is stored in, e.g. `[USD]` or `[days]`. Several units list the standard one first. | 2, 4 |

---

### About BEAM✲

BEAM✲ and the Modelstormer spreadsheet are the work of **Lawrence Corr** and
**Jim Stagnitto**, described in *Agile Data Warehouse Design: Collaborative Dimensional
Modeling, from Whiteboard to Star Schema* (DecisionOne Press, 2011). The "ADWD ch."
column points to the chapters that explain each code in depth. The summaries on this
page are BI Joe's own wording. For the full method, see the book and
[modelstorming.com](https://modelstorming.com).

<!-- bijoe: beam-annotations v1. This file is copied as-is into every BI Joe wiki; edit it in skills/bi-joe-data-profiler/assets/. -->
