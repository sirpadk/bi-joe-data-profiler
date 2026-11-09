"""BEAM✲ annotations: parsing, measuring, and rendering codes as links.

The reference page (skills/bi-joe-data-profiler/assets/beam-annotations.md) is written
once and copied into every wiki. Every code shown in the wiki links to its anchor there.

Two kinds of codes:
  measured   computed by the engine from the data (data types, ND, PK, NN, FK, {Source})
  suggested  written by the AI in descriptions.json, with a reason (table type, facts, ...)
"""

from __future__ import annotations

import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

PAGE = "beam-annotations.md"
ASSET = Path(__file__).resolve().parent.parent.parent / "assets" / PAGE

TABLE_CODES = {
    "DE": "Discrete Event", "RE": "Recurring Event", "EE": "Evolving Event",
    "TF": "Transaction Fact table", "AS": "Accumulating Snapshot", "PS": "Periodic Snapshot",
    "AG": "Aggregate", "DF": "Derived Fact table",
    "CV": "Current Value dimension", "HV": "Historic Value dimension", "RP": "Role-Playing dimension",
    "RU": "Rollup dimension", "SD": "Swappable Dimension", "ML": "Multi-Level dimension",
    "HM": "Hierarchy Map", "MV": "Multi-Valued bridge", "PD": "Pivoted Dimension",
}
COLUMN_CODES = {
    "MD": "Mandatory", "NN": "Not Null", "ND": "No Duplicates", "X": "Exclusive",
    "DC": "Defining Characteristic",
    "C": "Character", "T": "Text", "N": "Numeric", "I": "Integer", "D": "Date", "DT": "Date/time", "B": "Blob",
    "PK": "Primary Key", "SK": "Surrogate Key", "BK": "Business Key", "NK": "Natural Key",
    "FK": "Foreign Key", "RK": "Recursive Key",
    "CV": "Current Value", "HV": "Historic Value", "FV": "Fixed Value", "PV": "Previous Value",
    "MV": "Multi-Value", "ML": "Multi-Level", "DD": "Degenerate Dimension", "GD": "Granular Dimension",
    "FA": "Fully Additive fact", "SA": "Semi-Additive fact", "NA": "Non-Additive fact", "DF": "Derived Fact",
}
W_TYPES = {"who", "what", "when", "where", "why", "how"}
DATA_TYPES = {"C", "T", "N", "I", "D", "DT", "B"}
#: codes only the engine may set, because they are facts about the data
MEASURED_ONLY = DATA_TYPES | {"ND", "NN", "PK", "FK"}

_CODE_RE = re.compile(r"^([A-Z]+)(\d+(?:[.,]\d+)*)?$")


@dataclass(frozen=True)
class Code:
    text: str  # as written, e.g. "C30", "[who]", "~~MD~~"
    anchor: str  # anchor on the reference page
    base: str  # e.g. "C", "W", "UOM", "SOURCE"
    struck: bool = False

    def link(self, prefix: str = "") -> str:
        label = self.text.replace("[", "\\[").replace("]", "\\]")
        return f"[{label}]({prefix}{PAGE}#{self.anchor})"


def parse(token: str, scope: str, table_names: Iterable[str] = ()) -> Optional[Code]:
    """Parse one code. scope is 'table' or 'column'. Returns None if it isn't a BEAM code."""
    raw = token.strip()
    if not raw:
        return None
    if raw.startswith("~~") and raw.endswith("~~") and len(raw) > 4:
        inner = parse(raw[2:-2], scope, table_names)
        if inner is None:
            return None
        return Code(raw, "c-unavailable", inner.base, struck=True)
    if raw.startswith("{") and raw.endswith("}"):
        return Code(raw, f"{scope[0]}-source", "SOURCE")
    if raw == "?":
        return Code(raw, "c-suspect", "?")
    if raw == "!":
        return Code(raw, "c-important", "!")
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if inner.lower() in W_TYPES:
            return Code(f"[{inner.lower()}]", f"w-{inner.lower()}", "W")
        if scope == "table":
            return parse(inner, scope, table_names)
        if inner.lower() in {t.lower() for t in table_names}:
            return Code(raw, "c-dim", "DIM")
        return Code(raw, "c-uom", "UOM")
    if scope == "column" and raw.upper().startswith("DF="):
        return Code(raw, "c-df", "DF")
    m = _CODE_RE.match(raw)
    if not m:
        return None
    base = m.group(1)
    known = TABLE_CODES if scope == "table" else COLUMN_CODES
    if base not in known:
        return None
    if scope == "table":
        return Code(f"[{raw}]", f"t-{base.lower()}", base)
    return Code(raw, f"c-{base.lower()}", base)


