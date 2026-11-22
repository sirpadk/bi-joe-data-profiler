"""Renders profile.json + descriptions.json into a linked Markdown wiki.

Layout:
    <out>/index.md                    landing page: at a glance, data stories, data model
    <out>/data-stories/<slug>.md      one data story per table
    <out>/beam-annotations.md         static BEAM reference page (copied from assets/)
    <out>/how-to-read.md              static reading guide (copied from assets/)
    <out>/_bijoe/profile.json         measured facts (machine-readable)
    <out>/_bijoe/descriptions.json    written descriptions + provenance

Layout rules:
- Paired information (label + value) is shown as a simple HTML table with inline CSS,
  not a Markdown table, so there is no empty header row. Markdown is not processed
  inside HTML, so links inside those tables are written as HTML links.
- Every page ends with a "Metadata" section holding a fenced ```yaml block, so other AI
  agents and tools can read the wiki without parsing prose, while people see the content
  first.
- All headings, titles, table labels and column headers use Title Case.
"""

from __future__ import annotations

import html as _html
import json
import re
import shutil
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from . import SCHEMA_VERSION, beam, distribution, themes

STORIES_DIR = "data-stories"
HOW_TO_READ = "how-to-read.md"
#: the Relationships diagram of a data story shows at most this many columns, unless more
#: are needed to show every relationship and key column
MAX_DIAGRAM_COLUMNS = 20


def slugify(name: str, taken: Set[str]) -> str:
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-") or "table"
    base, n = slug, 2
    while slug in taken:
        slug = f"{base}-{n}"
        n += 1
    taken.add(slug)
    return slug


def profile_path(out_dir: Path) -> Path:
    return out_dir / "_bijoe" / "profile.json"


def load_profile(out_dir: Path) -> Dict[str, Any]:
    p = profile_path(out_dir)
    if not p.is_file():
        raise FileNotFoundError(f"No profile found at {p}. Run `bijoe profile` first.")
    return json.loads(p.read_text(encoding="utf-8"))


