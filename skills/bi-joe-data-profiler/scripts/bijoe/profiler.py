"""Turns rows from any connector into facts: per-table and per-column statistics.

The output is evidence for the person or LLM writing the data stories, so every
number here is measured, never guessed. Works on text values (CSV) and native
values (databases, Excel) alike, with the standard library only.
"""

from __future__ import annotations

import datetime as dt
import decimal
import hashlib
import math
import re
from collections import Counter
from typing import Any, Callable, Dict, List, Optional, Tuple

from .connectors.base import Connector, TableInfo

INT_RE = re.compile(r"^[+-]?\d+$")
DEC_RE = re.compile(r"^[+-]?(\d+\.\d*|\.\d+|\d+)([eE][+-]?\d+)?$")
TRUE_WORDS = {"true", "yes", "y", "t"}
BOOL_WORDS = TRUE_WORDS | {"false", "no", "n", "f"}
DATE_FORMATS = ["%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%m/%d/%Y", "%d.%m.%Y", "%d-%m-%Y"]
DATETIME_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d/%m/%Y %H:%M",
    "%m/%d/%Y %H:%M:%S",
    "%m/%d/%Y %H:%M",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y %H:%M",
]

# Most specific first. A column gets the first type that >= TYPE_THRESHOLD of its values fit.
TYPE_ORDER = ["boolean", "integer", "decimal", "date", "datetime", "time", "binary"]
COMPATIBLE = {
    "boolean": {"boolean"},
    "integer": {"integer"},
    "decimal": {"integer", "decimal"},
    "date": {"date"},
    "datetime": {"date", "datetime"},
    "time": {"time"},
    "binary": {"binary"},
}
TYPE_THRESHOLD = 0.95
TOP_N = 5
MAX_VALUE_CHARS = 60
MAX_KEY_CHARS = 200


