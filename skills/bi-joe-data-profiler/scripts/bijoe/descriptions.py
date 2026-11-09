"""descriptions.json: the human/LLM-written part of the wiki, and the checks that keep it honest.

The profiler writes facts to profile.json. Descriptions are written separately so the
wiki can be re-generated without losing them, and so they can be checked against the
facts before they are published.

Each table entry:
    description     the text shown on the data story
    source          system_metadata | user_documentation | inferred | pending
    confidence      high | medium | low        (required when source is inferred)
    evidence        list of facts the description is based on  (required when inferred)
    open_questions  what could not be determined and should be asked of the data owner
    ai_notes        optional inferred context added next to a system/user description
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

SOURCES = {"system_metadata", "user_documentation", "inferred", "pending"}
CONFIDENCE = {"high", "medium", "low"}
MIN_LENGTH = 50

HOW_TO_FILL = (
    "Fill each entry following references/writing-descriptions.md in the bi-joe-data-profiler skill. "
    "source: system_metadata | user_documentation | inferred | pending. "
    "When source is inferred, confidence (high|medium|low) and evidence are required. "
    "Put `backticks` only around real table names, column names or observed values. "
    "Then run: bijoe check <dir> and bijoe render <dir>."
)

# Phrases that state the obvious or pad the text. Each comes with a hint.
WEAK_PATTERNS: List[Tuple[str, str]] = [
    (r"\b(contains?|stores?|holds?|includes?) (the )?(information|data|details|records) (about|on|of|for|related to|regarding)\b",
     "says the table holds data about something; say what one row represents instead"),
    (r"\bdata related to\b", "vague; name the business event or entity"),
    (r"\bvarious\b", "vague; name the things or drop the word"),
    (r"\b(valuable|actionable) insights?\b", "marketing language; drop it"),
    (r"\bplays an? (crucial|key|vital|important) role\b", "filler; drop it"),
    (r"\b(comprehensive|robust|seamless(ly)?)\b", "filler adjective; drop it"),
    (r"\b(is|are) used (to|for) (store|storing|keep|keeping) (data|information)\b", "states the obvious"),
]

BACKTICK_RE = re.compile(r"`([^`\n]+)`")


def empty_entry() -> Dict[str, Any]:
    return {
        "description": "",
        "source": "pending",
        "confidence": None,
        "evidence": [],
        "open_questions": [],
        "ai_notes": "",
    }


def path_for(out_dir: Path) -> Path:
    return out_dir / "_bijoe" / "descriptions.json"


def load(out_dir: Path) -> Dict[str, Any]:
    p = path_for(out_dir)
    if p.is_file():
        return json.loads(p.read_text(encoding="utf-8"))
    return {}


def save(out_dir: Path, data: Dict[str, Any]) -> None:
    p = path_for(out_dir)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def merge(existing: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]:
    """Keep what was written before; add new tables; refresh system metadata."""
    data: Dict[str, Any] = {"_how_to_fill": HOW_TO_FILL}
    dataset = existing.get("dataset") or {}
    data["dataset"] = {
        "summary": dataset.get("summary", ""),
        "source": dataset.get("source", "pending"),
        "evidence": dataset.get("evidence", []),
    }
    old_tables = existing.get("tables") or {}
    tables: Dict[str, Any] = {}
    for t in profile["tables"]:
        entry = {**empty_entry(), **old_tables.get(t["name"], {})}
        comment = (t.get("comment") or "").strip()
        if comment and entry["source"] in ("pending", "system_metadata"):
            entry.update(
                description=comment,
                source="system_metadata",
                confidence="high",
                evidence=entry["evidence"] or ["Table comment stored in the source system"],
            )
        tables[t["name"]] = entry
    # Keep entries for tables not in this run (e.g. profiled with --tables) so nothing is lost.
    for name, entry in old_tables.items():
        tables.setdefault(name, entry)
    data["tables"] = tables
    return data


def _known_names(profile: Dict[str, Any]) -> Set[str]:
    names: Set[str] = set()
    for t in profile["tables"]:
        names.add(t["name"].lower())
        for c in t["columns"]:
            names.add(c["name"].lower())
            names.add(f"{t['name']}.{c['name']}".lower())
            for v in c.get("top_values", []):
                names.add(str(v["value"]).lower())
    return names


def _check_text(label: str, text: str, known: Set[str], problems: List[Tuple[str, str, str]]) -> None:
    for pattern, hint in WEAK_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            problems.append(("warning", label, f"weak phrase '{m.group(0)}': {hint}"))
    for ref in BACKTICK_RE.findall(text):
        if ref.strip().lower() not in known:
            problems.append((
                "warning", label,
                f"`{ref}` is not a table, column or observed value in the profile; make sure it is not invented",
            ))


def lint(profile: Dict[str, Any], data: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Return (level, where, message) tuples. level is 'error', 'warning' or 'todo'."""
    problems: List[Tuple[str, str, str]] = []
    known = _known_names(profile)
    by_name = {t["name"]: t for t in profile["tables"]}
    tables = data.get("tables") or {}

    dataset = data.get("dataset") or {}
    if not (dataset.get("summary") or "").strip():
        problems.append(("todo", "dataset", "dataset summary is still empty"))
    else:
        _check_text("dataset", dataset["summary"], known, problems)

    for name in by_name:
        if name not in tables:
            problems.append(("todo", name, "no entry in descriptions.json"))

    for name, entry in tables.items():
        if name not in by_name:
            continue  # kept from an earlier run; not rendered
        where = f"table {name}"
        source = entry.get("source", "pending")
        text = (entry.get("description") or "").strip()
        if source not in SOURCES:
            problems.append(("error", where, f"unknown source '{source}' (use one of {sorted(SOURCES)})"))
            continue
        if source == "pending" or not text:
            problems.append(("todo", where, "description not written yet"))
            continue
        if source == "system_metadata":
            comment = (by_name[name].get("comment") or "").strip()
            if not comment:
                problems.append(("error", where, "source is system_metadata but the source system has no comment for this table"))
            elif text != comment:
                problems.append(("error", where, "system metadata must be quoted exactly; put your own additions in ai_notes"))
        else:
            _check_text(where, text, known, problems)
            if len(text) < MIN_LENGTH and source == "inferred":
                problems.append(("warning", where, f"only {len(text)} characters; it likely adds nothing beyond the table name"))
        if source == "inferred":
            if entry.get("confidence") not in CONFIDENCE:
                problems.append(("error", where, "inferred descriptions need confidence: high, medium or low"))
            if not entry.get("evidence"):
                problems.append(("error", where, "inferred descriptions need at least one evidence item"))
            if entry.get("confidence") == "low" and not entry.get("open_questions"):
                problems.append(("warning", where, "low confidence: add open_questions saying what to ask the data owner"))
        for item in entry.get("evidence") or []:
            _check_text(f"{where} evidence", str(item), known, problems)
        notes = (entry.get("ai_notes") or "").strip()
        if notes:
            _check_text(f"{where} ai_notes", notes, known, problems)
    return problems
