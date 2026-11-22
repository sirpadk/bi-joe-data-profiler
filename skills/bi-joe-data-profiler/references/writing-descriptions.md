# Writing Descriptions

Descriptions are the part of the wiki that people and other AI agents read first and act
on. This guide has one rule above all the others: **never state the obvious.** Everything
else here serves it. A confident wrong description does more harm than an honest
"More context needed.", and a description that only repeats the name does no good at all.

## 1. Never State the Obvious

A description must tell the reader something they could not get from the name alone.

**Circular descriptions** repeat the name in other words:

| Name | Obvious (circular) | Better |
|---|---|---|
| `CustomerName` | Name of the customer | The full name of the person who is making the order or the purchase |
| `Shipments` | Information about shipments | A package that has left a warehouse for a customer, from dispatch until it is delivered |
| `Employees` | A list of employees | The people who work for the company and are paid by it, whether permanent or temporary |

Nothing is wrong with the circular version, but nothing is great about it either. The
better version says **what the thing is**, relates it to the business (who does what to
whom), and where the evidence allows it, says what sets it apart from look-alikes.

### The ladder

1. **Repeats the name.** "Customer information." *(useless)*
2. **Translates the name.** "A customer." *(still circular: what is a customer?)*
3. **Explains the thing.** "A person who has made one or more purchases from the company."
4. **Explains it in its context.** "A person who has bought from the company in a store
   or online, as opposed to a business account or a prospect who has not bought yet."

Aim for level 3 or 4, and only claim what the evidence supports.

### Three checks before you keep a description

1. **Cover the name.** Would a reader still learn something from your sentence? If it only
   works because of the name next to it, rewrite it.
2. **Ask "what is a ___?"** A description of a customers table has to answer what a
   customer is. If the reader would still ask, you stated the obvious.
3. **Could you have written it without looking at the data?** If so, you probably repeated
   the name. Real descriptions use the names, values and context you found.

### Write in Everyday Language

Write the way you would explain the data to a colleague over coffee: plain, natural,
day-to-day words. Avoid idioms, trade slang and colourful phrases, even when they sound
specific. "Rung up at the till" is the typical example of what not to write: nobody says
it, it needs decoding, and it quietly claims there is a cash register in the data.

- Prefer the words people in the business use: "the same bill", "purchase", "customer".
- If you wouldn't say it out loud in a meeting, don't write it.
- Specific is good only when the evidence makes it specific. Sounding specific is not the goal.

### Examples Are Illustrations, Not Templates

Every example in this guide shows the *kind* of description to write. Never copy its
wording, its phrases or its details into a description. Reason from the data in front of
you, and **drop every detail that no column, value or document backs** (a till, a
warehouse, a loyalty programme, an online channel). A shorter description that is fully
backed is better than a vivid one that is partly guessed.

### The data decides, not the name

The same table name can deserve a different description. A `Customers` table full of
people (first and last names, birth dates, personal emails) describes a person. If it held
company names and tax numbers and no birth dates, it would describe a business that buys
from the company. Let the evidence decide.

### Make good guesses, not wild ones

- **A good guess** is the reading that most of the evidence points to, and that a domain
  expert would agree with on sight. State it plainly.
- **A wild guess** depends on facts the data doesn't show: who uses the table, why it
  exists, which system it comes from, what a code means. Leave those out.
- **When the evidence doesn't support a sensible description or grain,** write exactly
  `More context needed.` and add an open question saying what would settle it.

`bijoe check` catches the most common ways of stating the obvious: a description or grain
that only repeats the table name, and filler such as "contains information about". It can't
judge everything, so you still have to apply the three checks above.

## 2. The Description

The description is the **first row of the data story** and also the **Description column
on the landing page**, so it has to work in both places.

- **A few short sentences, under about 400 characters.** It may be longer than one line as
  long as every sentence adds something. It also sits on the landing page.
- **Plain business language.** A column name may appear in plain text when it makes the
  description clearer ("the status and the reserved quantity"), but never in backticks or
  other code styling. `bijoe check` warns about backticks. Detailed technical notes belong in
  `ai_notes`.