def _to_naive(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is not None:
        return value.astimezone(dt.timezone.utc).replace(tzinfo=None)
    return value


class ColumnStats:
    def __init__(self, name: str, position: int, declared_type: Optional[str] = None,
                 comment: Optional[str] = None, primary_key: bool = False,
                 nullable: Optional[bool] = None) -> None:
        self.name = name
        self.position = position
        self.declared_type = declared_type
        self.comment = comment
        self.primary_key = primary_key
        self.nullable = nullable
        self.n = 0
        self.nulls = 0
        self.blanks = 0
        self.padded = 0
        self.leading_zero = 0
        self.bool_letters = 0
        self.int_digits = 0
        self.scale = 0
        self.types: Counter = Counter()
        self.values: Counter = Counter()
        self.formats: Counter = Counter()
        self._last_fmt: Optional[str] = None
        self.num_min: Optional[float] = None
        self.num_max: Optional[float] = None
        self.num_sum = 0.0
        self.num_count = 0
        self.t_min: Optional[dt.datetime] = None
        self.t_max: Optional[dt.datetime] = None
        self.len_min: Optional[int] = None
        self.len_max: Optional[int] = None

    # ---- classification ----------------------------------------------------
    def _try_formats(self, s: str, formats: List[str]) -> Optional[Tuple[dt.datetime, str]]:
        order = formats
        if self._last_fmt in formats:
            order = [self._last_fmt] + [f for f in formats if f != self._last_fmt]
        for fmt in order:
            try:
                value = dt.datetime.strptime(s, fmt)
            except ValueError:
                continue
            self._last_fmt = fmt
            return value, fmt
        return None

    def _classify_str(self, s: str) -> Tuple[str, Any, Optional[str]]:
        low = s.lower()
        if low in BOOL_WORDS:
            if len(low) == 1:
                self.bool_letters += 1  # "F" may be a code (gender, size) rather than false; settled in result()
            return "boolean", low in TRUE_WORDS, None
        if INT_RE.match(s):
            try:
                return "integer", int(s), None
            except ValueError:
                return "text", s, None
        if DEC_RE.match(s):
            f = float(s)
            if math.isfinite(f):
                return "decimal", f, None
        if s[0].isdigit():
            if 6 <= len(s) <= 10:
                hit = self._try_formats(s, DATE_FORMATS)
                if hit:
                    return "date", hit[0], hit[1]
            if len(s) >= 12:
                try:
                    return "datetime", _to_naive(dt.datetime.fromisoformat(s.replace("Z", "+00:00"))), "ISO 8601"
                except ValueError:
                    pass
                hit = self._try_formats(s, DATETIME_FORMATS)
                if hit:
                    return "datetime", hit[0], hit[1]
        return "text", s, None

    @staticmethod
    def _classify_native(v: Any) -> Tuple[str, Any, str]:
        if isinstance(v, bool):
            return "boolean", v, str(v)
        if isinstance(v, int):
            return "integer", v, str(v)
        if isinstance(v, (float, decimal.Decimal)):
            return "decimal", float(v), str(v)
        if isinstance(v, dt.datetime):
            if v.time() == dt.time(0) and v.tzinfo is None:  # Excel stores plain dates as midnight datetimes
                return "date", v, v.date().isoformat()
            return "datetime", _to_naive(v), v.isoformat(sep=" ")
        if isinstance(v, dt.date):
            return "date", dt.datetime(v.year, v.month, v.day), v.isoformat()
        if isinstance(v, dt.time):
            return "time", v, v.isoformat()
        if isinstance(v, (bytes, bytearray, memoryview)):
            return "binary", None, f"<{len(bytes(v))} bytes>"
        return "text", str(v), str(v)

    # ---- accumulation ------------------------------------------------------
    def add(self, v: Any) -> None:
        self.n += 1
        if v is None or (isinstance(v, float) and math.isnan(v)):
            self.nulls += 1
            return
        fmt = None
        if isinstance(v, str):
            s = v.strip()
            if not s:
                self.blanks += 1
                return
            if s != v:
                self.padded += 1
            kind, value, fmt = self._classify_str(s)
            if kind == "integer":
                digits = s.lstrip("+-")
                if len(digits) > 1 and digits[0] == "0":
                    self.leading_zero += 1
            key = s
        else:
            kind, value, key = self._classify_native(v)
        self.types[kind] += 1
        if fmt:
            self.formats[fmt] += 1
        self.values[key[:MAX_KEY_CHARS]] += 1
        length = len(key)
        self.len_min = length if self.len_min is None else min(self.len_min, length)
        self.len_max = length if self.len_max is None else max(self.len_max, length)
        if kind == "decimal" and "e" not in key.lower():
            whole, _, frac = key.lstrip("+-").partition(".")
            frac = frac.rstrip("0") if isinstance(v, float) else frac  # floats: 5.10 prints as 5.1 anyway
            self.int_digits = max(self.int_digits, len(whole.lstrip("0")) or 1)
            self.scale = max(self.scale, min(len(frac), 10))
        elif kind == "integer":
            self.int_digits = max(self.int_digits, len(key.lstrip("+-").lstrip("0")) or 1)
        if kind in ("integer", "decimal"):
            self.num_min = value if self.num_min is None else min(self.num_min, value)
            self.num_max = value if self.num_max is None else max(self.num_max, value)
            self.num_sum += float(value)
            self.num_count += 1
        elif kind in ("date", "datetime"):
            self.t_min = value if self.t_min is None else min(self.t_min, value)
            self.t_max = value if self.t_max is None else max(self.t_max, value)

    # ---- results -----------------------------------------------------------
    def result(self, include_values: bool = True) -> Dict[str, Any]:
        non_missing = self.n - self.nulls - self.blanks
        types = Counter(self.types)
        inferred = "empty"
        consistency: Optional[float] = None
        if non_missing:
            inferred = "text"
            for t in TYPE_ORDER:
                fits = sum(types[x] for x in COMPATIBLE[t])
                if fits / non_missing >= TYPE_THRESHOLD:
                    inferred, consistency = t, fits / non_missing
                    break
        if inferred != "boolean" and self.bool_letters:
            # Not a yes/no column, so single letters like "F" were codes, not booleans.
            types["boolean"] -= self.bool_letters
            types["text"] += self.bool_letters
            types = +types  # drop zero counts
            if inferred != "text":
                fits = sum(types[x] for x in COMPATIBLE[inferred])
                consistency = fits / non_missing
        allowed = COMPATIBLE.get(inferred, {inferred})
        unexpected = {k for k in types if k not in allowed}
        out: Dict[str, Any] = {
            "name": self.name,
            "position": self.position,
            "declared_type": self.declared_type,
            "primary_key": self.primary_key or None,
            "nullable": self.nullable,
            "comment": self.comment,
            "inferred_type": inferred,
            "type_consistency_pct": None if consistency is None or consistency == 1 else round(100 * consistency, 2),
            # Only report the mix when some values don't fit the column's type (ints in a decimal column are fine).
            "value_kinds": dict(types) if unexpected else None,
            "missing_count": self.nulls + self.blanks,
            "missing_pct": round(100 * (self.nulls + self.blanks) / self.n, 2) if self.n else None,
            "null_count": self.nulls,
            "blank_count": self.blanks,
            "distinct_count": len(self.values),
            "all_values_unique": bool(non_missing) and len(self.values) == non_missing,
        }
        if inferred in ("integer", "decimal") and self.num_count:
            out["min"] = self.num_min
            out["max"] = self.num_max
            out["mean"] = round(self.num_sum / self.num_count, 4)
            if inferred == "decimal":
                out["precision"] = self.int_digits + self.scale
                out["scale"] = self.scale
        elif inferred in ("date", "datetime") and self.t_min is not None:
            as_date = inferred == "date"
            out["min"] = self.t_min.date().isoformat() if as_date else self.t_min.isoformat(sep=" ")
            out["max"] = self.t_max.date().isoformat() if as_date else self.t_max.isoformat(sep=" ")
            if self.formats:
                out["value_formats"] = [f for f, _ in self.formats.most_common(3)]
        elif inferred == "text" and self.len_min is not None:
            out["min_length"] = self.len_min
            out["max_length"] = self.len_max
        if self.leading_zero:
            out["leading_zero_count"] = self.leading_zero
        if self.padded:
            out["whitespace_padded_count"] = self.padded
        if include_values and self.values:
            out["top_values"] = [
                {"value": v if len(v) <= MAX_VALUE_CHARS else v[: MAX_VALUE_CHARS - 1] + "…", "count": c}
                for v, c in self.values.most_common(TOP_N)
            ]
        return {k: v for k, v in out.items() if v is not None}


def profile_table(connector: Connector, table: str, sample_rows: int, include_values: bool = True,
                  info: Optional[TableInfo] = None) -> Dict[str, Any]:
    return _profile_table(connector, table, sample_rows, include_values, info)[0]


def _profile_table(connector: Connector, table: str, sample_rows: int, include_values: bool = True,
                   info: Optional[TableInfo] = None) -> Tuple[Dict[str, Any], List[ColumnStats]]:
    info = info or connector.describe_table(table)
    stats = [
        ColumnStats(c.name, i + 1, c.declared_type, c.comment, c.primary_key, c.nullable)
        for i, c in enumerate(info.columns)
    ]
    width = len(stats)
    # If the source told us the row count, read only the sample; otherwise read everything to count.
    limit = sample_rows if info.row_count is not None else None
    seen: set = set()
    duplicates = ragged = profiled = total = 0
    for row in connector.iter_rows(table, limit=limit):
        total += 1
        if profiled >= sample_rows:
            continue
        profiled += 1
        row = list(row)
        if len(row) != width:
            ragged += 1
            row = (row + [None] * width)[:width]
        digest = hashlib.blake2b(repr(row).encode("utf-8", "replace"), digest_size=16).digest()
        if digest in seen:
            duplicates += 1
        else:
            seen.add(digest)
        for col, value in zip(stats, row):
            col.add(value)
    row_count = info.row_count if info.row_count is not None else total
    result: Dict[str, Any] = {
        "name": table,
        "comment": info.comment,
        "row_count": row_count,
        "profiled_rows": profiled,
        "sampled": profiled < row_count,
        "column_count": width,
        "duplicate_rows": duplicates,
        "ragged_rows": ragged or None,
        "details": info.details or None,
        "columns": [c.result(include_values) for c in stats],
    }
    return {k: v for k, v in result.items() if v is not None}, stats


# ---- relationships --------------------------------------------------------------

def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _key_names(table: str, column: str) -> List[str]:
    """Names a column pointing at table.column could have: StoreID, store_id, StoresID..."""
    col = _norm(column)
    names = {col}
    if col in ("id", "key", "code", "no", "number"):
        t = _norm(table)
        names |= {t + col, t.rstrip("s") + col}
    return [n for n in names if len(n) >= 3]


def find_relationships(profiled: List[Tuple[Dict[str, Any], List[ColumnStats]]],
                       min_coverage: float = 0.5) -> List[Dict[str, Any]]:
    """Measure links between tables: a column whose name matches another table's unique key
    (StoreID, PreferredStoreID → Stores.StoreID) and whose values are found there."""
    targets = []
    for table, stats in profiled:
        for st, col in zip(stats, table["columns"]):
            if col.get("all_values_unique") and not col.get("missing_count") and col["distinct_count"] >= 2 \
                    and col["inferred_type"] in ("integer", "text"):
                targets.append((table, st, col, _key_names(table["name"], col["name"])))
    found = []
    for table, stats in profiled:
        for st, col in zip(stats, table["columns"]):
            non_missing = st.n - st.nulls - st.blanks
            if not non_missing:
                continue
            src = _norm(col["name"])
            for t_table, t_st, t_col, names in targets:
                if t_table["name"] == table["name"] and t_col["name"] == col["name"]:
                    continue
                if not any(src == n or (src.endswith(n) and len(n) >= 4) for n in names):
                    continue
                if col.get("all_values_unique") and t_table["name"] != table["name"] \
                        and table["row_count"] > t_table["row_count"]:
                    continue  # 1:1 link: report it once, from the smaller table
                matched = sum(c for v, c in st.values.items() if v in t_st.values)
                coverage = matched / non_missing
                if coverage < min_coverage:
                    continue
                found.append({
                    "from_table": table["name"], "from_column": col["name"],
                    "to_table": t_table["name"], "to_column": t_col["name"],
                    "matched_values": matched, "checked_values": non_missing,
                    "coverage_pct": round(100 * coverage, 2),
                    "sampled": bool(table.get("sampled") or t_table.get("sampled")),
                })
    return found


def profile_dataset(connector: Connector, tables: Optional[List[str]] = None, sample_rows: int = 100_000,
                    include_values: bool = True, progress: Optional[Callable[[str], None]] = None
                    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    names = connector.list_tables()
    if tables:
        wanted = {t.lower() for t in tables}
        names = [n for n in names if n.lower() in wanted]
    profiled = []
    for name in names:
        if progress:
            progress(name)
        profiled.append(_profile_table(connector, name, sample_rows, include_values))
    return [t for t, _ in profiled], find_relationships(profiled)


def profile_source(connector: Connector, tables: Optional[List[str]] = None, sample_rows: int = 100_000,
                   include_values: bool = True,
                   progress: Optional[Callable[[str], None]] = None) -> List[Dict[str, Any]]:
    return profile_dataset(connector, tables, sample_rows, include_values, progress)[0]
