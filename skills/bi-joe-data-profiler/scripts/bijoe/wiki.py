"""Renders profile.json + descriptions.json into a linked Markdown wiki.

Layout:
    <out>/index.md                    landing page: summary + list of data stories
    <out>/data-stories/<slug>.md      one data story per table
    <out>/_bijoe/profile.json         measured facts (machine-readable)
    <out>/_bijoe/descriptions.json    written descriptions + provenance

Every page starts with YAML front matter so other AI agents and tools can read the
wiki without parsing prose.
"""

from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from . import SCHEMA_VERSION

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


def front_matter(fields: Dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:" + ("" if value else " []"))
            lines.extend(f"  - {_yaml_value(v)}" for v in value)
        else:
            lines.append(f"{key}: {_yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines)


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

def render_story(table: Dict[str, Any], entry: Dict[str, Any], profile: Dict[str, Any]) -> str:
    source = entry.get("source", "pending")
    description = (entry.get("description") or "").strip()
    fm = front_matter({
        "bijoe": "data-story",
        "schema_version": SCHEMA_VERSION,
        "dataset": profile["dataset"]["name"],
        "table": table["name"],
        "rows": table.get("row_count"),
        "columns": table.get("column_count"),
        "description_source": source,
        "confidence": entry.get("confidence"),
        "generated_at": profile["generated_at"],
    })
    out = [fm, "", f"[← {profile['dataset']['name']} overview](../index.md)", "", f"# {table['name']}", "",
           "## Description", ""]
    if source == "pending":
        out.append("_No description yet. Ask the BI Joe skill to write one, or add it to `_bijoe/descriptions.json`._")
    else:
        out.append(description)
        out.append("")
        provenance = f"> **Where this comes from:** {SOURCE_LABELS[source]}"
        if source == "inferred" and entry.get("confidence"):
            provenance += f" Confidence: **{entry['confidence']}**."
        out.append(provenance)
        evidence = entry.get("evidence") or []
        if evidence and source != "system_metadata":
            out.append(">")
            out.append("> **Based on:**")
            out.extend(f"> - {item}" for item in evidence)
    notes = (entry.get("ai_notes") or "").strip()
    if notes and source != "pending":
        out += ["", "### Additional context (written by AI)", "", notes]
    questions = entry.get("open_questions") or []
    if questions:
        out += ["", "### Open questions for the data owner", ""]
        out.extend(f"- {q}" for q in questions)
    return "\n".join(out) + "\n"


def render_index(profile: Dict[str, Any], descriptions: Dict[str, Any]) -> str:
    ds = profile["dataset"]
    tables = profile["tables"]
    total_rows = sum(t.get("row_count") or 0 for t in tables)
    dataset_desc = descriptions.get("dataset") or {}
    summary = (dataset_desc.get("summary") or "").strip()
    sampled = [t["name"] for t in tables if t.get("sampled")]

    fm = front_matter({
        "bijoe": "data-profile-index",
        "schema_version": SCHEMA_VERSION,
        "dataset": ds["name"],
        "source": ds["source"],
        "source_type": ds["source_type"],
        "connector": ds["connector"],
        "tables": len(tables),
        "total_rows": total_rows,
        "generated_at": profile["generated_at"],
        "generator": f"bi-joe-data-profiler {profile['bijoe_version']}",
    })
    out = [fm, "", f"# {ds['name']}: data profile", ""]
    if summary:
        out += [summary, ""]
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
            "| Table | Rows | Columns | Description |", "|---|---:|---:|---|"]
    for t in tables:
        entry = _entry(descriptions, t["name"])
        desc = "_pending_" if entry["source"] == "pending" else _cell(_first_sentence(entry["description"]))
        link = f"[{_cell(t['name'])}]({STORIES_DIR}/{t['slug']}.md)"
        out.append(f"| {link} | {_num(t.get('row_count'))} | {t.get('column_count', 0):,} | {desc} |")

    out += ["", "## How to read the descriptions", "",
            "Every description says where it comes from:", ""]
    for key in ("system_metadata", "user_documentation", "inferred"):
        out.append(f"- **{key}**: {SOURCE_LABELS[key]}")
    out += ["", "The measured facts behind this wiki are in [`_bijoe/profile.json`](_bijoe/profile.json).", ""]
    return "\n".join(out)


def _is_generated(path: Path) -> bool:
    try:
        head = path.read_text(encoding="utf-8")[:200]
    except OSError:
        return False
    return "bijoe: \"data-story\"" in head or "bijoe: data-story" in head


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
    index = out_dir / "index.md"
    index.write_text(render_index(profile, descriptions), encoding="utf-8", newline="\n")
    written.insert(0, index)
    return written
