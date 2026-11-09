# Writing descriptions

A description tells a reader something they could not get from the table name alone,
and every word of it can be traced back to evidence. People read these pages, and so
do other AI agents, which will act on what you write. A confident wrong description
does more harm than an honest "unclear".

## 1. Pick the source, in this order

| Priority | When | `source` | What you do |
|---|---|---|---|
| 1 | The source system stores a table description (the profiler fills it in) | `system_metadata` | Keep it **exactly as it is**. Never reword or "improve" it. You may add grounded context in `ai_notes`. |
| 2 | The user gave you documentation, a data dictionary or an explanation | `user_documentation` | Use their wording or a faithful condensed version. List what you used in `evidence`, e.g. "Data dictionary v3 (sales.xlsx, sheet Docs)". |
| 3 | Neither of the above | `inferred` | Write it from the evidence, following the rules below. `confidence` and `evidence` are required. |

Column comments from the source system (shown in the `comment` column of `bijoe evidence`)
count as strong evidence for an inferred table description. Cite them.

## 2. What a good description says

Write two to five sentences, in this order of value. Skip any point you have no evidence for.

1. **What one row is.** This is the single most useful fact. Example: "One row per order
   line: an order with three products has three rows." Evidence: a column that is unique
   and has no missing values, or a combination of columns, compared with the row count.
2. **What business event or thing it records**, if the names and values show it. Example:
   "Customer sign-ups, from the web shop and the in-store form (`channel` = `web`,
   `store`)."
3. **How it connects to other tables.** Example: "Each row points to a customer through
   `cust_id`, which matches `customers.cust_id`." Only say this if the column exists in
   both tables and the values look compatible (same type and range).
4. **What period and scope it covers.** Example: "Orders from 2021-03-01 to 2024-11-30",
   taken from the min and max of a date column. Or: "Covers 4 countries: DK, SE, NO, FI".
5. **At most one caveat a reader must know before using the table.** Example:
   "`amount` is stored as text and 2% of values are not numbers." Leave the full
   data-quality review for later sections.

Fit the depth to the user's `purpose`, `audience` and `focus` (shown at the top of
`bijoe evidence`). Someone building a dashboard needs the grain and the time range.
Someone sourcing data into a warehouse needs the keys and the caveats.

## 3. Hard rules

- **Every claim has evidence.** If you can't point to a column, value, count or document,
  leave the claim out. List the facts you relied on in `evidence`, citing exact names
  and numbers, e.g. "`order_id` unique and never missing across 48,213 rows".
- **Backticks only for real things.** Put `backticks` only around table names, column
  names and values that appear in the evidence. `bijoe check` flags any backticked name
  it can't find in the profile. Treat that as a possible invention.
- **Don't expand names you can't confirm.** Don't spell out abbreviations, translate
  codes or name source systems unless the data shows it. `KDNR` might be a customer
  number. If the values don't confirm it, write "`KDNR` (likely a customer number;
  unconfirmed)", or move it to `open_questions`.
- **Don't invent business rules, owners, load schedules, systems or uses.** "Updated
  daily", "owned by Finance" and "used for the monthly report" are invented unless
  someone told you so.
- **Match your wording to your confidence.**
  - `high`: the names and values agree and leave no real doubt. State it plainly.
  - `medium`: the evidence points one way, but another reading is possible. Use
    "appears to" or "likely" once, not in every sentence.
  - `low`: the purpose is unclear. Say so ("The purpose of this table is unclear from
    the data alone") and add `open_questions`.
- **"Unclear" is an acceptable answer.** An honest low-confidence description with good
  open questions is better than a fluent guess.

## 4. Don't state the obvious

Don't write any of these (`bijoe check` catches most of them):
- "The `customers` table contains information about customers." This adds nothing.
- "This table stores data related to various orders." The words *data related to* and
  *various* are vague.
- Listing every column. The reader can see the columns.
- Repeating the row count with no meaning attached. Give it meaning instead: "48k
  orders over 3 years, so about 45 a day".
- Filler like *comprehensive*, *valuable insights*, *plays a key role* or *robust*.

**Test:** cover the table name. Would a reader still learn something from your first
sentence? If not, rewrite it.

## 5. Examples

Weak:
```json
"orders": {"description": "This table contains information about orders placed by customers.", "source": "inferred", "confidence": "high", "evidence": []}
```

Good:
```json
"orders": {
  "description": "One row per order, identified by `order_id`, with each order linked to a customer through `cust_id`. Orders run from 2023-01-02 to 2024-06-30, and most are `shipped` (71%) or `open`. `amount` is stored as text, and 3 of 4,120 values are not numbers.",
  "source": "inferred",
  "confidence": "medium",
  "evidence": [
    "`order_id` unique, 0% missing, 4,120 rows",
    "`cust_id` integer 1-950; `customers.cust_id` unique integer 1-950",
    "`order_date` min 2023-01-02, max 2024-06-30",
    "`status` top values: shipped (2,925), open (1,010), cancelled (185)",
    "`amount` inferred text: 4,117 numeric values, 3 non-numeric"
  ],
  "open_questions": ["Is `amount` before or after VAT?"]
}
```

Low confidence, done right:
```json
"tbl_x7": {
  "description": "The purpose of this table is unclear from the data alone. Each row pairs a `ref` code with a `val` decimal between 0 and 1, and `ref` values repeat (212 distinct in 9,400 rows).",
  "source": "inferred",
  "confidence": "low",
  "evidence": ["columns `ref` (text, 212 distinct) and `val` (decimal 0.0-1.0)", "9,400 rows, no unique column"],
  "open_questions": ["What does `ref` refer to?", "What does `val` measure, and is it a rate or a probability?"]
}
```

## 6. Dataset summary

Write `dataset.summary` last, in two to four sentences:
- what the data is about as a whole
- which tables are central and how they connect
- the time span, if it is known
- the one thing a reader should know first

The same rules apply. Set `dataset.source` to `inferred`, unless the user gave you the
summary.