- **Built from evidence.** Combine the table's name, the column names, the values and the
  context into the most likely meaning. For example, first and last names, birth dates and
  a minimum of one order per customer together say: a person who has made one or more
  purchases.
- **No invented facts.** Owners, source systems, load schedules, uses and business rules
  are invented unless the data or the user said so.

The evidence behind it goes in the `evidence` list. That list isn't shown in the page body,
but it is kept in the page's Metadata section for AI agents and is required for inferred
descriptions.

### What a Good Description Covers

Read the whole table, then say the things a colleague would want to know first. Pick the
ones the evidence supports; skip the rest.

- **What kind of table it is**, in plain words: a log of events, a list of things that exist
  (customers, products), a status that is measured regularly, a hierarchy, a link between two
  things. Lead with that when it is the most useful fact.
- **How the data changes over time**: does a row stay as it is, get replaced, or get added
  each day or period? Dates such as valid-from and valid-to, or a snapshot date, show this.
  Say what you see and no more (for example, that dates run from one year to another).
- **The word the business uses.** When the data uses an unusual term for a common thing (an
  "account" that is really a customer, a "node" that is a category), say both: the term
  and what it means in plain words, if the evidence shows it.
- **Hedge a guess once, honestly.** A qualified guess ("appears to be the count at the end of
  each day") is better than a flat claim or an empty "More context needed." when the evidence
  leans one way. Put what would settle it in the open questions.
- **Vary the way you start.** Do not open every description with the same words
  ("Holds data about…"). Start with whatever is most distinctive about this table.

## 3. The Grain

The grain says what one row is. It's built on the description, so it answers the "what is
a ___?" question, not only the table name:

| Description | Grain |
|---|---|
| A person who has made one or more purchases from the company. | One row for each person who is a customer |
| A purchase made by a customer at a store, with what was bought, how many, the price, when it happened and how much was paid. | One row for each product bought at a store under the same sales transaction, that is the same bill |

- Start with "One row for each …" (or "One row per …").
- **Name what pins a row down.** Say which things together make a row unique, such as the
  date, the product and the warehouse, or the node and the period it is valid for. Say what
  is notable in the data: zero stock is still a row, a value that repeats over time, not every
  product held at every place.
- A grain that only repeats the table name ("One row per customer") states the obvious.
- Base it on what is measured. See "Keys and Grain" below.

### Keys and Grain: Let the Measurements Decide

`bijoe evidence` prints **What Identifies a Row** for each table: columns that are unique on
their own, combinations that are unique together, the closest combinations that are not
quite unique, and how identifier-like columns map onto each other. Use these, not the
column names, to decide what a row is.

- **The measured key beats the obvious key.** A table may carry an account number and a
  national tax number. If the tax number is unique and the account number is too, but they do
  not map one-to-one, ask which one is the real identity of a row. Name the one the data
  supports in the grain.
- **Same thing, two identifiers.** When two columns identify the same kind of thing (a
  customer number and a tax number, a person ID and a social security number), expect a
  one-to-one mapping. If one value maps to several, the grain is finer than it looks or
  there are duplicates. Say which is more likely in an open question; never smooth it over.
- **Look for relationships that make sense, not every relationship that exists.** Zip code
  to city, an identifier to its own description, one identity named twice: these matter.
  Two unrelated columns that happen to move together do not.
- **A key that is almost unique is a finding.** If an employee and project together are
  unique except for 113 repeats, and adding the start date makes them unique, say that the
  same person returns to the same project and the dates separate the rows.
- **Measurements are sampled.** On large tables the numbers come from the first rows (the
  evidence says so). Describe what is measured as measured, and say when it is a sample.
- **Keys may have data issues.** Do not assume a key is clean because it is named like one.

## 4. Pick the Source, in This Order

| Priority | When | `source` | What you do |
|---|---|---|---|
| 1 | The source system stores a table description (the profiler fills it in) | `system_metadata` | Keep it **exactly as it is**. Never reword or "improve" it. You may add grounded context in `ai_notes`. |
| 2 | The user gave you documentation, a data dictionary or an explanation | `user_documentation` | Use their wording or a faithful condensed version. List what you used in `evidence`, e.g. "Data dictionary v3 (sales.xlsx, sheet Docs)". |
| 3 | Neither of the above | `inferred` | Write it from the evidence, following this guide. `confidence` and `evidence` are required. |

Column comments from the source system (shown in the `comment` column of `bijoe evidence`)
count as strong evidence for an inferred description. Cite them.

## 5. The Other Fields

- **`confidence`** (inferred only): `high` when names and values agree and leave no real
  doubt; `medium` when one reading is likely but another is possible (use "appears to" at
  most once); `low` when the purpose is unclear. Say so plainly, and add open questions.
- **`evidence`**: the facts you relied on, with exact names and numbers, e.g. "`order_id`
  unique and never missing across 48,213 rows". Write for an AI agent: precision beats style.
- **`open_questions`**: questions only the data owner can answer. Each should be specific
  and answerable, and name the column when it is about one. Duplicates in a key, impossible
  values and unclear codes belong here.
- **`ai_notes`**: context and data-quality observations that are too technical for the
  description. Column names and numbers are welcome here. It is shown lower on the page,
  just above the open questions.

## 6. Hard Rules

- **Every claim has evidence.** If you can't point to a column, value, count or document,
  leave the claim out.
- **Don't expand names you can't confirm.** Don't spell out abbreviations, translate codes
  or name source systems unless the data shows it. `KDNR` might be a customer number; if the
  values don't confirm it, say so in an open question.
- **Match your wording to your confidence.** Don't sound certain when you aren't.
- **"Unclear" is an acceptable answer.** An honest low-confidence description with good open
  questions is better than a fluent guess.
- **Fit the depth to the user's `purpose`, `audience` and `focus`** (shown at the top of
  `bijoe evidence`). Someone building a dashboard needs the grain and the time range;
  someone sourcing data into a warehouse needs the keys and the caveats.

