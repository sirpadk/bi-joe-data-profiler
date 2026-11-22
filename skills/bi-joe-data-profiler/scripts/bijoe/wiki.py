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

from . import SCHEMA_VERSION, beam

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
    out = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", out)
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

_LINE = "rgba(128,128,128,.4)"
_PROP_TABLE = "border-collapse:collapse;margin:8px 0;"
_PROP_LABEL = (f"text-align:left;vertical-align:top;white-space:nowrap;font-weight:600;"
               f"padding:6px 16px 6px 0;border-bottom:1px solid {_LINE};")
_PROP_VALUE = f"text-align:left;vertical-align:top;padding:6px 0;border-bottom:1px solid {_LINE};"


def property_table(rows: List[Tuple[str, str]]) -> List[str]:
    """Paired information (label + value) as a simple HTML table. Labels are plain text and are put
    in Title Case; values must already be HTML. Rows with an empty value are left out."""
    out = [f'<table style="{_PROP_TABLE}">']
    for label, value in rows:
        if value in (None, ""):
            continue
        out.append(f'<tr><th scope="row" align="left" style="{_PROP_LABEL}">{esc(title_case(label))}</th>'
                   f'<td style="{_PROP_VALUE}">{value}</td></tr>')
    out.append("</table>")
    return out


def _property_table_html(rows: List[Tuple[str, str]]) -> List[str]:
    """Like property_table, but the label is already HTML (used for 'Why [CV]')."""
    out = [f'<table style="{_PROP_TABLE}">']
    for label_html, value in rows:
        if value in (None, ""):
            continue
        out.append(f'<tr><th scope="row" align="left" style="{_PROP_LABEL}">{label_html}</th>'
                   f'<td style="{_PROP_VALUE}">{value}</td></tr>')
    out.append("</table>")
    return out


# ---- the columns matrix -----------------------------------------------------

_LABEL_BG = "background:#eef0f2;color:#1f2328;"
_COL1_W = 34  # px: the narrow first column holding the rotated group names
_CELL = f"border:0 solid {_LINE};border-width:0 1px 1px 0;padding:3px 8px;white-space:nowrap;text-align:left;vertical-align:top;"
_HEAD = _CELL + "font-weight:600;"
_NUM = _CELL.replace("text-align:left", "text-align:right")
_COL1 = (f"position:sticky;left:0;z-index:2;{_LABEL_BG}box-sizing:border-box;width:{_COL1_W}px;min-width:{_COL1_W}px;"
         f"max-width:{_COL1_W}px;border:0 solid {_LINE};border-width:0 1px 1px 0;padding:4px 0;text-align:center;vertical-align:middle;")
_COL2 = (f"position:sticky;left:{_COL1_W}px;z-index:2;{_LABEL_BG}border:0 solid {_LINE};border-width:0 1px 1px 0;"
         f"padding:3px 8px;white-space:nowrap;text-align:left;vertical-align:top;font-weight:600;")
_COL12 = (f"position:sticky;left:0;z-index:2;{_LABEL_BG}border:0 solid {_LINE};border-width:0 1px 1px 0;"
          f"padding:3px 8px;white-space:nowrap;text-align:left;vertical-align:top;font-weight:600;")
_ROTATED = "writing-mode:vertical-rl;transform:rotate(180deg);white-space:nowrap;margin:0 auto;font-weight:600;"

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

    def td(content: str, style: str = _CELL) -> str:
        return f'<td style="{style}">{content}</td>'

    def type_cell(c: Dict[str, Any]) -> str:
        code = beam.data_type_code(c)
        plain = esc(_PLAIN_TYPES.get(c["inferred_type"], c["inferred_type"]))
        return (beam.links_html([code], "column", pre) + " " if code else "") + plain

    def beam_cell(c: Dict[str, Any]) -> str:
        measured = beam.links_html(beam.measured_column_codes(table, c, rels), "column", pre, names)
        sug = _column_suggestion(suggestions.get(c["name"]), c)
        suggested = beam.links_html(sug["codes"], "column", pre, names, italic=True)
        return " ".join(x for x in (measured, suggested) if x)

    def group(label: str, rows: List[Tuple[str, List[str], str]]) -> List[str]:
        out = []
        for i, (row_label, cells, style) in enumerate(rows):
            tr = "<tr>"
            if i == 0:
                tr += (f'<td rowspan="{len(rows)}" style="{_COL1}"><div style="{_ROTATED}">'
                       f'{esc(title_case(label))}</div></td>')
            tr += f'<td style="{_COL2}">{esc(title_case(row_label))}</td>'
            tr += "".join(td(c, style) for c in cells) + "</tr>"
            out.append(tr)
        return out

    hidden = "<i>hidden</i>"
    profiling = [
        ("Sample Count", [f"{n:,}" for _ in cols], _NUM),
        ("Missing", [_count_pct(c.get("missing_count", 0), n) for c in cols], _CELL),
        ("Unique Values", [_count_pct(c.get("distinct_count", 0), n) for c in cols], _CELL),
        ("Min Value", [esc(_value(c.get("min_value"))) for c in cols], _CELL),
        ("Min Count", [_count_pct(c["min_count"], n) if "min_count" in c else "—" for c in cols], _CELL),
        ("Max Value", [esc(_value(c.get("max_value"))) for c in cols], _CELL),
        ("Max Count", [_count_pct(c["max_count"], n) if "max_count" in c else "—" for c in cols], _CELL),
        ("Min Length", [str(c["min_length"]) if "min_length" in c else "—" for c in cols], _NUM),
        ("Max Length", [str(c["max_length"]) if "max_length" in c else "—" for c in cols], _NUM),
    ]
    variation = []
    for label in ("Typical", "Different", "Repeat", "Missing", "Range", "Change"):
        cells = []
        for c in cols:
            text = _example(label, c, show_values)
            cells.append(esc(text) if text else hidden)
        variation.append((label, cells, _CELL))

    out = ['<div style="overflow-x:auto;max-width:100%;">',
           f'<table style="border-collapse:separate;border-spacing:0;border:1px solid {_LINE};border-width:1px 0 0 1px;font-size:90%;">']
    out.append(f'<tr><th colspan="2" style="{_COL12}">{esc("Column Name")}</th>'
               + "".join(f'<th style="{_HEAD}">{esc(c["name"])}</th>' for c in cols) + "</tr>")
    out.append(f'<tr><td colspan="2" style="{_COL12}">{esc("Data Type")}</td>'
               + "".join(td(type_cell(c)) for c in cols) + "</tr>")
    out.append(f'<tr><td colspan="2" style="{_COL12}">BEAM✲</td>'
               + "".join(td(beam_cell(c)) for c in cols) + "</tr>")
    out += group("Data Profiling Results", profiling)
    out += group("Variation", variation)
    sample = table.get("sample_rows") or []
    if sample and show_values:
        rows = [("", [esc(_value(v, blank="")) for v in r], _CELL) for r in sample]
        out += group("Sample Data", rows)
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
        description = "<i>No description yet. Ask the BI Joe skill to write one, or add it to <code>_bijoe/descriptions.json</code>.</i>"
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