def links(tokens: Sequence[str], scope: str, prefix: str = "", table_names: Iterable[str] = ()) -> str:
    out = []
    for t in tokens:
        code = parse(t, scope, table_names)
        out.append(code.link(prefix) if code else t)
    return " ".join(out)


# ---- prose: link bracketed table codes and W-types written in descriptions ----------

_PROSE_RE = re.compile(r"(?<![\\\w])\[([A-Za-z]{2,5}(?:\s*,\s*[A-Za-z]{2,5})*)\](?!\()")


def link_prose(text: str, prefix: str = "") -> str:
    def repl(m: "re.Match[str]") -> str:
        parts = [p.strip() for p in m.group(1).split(",")]
        codes = []
        for p in parts:
            if p.lower() in W_TYPES:
                codes.append(Code(f"[{p.lower()}]", f"w-{p.lower()}", "W"))
            elif p in TABLE_CODES:
                codes.append(Code(f"[{p}]", f"t-{p.lower()}", p))
            else:
                return m.group(0)
        if len(codes) == 1:
            return codes[0].link(prefix)
        inner = ", ".join(f"[{c.text.strip('[]')}]({prefix}{PAGE}#{c.anchor})" for c in codes)
        return f"\\[{inner}\\]"

    return _PROSE_RE.sub(repl, text)


# ---- measured codes ---------------------------------------------------------------

def data_type_code(col: Dict[str, Any]) -> Optional[str]:
    t = col.get("inferred_type")
    if t == "text":
        n = col.get("max_length")
        if n is None:
            return "C"
        return f"T{n}" if n > 255 else f"C{n}"
    if t == "integer":
        return "I"
    if t == "decimal":
        p, s = col.get("precision"), col.get("scale")
        return f"N{p}.{s}" if p and s is not None else "N"
    if t == "date":
        return "D"
    if t == "datetime":
        return "DT"
    if t == "binary":
        return "B"
    return None  # boolean, time, empty: no BEAM data type


def measured_column_codes(table: Dict[str, Any], col: Dict[str, Any],
                          relationships: Sequence[Dict[str, Any]]) -> List[str]:
    codes: List[str] = []
    if col.get("primary_key"):
        codes.append("PK")
    if col.get("nullable") is False and not col.get("primary_key"):
        codes.append("NN")
    # Unique amounts or dates are usually coincidence, not a rule, so ND is only measured on text/integers.
    if col.get("all_values_unique") and not col.get("missing_count") and not col.get("primary_key") \
            and col.get("inferred_type") in ("text", "integer"):
        codes.append("ND")
    for r in relationships:
        if r["from_table"] == table["name"] and r["from_column"] == col["name"] and r["coverage_pct"] == 100:
            codes.append("RK" if r["to_table"] == table["name"] else "FK")
            break
    return codes


def source_code(table: Dict[str, Any], dataset: Dict[str, Any]) -> str:
    d = table.get("details") or {}
    if d.get("sheet"):
        return f"{{{d.get('file', dataset.get('source', ''))}: {d['sheet']}}}"
    if d.get("file"):
        return f"{{{d['file']}}}"
    if d.get("schema"):
        return f"{{{d['schema']}.{table['name']}}}"
    return f"{{{table['name']}}}"


# ---- reference page ---------------------------------------------------------------

def copy_page(out_dir: Path) -> Path:
    if not ASSET.is_file():
        raise FileNotFoundError(f"BEAM reference page missing: {ASSET}")
    target = out_dir / PAGE
    shutil.copyfile(ASSET, target)
    return target
