"""BEAM✲ annotations: parsing, measuring, and rendering codes as links.

The reference page (skills/bi-joe-data-profiler/assets/beam-annotations.md) is written
once and copied into every wiki. Every code shown in the wiki links to its anchor there.

Two kinds of codes:
  measured   computed by the engine from the data (data types, ND, PK, NN, FK, {Source})
  suggested  written by the AI in descriptions.json, with a reason (table type, facts, ...)
"""

from __future__ import annotations

import html
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



# ---- hover text: the reference page is the single source for what each code means ------------

_ROW_RE = re.compile(r'<a id="([^"]+)"></a>(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|')
_hover: Dict[str, str] = {}


def _plain(text: str) -> str:
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"", text)  # [label](url) -> label
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("**", "").replace("*", "").replace("`", "").replace("~~", "").replace("\\", "")
    return re.sub(r"\s+", " ", text).strip()


def _shorten(text: str, limit: int = 230) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = cut.rfind(". ")
    return cut[: end + 1] if end > 60 else cut.rsplit(" ", 1)[0].rstrip(" ,;") + "…"


def _load_hover() -> Dict[str, str]:
    if _hover:
        return _hover
    try:
        lines = ASSET.read_text(encoding="utf-8").splitlines()
    except OSError:
        return _hover
    for line in lines:
        m = _ROW_RE.search(line)
        if not m:
            continue
        anchor, name, second, third = m.group(1), _plain(m.group(2)), _plain(m.group(3)), _plain(m.group(4))
        if anchor.startswith("w-"):  # the 7Ws: code | question | examples
            _hover[anchor] = f"{name}: {second} For example {third}."
        else:  # code | name | what it means | chapters
            _hover[anchor] = f"{second}: {third}" if third else second
    _hover.setdefault("c-unavailable", "Not met: the data does not support this code.")
    return _hover


def explain(code: "Code", suggested: bool = False) -> str:
    """Short hover text for a code: its name and meaning from the reference page."""
    hover = _load_hover()
    key = f"c-{code.base.lower()}" if code.struck else code.anchor
    text = _shorten(hover.get(key) or hover.get(code.anchor, ""))
    if not text:
        return ""
    if code.struck:
        text = f"Not met by the data. {text}"
    if suggested:
        text += " (Suggested by AI.)"
    elif code.base in MEASURED_ONLY:
        text += " (Measured from the data.)"
    return text


def _title(text: str) -> str:
    return f' title="{html.escape(text, quote=True)}"' if text else ""


@dataclass(frozen=True)
class Code:
    text: str  # as written, e.g. "C30", "[who]", "~~MD~~"
    anchor: str  # anchor on the reference page
    base: str  # e.g. "C", "W", "UOM", "SOURCE"
    struck: bool = False

    def link(self, prefix: str = "") -> str:
        label = self.text.replace("[", "\\[").replace("]", "\\]")
        tip = explain(self).replace('"', "'")
        return f"[{label}]({prefix}{PAGE}#{self.anchor}" + (f' "{tip}")' if tip else ")")


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


# ---- the same links as HTML, for the HTML tables (Markdown is not processed inside them) ----------

def _html_label(code: Code) -> str:
    text = code.text
    if code.struck:
        return f"<s>{html.escape(text[2:-2], quote=False)}</s>"
    return html.escape(text, quote=False)


def code_html(code: Code, prefix: str = "", italic: bool = False) -> str:
    link = f'<a href="{prefix}{PAGE}#{code.anchor}"{_title(explain(code, suggested=italic))}>{_html_label(code)}</a>'
    return f"<i>{link}</i>" if italic else link


def links_html(tokens: Sequence[str], scope: str, prefix: str = "", table_names: Iterable[str] = (),
               italic: bool = False) -> str:
    out = []
    for t in tokens:
        code = parse(t, scope, table_names)
        out.append(code_html(code, prefix, italic) if code else html.escape(t, quote=False))
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


def link_prose_html(text: str, prefix: str = "") -> str:
    """Like link_prose, for text that is already HTML-escaped and goes inside an HTML table."""
    def repl(m: "re.Match[str]") -> str:
        codes = []
        for p in (x.strip() for x in m.group(1).split(",")):
            if p.lower() in W_TYPES:
                codes.append(Code(f"[{p.lower()}]", f"w-{p.lower()}", "W"))
            elif p in TABLE_CODES:
                codes.append(Code(f"[{p}]", f"t-{p.lower()}", p))
            else:
                return m.group(0)
        if len(codes) == 1:
            return code_html(codes[0], prefix)
        inner = ", ".join(f'<a href="{prefix}{PAGE}#{c.anchor}"{_title(explain(c))}>{c.text.strip("[]")}</a>' for c in codes)
        return f"[{inner}]"

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
    if d.get("schema") and not table["name"].startswith(f"{d['schema']}."):  # already qualified: Sales.Customer
        return f"{{{d['schema']}.{table['name']}}}"
    return f"{{{table['name']}}}"


# ---- reference page ---------------------------------------------------------------

def copy_page(out_dir: Path) -> Path:
    if not ASSET.is_file():
        raise FileNotFoundError(f"BEAM reference page missing: {ASSET}")
    target = out_dir / PAGE
    shutil.copyfile(ASSET, target)
    return target