## 7. Don't Pad

Don't write any of these (`bijoe check` catches most of them):
- "The customers table contains information about customers."
- "This table stores data related to various orders." The words *data related to* and
  *various* are vague.
- Listing every column. The reader can see the columns.
- Filler like *comprehensive*, *valuable insights*, *plays a key role* or *robust*.

## 8. Dataset Summary (the "About" Row on the Landing Page)

Write `dataset.summary` last, in one to three plain sentences that tell the reader **what
the data is about as a whole**: the business, the area it covers, and the time span if it
is known.

**Don't** name tables or columns, or explain how tables connect. The data stories and the
diagrams do that. The summary has to read just as well for a database of 100 tables as for
3. `bijoe check` warns when the summary names a table or uses `backticks`. The same rules
apply: no obvious statements, no invention. Set `dataset.source` to `inferred`, unless the
user gave you the summary.

## 9. Example

```json
"orders": {
  "description": "A purchase placed by a customer, from the moment it is ordered until it is paid, with the date and the channel it came through.",
  "grain": "One row for each purchase a customer makes",
  "source": "inferred",
  "confidence": "medium",
  "evidence": [
    "`order_id` unique, 0% missing, 4,120 rows",
    "`cust_id` integer 1-950; `customers.cust_id` unique integer 1-950, measured relationship 100%",
    "`order_date` min 2023-01-02, max 2024-06-30",
    "`channel` values: web (2,925), store (1,010), phone (185)"
  ],
  "ai_notes": "`amount` is stored as text and 3 of 4,120 values are not numbers.",
  "open_questions": ["Is `amount` before or after VAT?"]
}
```

Low confidence, done right:

```json
"tbl_x7": {
  "description": "More context needed.",
  "grain": "More context needed.",
  "source": "inferred",
  "confidence": "low",
  "evidence": ["columns `ref` (text, 212 distinct) and `val` (decimal 0.0-1.0)", "9,400 rows, no unique column"],
  "open_questions": ["What does `ref` refer to?", "What does `val` measure, and is it a rate or a probability?"]
}
```