def save_profile(out_dir: Path, profile: Dict[str, Any]) -> None:
    p = profile_path(out_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(profile, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


# ---- text helpers -----------------------------------------------------------

_SMALL_WORDS = {"a", "an", "the", "and", "but", "or", "nor", "for", "so", "yet", "at", "by", "in", "of", "on",
                "to", "up", "as", "per", "via", "vs", "with", "from", "into", "off", "out", "over"}


def _title_token(tok: str, first: bool, last: bool) -> str:
    if "-" in tok.strip("-") and not tok.startswith("-"):
        parts = tok.split("-")
        return "-".join(_title_token(p, first and k == 0, last and k == len(parts) - 1) for k, p in enumerate(parts))
    m = re.match(r"^(\W*)(.*?)(\W*)$", tok, re.UNICODE)
    lead, body, trail = m.groups() if m else ("", tok, "")
    if not body:
        return tok
    if any(c.isupper() for c in body[1:]) or any(c.isdigit() for c in body):
        return tok  # BEAM, ADWD, BI, 7Ws: already deliberate
    if body.lower() in _SMALL_WORDS and not first and not last:
        return lead + body.lower() + trail
    return lead + body[0].upper() + body[1:] + trail


def title_case(text: str) -> str:
    """Title Case: capitalise every word except small ones (a, the, of...) that are not first or last,
    and the first word after a colon. Words that already contain capitals or digits are left alone."""
    tokens = text.split(" ")
    out, after_colon = [], False
    for i, tok in enumerate(tokens):
        out.append(_title_token(tok, i == 0 or after_colon, i == len(tokens) - 1))
        after_colon = tok.endswith(":")
    return " ".join(out)


def _display_name(name: str) -> str:
    """Dataset name as shown in titles (file-style names like shoe_company read as words)."""
    return title_case(name.replace("_", " "))


def esc(text: Any) -> str:
    return _html.escape(str(text), quote=True)


def inline_html(text: str, prefix: str = "") -> str:
    """Plain text from descriptions.json -> HTML for an HTML table cell."""
    out = _html.escape(text, quote=False)
    out = re.sub(r"`([^`\n]+)`", r'<code style="background:rgba(128,128,128,.25);color:inherit;padding:1px 5px;border-radius:4px;">\1</code>', out)
    return beam.link_prose_html(out, prefix)


def _yaml_value(v: Any) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return json.dumps(str(v), ensure_ascii=False)  # JSON strings are valid YAML


METADATA_HEADING = "## Metadata"


def metadata_block(fields: Dict[str, Any]) -> List[str]:
    """Closing section of every page: a fenced YAML block with the page's facts."""
    lines = ["", "---", "", METADATA_HEADING, "",
             "_Machine-readable facts about this page, for tools and AI agents._", "", "```yaml"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:" + ("" if value else " []"))
            lines.extend(f"  - {_yaml_value(v)}" for v in value)
        else:
            lines.append(f"{key}: {_yaml_value(value)}")
    lines.append("```")
    return lines


def _cell(text: Any) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _entry(descriptions: Dict[str, Any], table: str) -> Dict[str, Any]:
    entry = (descriptions.get("tables") or {}).get(table) or {}
    if not (entry.get("description") or "").strip():
        entry = {**entry, "source": "pending"}
    return entry


# ---- HTML tables ------------------------------------------------------------

_theme_key = themes.DEFAULT_THEME


def set_theme(name: Optional[str]) -> str:
    """Choose the colour theme used by every table written from now on (see themes.py)."""
    global _theme_key
    _theme_key = themes.resolve(name)
    return _theme_key


def current_theme() -> str:
    return _theme_key


def _prop_styles() -> Tuple[str, str, str]:
    t = themes.THEMES[_theme_key]
    line = f"border-bottom:1px solid {t['line']};"
    table = "border-collapse:collapse;margin:8px 0;"
    label = (f"text-align:left;vertical-align:top;white-space:nowrap;font-weight:600;padding:6px 16px 6px 10px;"
             f"background:{t['label']};color:{t['label_fg']};{line}")
    value = f"text-align:left;vertical-align:top;padding:6px 10px;background:{t['cell']};color:{t['fg']};{line}"
    return table, label, value


def property_table(rows: List[Tuple[str, str]]) -> List[str]:
    """Paired information (label + value) as a simple HTML table. Labels are plain text and are put
    in Title Case; values must already be HTML. Rows with an empty value are left out."""
    tbl, lab, val = _prop_styles()
    out = [f'<table style="{tbl}">']
    for label, value in rows:
        if value in (None, ""):
            continue
        out.append(f'<tr><th scope="row" align="left" style="{lab}">{esc(title_case(label))}</th>'
                   f'<td style="{val}">{value}</td></tr>')
    out.append("</table>")
    return out


def _property_table_html(rows: List[Tuple[str, str]]) -> List[str]:
    """Like property_table, but the label is already HTML (used for 'Why [CV]')."""
    tbl, lab, val = _prop_styles()
    out = [f'<table style="{tbl}">']
    for label_html, value in rows:
        if value in (None, ""):
            continue
        out.append(f'<tr><th scope="row" align="left" style="{lab}">{label_html}</th>'
                   f'<td style="{val}">{value}</td></tr>')
    out.append("</table>")
    return out


# ---- the columns matrix -----------------------------------------------------

# ---- hover text for the matrix labels (what it means, why it matters) -------------------

MEASURE_HELP = {
    "Column Name": "The column as it is named in the data. Each column of the table is one column in this matrix.",
    "Data Type": "The kind of values found in the data, which may differ from what the source declares. The short code is a BEAM annotation, for example C9 is text with a longest value of 9 characters.",
    "BEAM✲": "Short BEAM annotations. Plain codes are measured from the data. Codes in italics are suggested by AI and should be checked. Click a code to read what it means.",
    "Sample Count": "How many rows were read for these numbers. Every percentage in this group is based on it, so check it first: on very large tables it can be fewer than all rows.",
    "Missing": "Rows where the column is empty or blank, with the share of rows. It matters because gaps break joins and totals, and a column that should always be filled in should show 0.",
    "Unique Values": "How many different values occur, with the share of rows. 100% means every value is different, so the column could identify a row. A low share means the column holds categories or codes.",
    "Min Value": "The smallest value: the lowest number, the earliest date, or the first in alphabetical order. It matters because it shows the start of the range and catches impossible values such as a negative quantity.",
    "Min Count": "How many rows have the smallest value. On a unique column it is 1. A high count suggests a default or a stand-in value, such as 0 or 1900-01-01, rather than a real minimum.",
    "Max Value": "The largest value: the highest number, the latest date, or the last in alphabetical order. It matters because it shows the end of the range and catches outliers or future dates.",
    "Max Count": "How many rows have the largest value. A high count suggests a cap or a stand-in value, such as 9999-12-31, rather than a real maximum.",
    "Min Length": "The shortest text, counted in characters. If it differs a lot from the longest, the column may mix formats, or have values that were cut off.",
    "Max Length": "The longest text, counted in characters. It matters when you load the data elsewhere, because the target column must be wide enough.",
    "Typical": "The most common value, so you can see what a normal row looks like. In a column where every value is different, this is just the first of them.",
    "Different": "A rare value, one of the least common. Odd values are often special cases or mistakes, so they are worth a look.",
    "Repeat": "A value that occurs more than once, and how many times (x3 means three rows). 'No repeats' means every value is different.",
    "Variation Missing": "What stands in for 'no value': empty cells and stand-in words such as N/A or unknown, with how many of each. Stand-ins are easy to mistake for real values.",
    "Range": "From the smallest to the largest value in one line, to show the spread at a glance.",
    "Change": "How values change over time cannot be seen in a single snapshot. Profile the same data again later and compare to see it.",
    "Histogram": "How the rows are spread over ranges of values (bins). Each bar is one bin and its height is the number of rows. Hover a bar for its range and count. Orange bars are outliers, dashed boxes are gaps with no rows. Categories show the most frequent values. Keys, names and other personal data are not charted.",
    "Shape": "The overall form of the histogram: symmetric, right-skewed, left-skewed, uniform, bimodal or one dominant value. It matters because a skewed column has an average that misleads, and two peaks often mean two groups mixed together.",
    "Median": "The middle value: half of the rows are below it and half above. Compare it with the average. A big difference means the data is skewed or has outliers.",
    "Spread": "The range holding the middle half of the rows (first to third quartile). A narrow spread means similar values, a wide one means high variability.",
    "Outliers": "Values far outside the usual range (more than 1.5 times the middle spread beyond the quartiles). They may be mistakes or real extremes, so they are worth checking. The count is shown with the limit it passed.",
    "Gaps": "Ranges between filled bins where no rows exist at all. In dates they show periods with no activity or missing data, which a total or an average would hide.",
}
GROUP_HELP = {
    "Data Profiling Results": "Counts and extremes measured from the rows that were read. They are facts, not opinions.",
    "Variation": "Examples taken from the measured values, to show how varied the column is and what odd values look like.",
    "Distribution": "How the values are spread: a small histogram, its shape, the middle value, the spread, and any outliers and gaps. Counted from the rows that were read.",
    "Sample Data": "Five random rows from the table, shown side by side so you can see real values together.",
}


MASKED_HELP = ("Personal data. The engine measured this column but never saved or shows its values, so "
               "neither the AI agent nor the reader sees them.")
MASKED_HTML = f'<i title="{_html.escape(MASKED_HELP, quote=True)}">masked</i>'


def _tip(text: str) -> str:
    return f' title="{_html.escape(text, quote=True)}"' if text else ""



# ---- distribution cells (mini histograms) ---------------------------------------------------

def _bars(dist: Dict[str, Any], S: Dict[str, Any]) -> str:
    """A tiny histogram as an HTML table of coloured bars. Every bar has its own hover text."""
    kind = dist.get("kind")
    if kind == "none":
        share = dist.get("top_share_pct")
        extra = f"<br>most common value: {share}% of rows" if share is not None else ""
        return (f'<i title="{_html.escape(MASKED_HELP, quote=True)}">not charted: personal data</i>'
                f'<span style="font-size:80%;opacity:.75">{extra}</span>')
    bins = dist.get("bins") or []
    if not bins:
        return "—"
    top = max(b["count"] for b in bins) or 1
    width = 9 if len(bins) <= 12 else 7 if len(bins) <= 20 else 5 if len(bins) <= 30 else 4
    cells = []
    for b in bins:
        tip = f'{b["label"]}: {b["count"]:,} rows ({b["pct"]:g}%)'
        if b.get("outlier"):
            tip += " (outliers: far outside the usual range)"
        if b.get("gap"):
            tip += " (gap: no rows in this range)"
        if b.get("other_group"):
            tip += " (rare values grouped to protect small groups)"
        if b.get("gap"):
            box = f"width:{width}px;height:8px;box-sizing:border-box;border:1px dashed {S['bar_gap']};"
        else:
            height = max(2, round(34 * b["count"] / top)) if b["count"] else 1
            colour = S["bar_warn"] if (b.get("outlier") or b.get("other_group")) else S["bar"]
            box = f"width:{width}px;height:{height}px;background:{colour};"
            if not b["count"]:
                box = f"width:{width}px;height:1px;background:{S['bar_gap']};"
        cells.append(f'<td title="{_html.escape(tip, quote=True)}" style="padding:0 1px;border:0;background:transparent;'
                     f'vertical-align:bottom;"><div style="{box}"></div></td>')
    if kind == "categories":
        lead = bins[0]
        caption = f'{lead["label"]} {lead["pct"]:g}%'
    elif kind == "time":
        caption = f'{bins[0]["label"]} → {bins[-1]["label"]}'
    else:
        main = [b for b in bins if not b.get("outlier")] or bins
        caption = f'{main[0]["label"].split("–")[0]} → {main[-1]["label"].split("–")[-1]}'
    if dist.get("sampled"):
        caption += " (sample)"
    return ('<table style="border-collapse:collapse;border:0;margin:0;background:transparent;"><tr style="vertical-align:bottom">'
            + "".join(cells) + "</tr></table>"
            f'<div style="font-size:75%;opacity:.75;white-space:nowrap;">{esc(caption)}</div>')


def _shape_cell(dist: Optional[Dict[str, Any]]) -> str:
    shape = (dist or {}).get("shape")
    if not shape:
        return "—"
    return f'<span title="{_html.escape(distribution.SHAPES.get(shape, ""), quote=True)}">{esc(shape.capitalize())}</span>'


def _number(x: Optional[float], step: float = 1.0) -> str:
    return "—" if x is None else distribution._fmt(x, step)


def distribution_rows(cols: List[Dict[str, Any]], S: Dict[str, Any]) -> List[Tuple[str, List[str], str]]:
    def dist(c: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return c.get("distribution")

    def step(c: Dict[str, Any]) -> float:
        d = dist(c) or {}
        return d.get("bin_width") or 0.01 if d.get("kind") == "numeric" else 1.0

    def has_numbers(c: Dict[str, Any]) -> bool:
        return (dist(c) or {}).get("kind") in ("numeric", "discrete")

    def outliers(c: Dict[str, Any]) -> str:
        if not has_numbers(c):
            return "—"
        o = dist(c).get("outliers")
        if not o:
            return "none"
        parts = []
        if o["below"]:
            parts.append(f'{o["below"]:,} below {_number(o["low_fence"], step(c))}')
        if o["above"]:
            parts.append(f'{o["above"]:,} above {_number(o["high_fence"], step(c))}')
        return esc(", ".join(parts))

    def gaps(c: Dict[str, Any]) -> str:
        d = dist(c) or {}
        if d.get("kind") not in ("numeric", "discrete", "time"):
            return "—"
        runs = d.get("gap_runs") or 0
        if not runs:
            return "none"
        unit = d.get("unit") or "bin"
        return f'{runs} gap{"s" if runs != 1 else ""} ({d["gap_bins"]} empty {unit}{"s" if d["gap_bins"] != 1 else ""})'

    return [
        ("Histogram", [_bars(dist(c), S) if dist(c) else "—" for c in cols], "cell"),
        ("Shape", [_shape_cell(dist(c)) for c in cols], "cell"),
        ("Median", [_number(dist(c).get("median"), step(c)) if has_numbers(c) else "—" for c in cols], "cell"),
        ("Spread", [f'{_number(dist(c)["q1"], step(c))} – {_number(dist(c)["q3"], step(c))}' if has_numbers(c) else "—"
                    for c in cols], "cell"),
        ("Outliers", [outliers(c) for c in cols], "cell"),
        ("Gaps", [gaps(c) for c in cols], "cell"),
    ]


_COL1_W = 34  # px: the narrow first column holding the rotated group names


def _matrix_styles() -> Dict[str, Any]:
    t = themes.THEMES[_theme_key]
    line = t["line"]
    border = f"border:0 solid {line};border-width:0 1px 1px 0;"
    colors = f"background:{t['cell']};color:{t['fg']};"
    label = f"background:{t['label']};color:{t['label_fg']};"
    cell = border + "padding:3px 8px;white-space:nowrap;text-align:left;vertical-align:top;" + colors
    z = "z-index:2;"
    col1 = ["position:sticky;left:0;" + z + "box-sizing:border-box;" + f"width:{_COL1_W}px;min-width:{_COL1_W}px;max-width:{_COL1_W}px;"
            + border + f"background:{bg};color:{fg};padding:4px 0;text-align:center;vertical-align:middle;"
            + (f"border-left:3px solid {edge};" if edge else f"border-left:1px solid {line};")
            for bg, fg, _tint, edge in t["groups"]]
    return {
        "line": line,
        "cell": cell,
        "head": cell + f"font-weight:600;background:{t['head']};color:{t['head_fg']};",
        "num": cell.replace("text-align:left", "text-align:right"),
        "tint": [tint for _bg, _fg, tint, _edge in t["groups"]],
        "col1": col1,
        "col2": f"position:sticky;left:{_COL1_W}px;" + z + border + label + "padding:3px 8px;white-space:nowrap;text-align:left;"
                "vertical-align:top;font-weight:600;",
        "corner": "position:sticky;left:0;" + z + f"box-sizing:border-box;width:{_COL1_W}px;min-width:{_COL1_W}px;"
                  f"max-width:{_COL1_W}px;padding:0;border:0;background:transparent;",
        "top": f"border-top:1px solid {line};",
        "left": f"border-left:1px solid {line};",
        "col12": "position:sticky;left:0;" + z + border + label + "padding:3px 8px;white-space:nowrap;text-align:left;"
                 "vertical-align:top;font-weight:600;",
        "head12": "position:sticky;left:0;" + z + border + f"background:{t['head']};color:{t['head_fg']};"
                  "padding:3px 8px;white-space:nowrap;text-align:left;vertical-align:top;font-weight:700;",
        "help": "cursor:help;",
        "bar": t["bar"], "bar_warn": t["bar_warn"], "bar_gap": t["bar_gap"], "muted": t["label_fg"],
        "rotated": "writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;margin:0 auto;font-weight:600;",
    }


_PLAIN_TYPES = {"text": "text", "integer": "whole number", "decimal": "number", "date": "date",
                "datetime": "date/time", "boolean": "yes/no", "time": "time", "binary": "binary", "empty": "empty"}


def _value(v: Any, width: int = 25, blank: str = "—") -> str:
    if v is None or v == "":
        return blank
    text = str(v)
    return text if len(text) <= width else text[: width - 1] + "…"


def _count_pct(count: int, n: int) -> str:
    if not n:
        return f"{count:,}"
    return f"{count:,} ({100 * count / n:.3g}%)"


def _example(label: str, col: Dict[str, Any], show_values: bool) -> str:
    """The Variation rows, filled from what was measured (plain text)."""
    tops = col.get("top_values") or []
    if label == "Change":
        return "—"
    if col.get("pii") and label != "Missing":
        return "masked"
    if label == "Missing":
        parts = []
        if col.get("missing_count"):
            parts.append(f"empty ×{col['missing_count']:,}")
        parts += [f"{_value(p['value'])} ×{p['count']:,}" for p in col.get("placeholder_values", [])]
        return ", ".join(parts) or "—"
    if label == "Range":
        lo, hi = col.get("min_value"), col.get("max_value")
        return f"{_value(lo)} → {_value(hi)}" if lo is not None and hi is not None and lo != hi else "—"
    if not show_values:
        return ""  # shown as "hidden"
    if label == "Typical":
        return _value(tops[0]["value"]) if tops else "—"
    if label == "Different":
        rare = col.get("rare_value")
        if rare and (not tops or rare["value"] != tops[0]["value"]):
            return _value(rare["value"])
        return _value(tops[1]["value"]) if len(tops) > 1 else "—"
    if label == "Repeat":
        repeated = [t for t in tops if t["count"] > 1]
        if not repeated:
            return "no repeats"
        pick = next((t for t in repeated if tops and t["value"] != tops[0]["value"]), repeated[0])
        return f"{_value(pick['value'])} ×{pick['count']:,}"
    return "—"


def _column_suggestion(spec: Any, col: Dict[str, Any]) -> Dict[str, Any]:
    spec = spec if isinstance(spec, dict) else {"codes": list(spec or [])}
    codes = []
    for c in spec.get("codes") or []:
        if c == "MD" and col.get("missing_count"):
            c = "~~MD~~"  # should always be filled in, but the data has gaps
        codes.append(c)
    return {"codes": codes, "why": spec.get("why") or ""}


def columns_matrix(table: Dict[str, Any], entry: Dict[str, Any], profile: Dict[str, Any], pre: str,
                   show_values: bool) -> List[str]:
    """One matrix column per real column (Modelstormer layout), as an HTML table with the two
    label columns frozen on sideways scroll. Rows are grouped: Data Profiling Results, Variation, Sample Data."""
    cols = table["columns"]
    n = table.get("profiled_rows") or 0
    names = [t["name"] for t in profile["tables"]]
    rels = profile.get("relationships") or []
    suggestions = (entry.get("beam") or {}).get("columns") or {}
    S = _matrix_styles()

    def td(content: str, style: Optional[str] = None) -> str:
        return f'<td style="{style or S["cell"]}">{content}</td>'

    def type_cell(c: Dict[str, Any]) -> str:
        code = beam.data_type_code(c)
        plain = esc(_PLAIN_TYPES.get(c["inferred_type"], c["inferred_type"]))
        tag = (f' <span title="{_html.escape(MASKED_HELP, quote=True)}" style="white-space:nowrap">'
               f'🔒 {esc(c["pii"]["class"])}</span>') if c.get("pii") else ""
        return (beam.links_html([code], "column", pre) + " " if code else "") + plain + tag

    def beam_cell(c: Dict[str, Any]) -> str:
        measured = beam.links_html(beam.measured_column_codes(table, c, rels), "column", pre, names)
        sug = _column_suggestion(suggestions.get(c["name"]), c)
        suggested = beam.links_html(sug["codes"], "column", pre, names, italic=True)
        return " ".join(x for x in (measured, suggested) if x)

    def group(gi: int, label: str, rows: List[Tuple[str, List[str], str]]) -> List[str]:
        out = []
        for i, (row_label, cells, style) in enumerate(rows):
            tr = "<tr>"
            if i == 0:
                tr += (f'<td rowspan="{len(rows)}" style="{S["col1"][gi]}{S["help"]}"{_tip(GROUP_HELP.get(label, ""))}><div style="{S["rotated"]}">'
                       f'{esc(title_case(label))}</div></td>')
            key = ("Variation " + row_label) if (label == "Variation" and row_label == "Missing") else row_label
            tr += f'<td style="{S["col2"]}{S["help"]}"{_tip(MEASURE_HELP.get(key, ""))}>{esc(title_case(row_label))}</td>'
            tint = f"background:{S['tint'][gi]};"
            tr += "".join(td(c, S["num" if style == "num" else "cell"] + tint) for c in cells) + "</tr>"
            out.append(tr)
        return out

    hidden = "<i>hidden</i>"
    profiling = [
        ("Sample Count", [f"{n:,}" for _ in cols], "num"),
        ("Missing", [_count_pct(c.get("missing_count", 0), n) for c in cols], "cell"),
        ("Unique Values", [_count_pct(c.get("distinct_count", 0), n) for c in cols], "cell"),
        ("Min Value", [MASKED_HTML if c.get("pii") and "min_value" not in c else esc(_value(c.get("min_value"))) for c in cols], "cell"),
        ("Min Count", [_count_pct(c["min_count"], n) if "min_count" in c else "—" for c in cols], "cell"),
        ("Max Value", [MASKED_HTML if c.get("pii") and "max_value" not in c else esc(_value(c.get("max_value"))) for c in cols], "cell"),
        ("Max Count", [_count_pct(c["max_count"], n) if "max_count" in c else "—" for c in cols], "cell"),
        ("Min Length", [str(c["min_length"]) if "min_length" in c else "—" for c in cols], "num"),
        ("Max Length", [str(c["max_length"]) if "max_length" in c else "—" for c in cols], "num"),
    ]
    variation = []
    for label in ("Typical", "Different", "Repeat", "Missing", "Range", "Change"):
        cells = []
        for c in cols:
            text = _example(label, c, show_values)
            cells.append(MASKED_HTML if text == "masked" else esc(text) if text else hidden)
        variation.append((label, cells, "cell"))

    out = ['<div style="overflow-x:auto;max-width:100%;">',
           f'<table style="border-collapse:separate;border-spacing:0;font-size:90%;">']
    label_style = S["col2"] + S["left"]
    out.append(f'<tr><td rowspan="3" style="{S["corner"]}"></td>'
               f'<th style="{S["head12"].replace("left:0;", f"left:{_COL1_W}px;")}{S["top"]}{S["left"]}{S["help"]}"{_tip(MEASURE_HELP["Column Name"])}>{esc("Column Name")}</th>'
               + "".join(f'<th style="{S["head"]}{S["top"]}">{esc(c["name"])}</th>' for c in cols) + "</tr>")
    out.append(f'<tr><td style="{label_style}{S["help"]}"{_tip(MEASURE_HELP["Data Type"])}>{esc("Data Type")}</td>'
               + "".join(td(type_cell(c)) for c in cols) + "</tr>")
    out.append(f'<tr><td style="{label_style}{S["help"]}"{_tip(MEASURE_HELP["BEAM✲"])}>BEAM✲</td>'
               + "".join(td(beam_cell(c)) for c in cols) + "</tr>")
    out += group(0, "Data Profiling Results", profiling)
    out += group(1, "Variation", variation)
    out += group(2, "Distribution", distribution_rows(cols, S))
    sample = table.get("sample_rows") or []
    if sample and show_values:
        rows = [("", [esc(_value(v, blank="")) for v in r], "cell") for r in sample]
        out += group(3, "Sample Data", rows)
    out += ["</table>", "</div>"]
    return out


# ---- the relationships diagram ----------------------------------------------

def _mermaid_id(name: str, taken: Dict[str, str]) -> str:
    if name in taken:
        return taken[name]
    # Prefix every id so table names like "end" or "graph" can't clash with Mermaid keywords.
    base = "t_" + re.sub(r"[^A-Za-z0-9_]", "_", name)
    ident, n = base, 2
    while ident in taken.values():
        ident = f"{base}_{n}"
        n += 1
    taken[name] = ident
    return ident


def _mm(text: str) -> str:
    """Escape text for a Mermaid label."""
    return (text.replace("#", "#35;").replace("&", "#amp;").replace('"', "#quot;")
            .replace("<", "#lt;").replace(">", "#gt;"))


def er_diagram(profile: Dict[str, Any]) -> List[str]:
    """Table-level diagram (Mermaid flowchart) with plain lines, drawn from the measured relationships.
    No cardinality notation on purpose: most readers don't know it."""
    ids: Dict[str, str] = {}
    lines = ["```mermaid", "flowchart LR"]
    for t in profile["tables"]:
        lines.append(f'    {_mermaid_id(t["name"], ids)}["{_mm(t["name"])}"]')
    seen = set()
    for r in profile.get("relationships") or []:
        pair = tuple(sorted((ids[r["from_table"]], ids[r["to_table"]])))
        if pair in seen or pair[0] == pair[1]:
            continue
        seen.add(pair)
        lines.append(f'    {ids[r["to_table"]]} --- {ids[r["from_table"]]}')
    lines.append("```")
    return lines


def _key_columns(table: Dict[str, Any], entry: Dict[str, Any]) -> Set[str]:
    """Columns that identify a row of the table: declared primary keys plus AI-suggested business or natural keys."""
    keys = {c["name"] for c in table["columns"] if c.get("primary_key")}
    for name, spec in ((entry.get("beam") or {}).get("columns") or {}).items():
        spec = spec if isinstance(spec, dict) else {"codes": list(spec or [])}
        for token in spec.get("codes") or []:
            code = beam.parse(token, "column")
            if code and code.base in ("BK", "NK", "PK"):
                keys.add(name)
    return keys


def diagram_columns(table: Dict[str, Any], entry: Dict[str, Any], rels: List[Dict[str, Any]],
                    limit: int = MAX_DIAGRAM_COLUMNS) -> List[Optional[str]]:
    """Which columns to list in the box, in table order. None stands for "..." (columns skipped here).
    Up to `limit` columns. Above that, the relationship columns and the key columns always come first,
    and the remaining places go to the earliest other columns. If those alone exceed the limit, all are shown."""
    names = [c["name"] for c in table["columns"]]
    if len(names) <= limit:
        return list(names)
    name = table["name"]
    priority = {r["from_column"] for r in rels if r["from_table"] == name}
    priority |= {r["to_column"] for r in rels if r["to_table"] == name}
    priority |= _key_columns(table, entry)
    chosen = {c for c in names if c in priority}
    for c in names:
        if len(chosen) >= limit:
            break
        chosen.add(c)
    out: List[Optional[str]] = []
    skipped = False
    for c in names:
        if c in chosen:
            if skipped:
                out.append(None)
            out.append(c)
            skipped = False
        else:
            skipped = True
    if skipped:
        out.append(None)
    return out


def relationship_diagram(table: Dict[str, Any], entry: Dict[str, Any], profile: Dict[str, Any]) -> List[str]:
    """The current table as a box listing column names, joined by plain lines to plain boxes for the
    tables it is linked to. Returns [] when the table has no measured relationships."""
    name = table["name"]
    rels = [r for r in profile.get("relationships") or [] if name in (r["from_table"], r["to_table"])]
    if not rels:
        return []
    ids: Dict[str, str] = {}
    me = _mermaid_id(name, ids)
    shown = diagram_columns(table, entry, rels)
    body = "<br/>".join("..." if c is None else _mm(c) for c in shown)
    label = f"<div style='text-align:left'><b>{_mm(name)}</b><br/>──────────<br/>{body}</div>"
    lines = ["```mermaid", "flowchart LR", f'    {me}["{label}"]']
    others, seen = [], set()
    for r in rels:
        other = r["to_table"] if r["from_table"] == name else r["from_table"]
        if other not in seen:
            seen.add(other)
            others.append(other)
    for other in others:
        ident = _mermaid_id(other, ids)
        if other != name:
            lines.append(f'    {ident}["{_mm(other)}"]')
        lines.append(f"    {me} --- {ident}")
    lines.append("```")
    return lines


# ---- pages ------------------------------------------------------------------

STORY_INTRO = ("_A data story describes one table: what the thing is, what one row is, "
               "and what to watch out for._")
SOURCE_SHORT = {
    "system_metadata": "Source system metadata, quoted word for word",
    "user_documentation": "Documentation from the data owner",
    "inferred": "Written by AI from the data. Check before relying on it.",
    "pending": "Not written yet",
}


def render_story(table: Dict[str, Any], entry: Dict[str, Any], profile: Dict[str, Any]) -> str:
    source = entry.get("source", "pending")
    ds = profile["dataset"]
    beam_info = entry.get("beam") or {}
    table_tokens = beam_info.get("table") or []
    table_why = beam_info.get("table_why") or ""
    names = [t["name"] for t in profile["tables"]]
    pre = "../"
    show_values = (profile.get("settings") or {}).get("include_values", True)
    table_codes = [c for c in (beam.parse(t, "table") for t in table_tokens) if c]
    src_code = beam.source_code(table, ds)
    rels = [r for r in profile.get("relationships") or [] if table["name"] in (r["from_table"], r["to_table"])]

    reasons = []
    if table_tokens and table_why:
        reasons.append(f"{' '.join(c.text for c in table_codes)}: {table_why}")
    for col, spec in (beam_info.get("columns") or {}).items():
        spec = spec if isinstance(spec, dict) else {"codes": list(spec or [])}
        if spec.get("codes") and spec.get("why"):
            reasons.append(f"{col} {' '.join(spec['codes'])}: {spec['why']}")
    meta = metadata_block({
        "bijoe": "data-story",
        "schema_version": SCHEMA_VERSION,
        "dataset": ds["name"],
        "table": table["name"],
        "grain": entry.get("grain") or None,
        "sampled_rows": table.get("profiled_rows"),
        "columns": table.get("column_count"),
        "description_source": source,
        "confidence": entry.get("confidence"),
        "beam_table_codes": [c.text for c in table_codes],
        "beam_source": src_code,
        "beam_reasons": reasons,
        "evidence": [str(e) for e in entry.get("evidence") or []],
        "relationships": [f"{r['from_table']}.{r['from_column']} -> {r['to_table']}.{r['to_column']}: "
                          f"{r['matched_values']}/{r['checked_values']} values found ({r['coverage_pct']:g}%)"
                          for r in rels],
        "generated_at": profile["generated_at"],
    })

    out = [f"[← {_display_name(ds['name'])} Overview](../index.md) · [BEAM✲ Annotations](../{beam.PAGE}) · "
           f"[How to Read This Wiki](../{HOW_TO_READ})", "", f"# {table['name']}", ""]

    codes_html = beam.links_html(table_tokens, "table", pre, names)
    if source == "pending":
        description = "<i>No description yet. Ask the BI Joe skill to write one, or add it to <code style=\"background:rgba(128,128,128,.25);color:inherit;padding:1px 5px;border-radius:4px;\">_bijoe/descriptions.json</code>.</i>"
    else:
        description = inline_html((entry.get("description") or "").strip(), pre)
    grain = entry.get("grain") or ""
    rows: List[Tuple[str, str]] = [
        (esc("Description"), description),
        (esc("Grain"), inline_html(grain, pre) if grain.strip() else "<i>pending</i>"),
        (esc("BEAM✲"), f"{codes_html} <i>(suggested by AI)</i>" if codes_html else "<i>pending</i>"),
    ]
    if codes_html and table_why:
        rows.append((f"Why {codes_html}", inline_html(table_why, pre)))
    rows += [
        (esc("Source"), beam.links_html([src_code], "table", pre) + " <i>(measured)</i>"),
        (esc("Sampled Rows"), f"{table.get('profiled_rows', 0):,}"),
        (esc("Columns"), f"{table.get('column_count', 0):,}"),
        (esc("Description Source"), esc(SOURCE_SHORT[source])),
        (esc("Confidence"), esc(entry.get("confidence") or "") if source == "inferred" else ""),
    ]
    out += _property_table_html(rows)

    out += ["", "## Columns", ""] + columns_matrix(table, entry, profile, pre, show_values)
    note = ("_BEAM✲ codes in plain text are measured from the data; codes in italics are suggested by AI. "
            f"Change can't be seen in a single snapshot of the data. [What do the codes mean?]({pre}{beam.PAGE})_")
    out += ["", note]
    if not show_values:
        out += ["", "_Example values and sample rows are hidden: this profile was made without example values._"]

    out += ["", "## Relationships (Measured)", ""]
    diagram = relationship_diagram(table, entry, profile)
    out += diagram if diagram else ["N/A"]

    notes = (entry.get("ai_notes") or "").strip()
    if notes and source != "pending":
        out += ["", "## Additional Context (Written by AI)", "", beam.link_prose(notes, pre)]
    questions = entry.get("open_questions") or []
    if questions:
        out += ["", "## Open Questions for the Data Owner", ""]
        out.extend(f"- {beam.link_prose(q, pre)}" for q in questions)
    out += meta
    return "\n".join(out) + "\n"


def render_index(profile: Dict[str, Any], descriptions: Dict[str, Any]) -> str:
    ds = profile["dataset"]
    tables = profile["tables"]
    names = [t["name"] for t in tables]
    sampled_rows = sum(t.get("profiled_rows") or 0 for t in tables)
    dataset_desc = descriptions.get("dataset") or {}
    summary = (dataset_desc.get("summary") or "").strip()
    rels = profile.get("relationships") or []
    settings = profile.get("settings") or {}

    meta = metadata_block({
        "bijoe": "data-profile-index",
        "schema_version": SCHEMA_VERSION,
        "dataset": ds["name"],
        "source": ds["source"],
        "source_type": ds["source_type"],
        "connector": ds["connector"],
        "tables": len(tables),
        "sampled_rows": sampled_rows,
        "relationships": len(rels),
        "generated_at": profile["generated_at"],
        "generator": f"bi-joe-data-profiler {profile['bijoe_version']}",
    })
    about = inline_html(summary) if summary else "<i>pending</i>"
    if summary and dataset_desc.get("source") == "inferred":
        about += " <i>(written by AI)</i>"
    out = [f"# {_display_name(ds['name'])}: Data Profile", "", "## At a Glance", ""]
    out += property_table([
        ("About", about),
        ("Source", esc(f"{ds['source']} ({ds['connector']})")),
        ("Tables", f"{len(tables):,}"),
        ("Sampled Rows", f"{sampled_rows:,}"),
        ("Profiled", f"{profile['generated_at'][:16].replace('T', ' ')} UTC"),
        ("Purpose", esc(settings.get("purpose") or "")),
        ("How to Read", f'<a href="{HOW_TO_READ}">How to Read This Wiki</a> · '
                        f'<a href="{beam.PAGE}">BEAM✲ Annotations</a>'),
    ])
    out += ["", "## Data Stories", "", STORY_INTRO, "",
            "| Table | BEAM✲ | Grain | Description | Sampled Rows | Columns |", "|---|---|---|---|---:|---:|"]
    for t in tables:
        entry = _entry(descriptions, t["name"])
        link = f"[{_cell(t['name'])}]({STORIES_DIR}/{t['slug']}.md)"
        codes = beam.links(((entry.get("beam") or {}).get("table")) or [], "table", "", names)
        grain = _cell(entry.get("grain") or "_pending_")
        desc = "_pending_" if entry["source"] == "pending" else _cell(beam.link_prose(entry["description"]))
        out.append(f"| {link} | {codes} | {grain} | {desc} | {t.get('profiled_rows', 0):,} | "
                   f"{t.get('column_count', 0):,} |")
    out += ["", "## Data Model", "", "_How the tables connect, drawn from the measured relationships._", ""]
    out += er_diagram(profile)
    out += meta
    return "\n".join(out) + "\n"


def _is_generated(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return False
    return 'bijoe: "data-story"' in text


def render(out_dir: Path, profile: Dict[str, Any], descriptions: Dict[str, Any]) -> List[Path]:
    set_theme((profile.get("settings") or {}).get("theme"))
    stories = out_dir / STORIES_DIR
    stories.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []
    keep = set()
    for t in profile["tables"]:
        p = stories / f"{t['slug']}.md"
        p.write_text(render_story(t, _entry(descriptions, t["name"]), profile), encoding="utf-8", newline="\n")
        written.append(p)
        keep.add(p.name)
    for old in stories.glob("*.md"):  # remove stories for tables no longer profiled
        if old.name not in keep and _is_generated(old):
            old.unlink()
    beam.copy_page(out_dir)  # the same reference page in every wiki, never regenerated
    shutil.copyfile(beam.ASSET.parent / HOW_TO_READ, out_dir / HOW_TO_READ)  # static, like the BEAM page
    index = out_dir / "index.md"
    index.write_text(render_index(profile, descriptions), encoding="utf-8", newline="\n")
    written.insert(0, index)
    return written
