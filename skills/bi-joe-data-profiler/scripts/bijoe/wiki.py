"""Renders profile.json + descriptions.json into a linked Markdown wiki.

Layout:
    <out>/index.md                    landing page: summary + list of data stories
    <out>/data-stories/<slug>.md      one data story per table
    <out>/_bijoe/profile.json         measured facts (machine-readable)
    <out>/_bijoe/descriptions.json    written descriptions + provenance

Every page ends with a "Metadata" section holding a fenced ```yaml block, so other AI
agents and tools can read the wiki without parsing prose, while people see the content
first.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from . import SCHEMA_VERSION, beam

STORIES_DIR = "data-stories"

SOURCE_LABELS = {
    "system_metadata": "Taken word for word from the description stored in the source system.",
    "user_documentation": "Taken from documentation provided by the data owner.",
    "inferred": "Written by AI from the table's name, columns and values. Check it before you rely on it.",
    "pending": "No description yet.",
}


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


# ---- markdown helpers -------------------------------------------------------

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


def _num(n: Optional[int]) -> str:
    return "?" if n is None else f"{n:,}"


def _first_sentence(text: str, limit: int = 160) -> str:
    text = " ".join(text.split())
    m = re.search(r"(?<=[.!?])\s", text)
    sentence = text[: m.start()] if m else text
    return sentence if len(sentence) <= limit else sentence[: limit - 1].rstrip() + "…"


def _entry(descriptions: Dict[str, Any], table: str) -> Dict[str, Any]:
    entry = (descriptions.get("tables") or {}).get(table) or {}
    if not (entry.get("description") or "").strip():
        entry = {**entry, "source": "pending"}
    return entry


# ---- pages ------------------------------------------------------------------

_PLAIN_TYPES = {"text": "text", "integer": "whole number", "decimal": "number", "date": "date",
                "datetime": "date/time", "boolean": "yes/no", "time": "time", "binary": "binary", "empty": "empty"}


def _table_names(profile: Dict[str, Any]) -> List[str]:
    return [t["name"] for t in profile["tables"]]


def _slugs(profile: Dict[str, Any]) -> Dict[str, str]:
    return {t["name"]: t["slug"] for t in profile["tables"]}


def _beam(entry: Dict[str, Any]) -> Dict[str, Any]:
    b = entry.get("beam") or {}
    return {"table": b.get("table") or [], "table_why": b.get("table_why") or "", "columns": b.get("columns") or {}}


def _column_suggestion(spec: Any, col: Dict[str, Any]) -> Dict[str, Any]:
    spec = spec if isinstance(spec, dict) else {"codes": list(spec or [])}
    codes = []
    for c in spec.get("codes") or []:
        if c == "MD" and col.get("missing_count"):
            c = "~~MD~~"  # should always be filled in, but the data has gaps
        codes.append(c)
    return {"codes": codes, "why": spec.get("why") or ""}


def _examples(col: Dict[str, Any], n: int = 3, width: int = 25) -> str:
    vals = []
    for v in col.get("top_values", [])[:n]:
        text = str(v["value"])
        vals.append(text if len(text) <= width else text[: width - 1] + "…")
    return ", ".join(vals)


def render_story(table: Dict[str, Any], entry: Dict[str, Any], profile: Dict[str, Any]) -> str:
    source = entry.get("source", "pending")
    description = (entry.get("description") or "").strip()
    b = _beam(entry)
    names = _table_names(profile)
    slugs = _slugs(profile)
    pre = "../"
    table_codes = [c for c in (beam.parse(t, "table") for t in b["table"]) if c]
    meta = metadata_block({
        "bijoe": "data-story",
        "schema_version": SCHEMA_VERSION,
        "dataset": profile["dataset"]["name"],
        "table": table["name"],
        "rows": table.get("row_count"),
        "columns": table.get("column_count"),
        "description_source": source,
        "confidence": entry.get("confidence"),
        "beam_table_codes": [c.text for c in table_codes],
        "beam_source": beam.source_code(table, profile["dataset"]),
        "generated_at": profile["generated_at"],
    })
    out = [f"[← {profile['dataset']['name']} overview](../index.md) · [BEAM✲ annotations](../{beam.PAGE})", "",
           f"# {table['name']}", ""]
    tags = []
    if b["table"]:
        tags.append(beam.links(b["table"], "table", pre, names) + " _(suggested by AI)_")
    tags.append(beam.links([beam.source_code(table, profile["dataset"])], "table", pre) + " _(measured)_")
    out += ["**BEAM✲:** " + " · ".join(tags), "", "## Description", ""]
    if source == "pending":
        out.append("_No description yet. Ask the BI Joe skill to write one, or add it to `_bijoe/descriptions.json`._")
    else:
        out.append(beam.link_prose(description, pre))
        out.append("")
        provenance = f"> **Where this comes from:** {SOURCE_LABELS[source]}"
        if source == "inferred" and entry.get("confidence"):
            provenance += f" Confidence: **{entry['confidence']}**."
        out.append(provenance)
        evidence = entry.get("evidence") or []
        if evidence and source != "system_metadata":
            out.append(">")
            out.append("> **Based on:**")
            out.extend(f"> - {beam.link_prose(str(item), pre)}" for item in evidence)
        if b["table"] and b["table_why"]:
            why_codes = beam.links(b["table"], "table", pre, names)
            out += [">", f"> **Why {why_codes}:** {beam.link_prose(b['table_why'], pre)}"]
    notes = (entry.get("ai_notes") or "").strip()
    if notes and source != "pending":
        out += ["", "### Additional context (written by AI)", "", beam.link_prose(notes, pre)]
    questions = entry.get("open_questions") or []
    if questions:
        out += ["", "### Open questions for the data owner", ""]
        out.extend(f"- {beam.link_prose(q, pre)}" for q in questions)

    # columns
    rels = profile.get("relationships") or []
    has_values = any(c.get("top_values") for c in table["columns"])
    head = "| Column | Type | Measured | Suggested | Missing | Distinct |" + (" Examples |" if has_values else "")
    out += ["", "## Columns", "", head, "|---|---|---|---|---:|---:|" + ("---|" if has_values else "")]
    reasons = []
    for col in table["columns"]:
        dtype = beam.data_type_code(col)
        plain = _PLAIN_TYPES.get(col["inferred_type"], col["inferred_type"])
        type_cell = (beam.links([dtype], "column", pre) + " " if dtype else "") + plain
        measured = beam.links(beam.measured_column_codes(table, col, rels), "column", pre, names)
        sug = _column_suggestion(b["columns"].get(col["name"]), col)
        suggested = beam.links(sug["codes"], "column", pre, names)
        if sug["codes"] and sug["why"]:
            reasons.append(f"- **{_cell(col['name'])}** {suggested}: {beam.link_prose(sug['why'], pre)}")
        row = (f"| {_cell(col['name'])} | {type_cell} | {measured} | {suggested} | "
               f"{col.get('missing_pct', 0):g}% | {col['distinct_count']:,} |")
        if has_values:
            row += f" {_cell(_examples(col))} |"
        out.append(row)
    sample_note = f" Statistics use the first {table['profiled_rows']:,} rows." if table.get("sampled") else ""
    out += ["", "**Measured** codes come from the data. **Suggested** codes are AI judgement, "
                f"with the reasons below.{sample_note} [What do the codes mean?](../{beam.PAGE})"]
    if reasons:
        out += ["", "**Why the suggestions:**", ""] + reasons

    # relationships
    outgoing = [r for r in rels if r["from_table"] == table["name"]]
    incoming = [r for r in rels if r["to_table"] == table["name"] and r["from_table"] != table["name"]]
    if outgoing or incoming:
        out += ["", "## Relationships (measured)", ""]
        for r in outgoing:
            code = "RK" if r["to_table"] == table["name"] else "FK"
            tag = " " + beam.links([code], "column", pre) if r["coverage_pct"] == 100 else ""
            out.append(f"- `{r['from_column']}` → [{_cell(r['to_table'])}]({slugs[r['to_table']]}.md) "
                       f"`{r['to_column']}`: {r['matched_values']:,} of {r['checked_values']:,} values found "
                       f"({r['coverage_pct']:g}%){tag}")
        for r in incoming:
            out.append(f"- Referenced by [{_cell(r['from_table'])}]({slugs[r['from_table']]}.md) "
                       f"`{r['from_column']}` → `{r['to_column']}` ({r['coverage_pct']:g}% of values found)")
    out += meta
    return "\n".join(out) + "\n"


def render_index(profile: Dict[str, Any], descriptions: Dict[str, Any]) -> str:
    ds = profile["dataset"]
    tables = profile["tables"]
    names = _table_names(profile)
    slugs = _slugs(profile)
    total_rows = sum(t.get("row_count") or 0 for t in tables)
    dataset_desc = descriptions.get("dataset") or {}
    summary = (dataset_desc.get("summary") or "").strip()
    sampled = [t["name"] for t in tables if t.get("sampled")]
    rels = profile.get("relationships") or []

    meta = metadata_block({
        "bijoe": "data-profile-index",
        "schema_version": SCHEMA_VERSION,
        "dataset": ds["name"],
        "source": ds["source"],
        "source_type": ds["source_type"],
        "connector": ds["connector"],
        "tables": len(tables),
        "total_rows": total_rows,
        "relationships": len(rels),
        "generated_at": profile["generated_at"],
        "generator": f"bi-joe-data-profiler {profile['bijoe_version']}",
    })
    out = [f"# {ds['name']}: data profile", ""]
    if summary:
        out += [beam.link_prose(summary), ""]
        if dataset_desc.get("source") == "inferred":
            out += ["> Summary written by AI from the profile below. Check it before you rely on it.", ""]
    else:
        out += ["_No summary yet._", ""]

    out += [
        "## At a glance", "",
        "| | |", "|---|---|",
        f"| Source | {_cell(ds['source'])} ({ds['connector']}) |",
        f"| Tables | {len(tables):,} |",
        f"| Total rows | {total_rows:,} |",
        f"| Profiled | {profile['generated_at'][:16].replace('T', ' ')} UTC |",
    ]
    settings = profile.get("settings") or {}
    if settings.get("purpose"):
        out.append(f"| Purpose | {_cell(settings['purpose'])} |")
    if sampled:
        out.append(f"| Sampled | Statistics use the first {settings.get('sample_rows', 0):,} rows of: "
                   f"{_cell(', '.join(sampled))} |")
    out += ["", "## Data stories", "", "One page per table.", "",
            "| Table | BEAM✲ | Rows | Columns | Description |", "|---|---|---:|---:|---|"]
    for t in tables:
        entry = _entry(descriptions, t["name"])
        if entry["source"] == "pending":
            desc = "_pending_"
        else:
            desc = _cell(beam.link_prose(_first_sentence(entry["description"])))
        link = f"[{_cell(t['name'])}]({STORIES_DIR}/{t['slug']}.md)"
        codes = beam.links(_beam(entry)["table"], "table", "", names)
        out.append(f"| {link} | {codes} | {_num(t.get('row_count'))} | {t.get('column_count', 0):,} | {desc} |")

    if rels:
        out += ["", "## How the tables connect (measured)", ""]
        for r in rels:
            tag = " " + beam.links(["FK"], "column") if r["coverage_pct"] == 100 else ""
            out.append(f"- [{_cell(r['from_table'])}]({STORIES_DIR}/{slugs[r['from_table']]}.md) "
                       f"`{r['from_column']}` → [{_cell(r['to_table'])}]({STORIES_DIR}/{slugs[r['to_table']]}.md) "
                       f"`{r['to_column']}` ({r['coverage_pct']:g}% of values found){tag}")

    out += ["", "## How to read this wiki", "",
            "Every description says where it comes from:", ""]
    for key in ("system_metadata", "user_documentation", "inferred"):
        out.append(f"- **{key}**: {SOURCE_LABELS[key]}")
    cv, nd = beam.links(["CV"], "table"), beam.links(["ND"], "column")
    out += ["", f"Short codes like {cv} or {nd} are **BEAM✲ annotations**. Click any code, "
                f"or see [all BEAM✲ annotations]({beam.PAGE}).",
            "", "The measured facts behind this wiki are in [`_bijoe/profile.json`](_bijoe/profile.json)."]
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
    index = out_dir / "index.md"
    index.write_text(render_index(profile, descriptions), encoding="utf-8", newline="\n")
    written.insert(0, index)
    return written
