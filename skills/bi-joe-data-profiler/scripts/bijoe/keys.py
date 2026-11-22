"""Measures what identifies a row: unique columns, unique combinations of columns, and how
identifier-like columns in the same table map onto each other (one-to-one or not).

Everything here is counted, never guessed. The agent reasons on the numbers: which column or
combination is the real key, whether two identifiers name the same thing, and what a
deviation means (a finer grain, duplicates, a data issue).

Only columns that could plausibly identify something are tried (identifier-like names, and dates
as the extra part of a combination), so the cost stays small.
"""

from __future__ import annotations

import itertools
import re
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

KEY_ROW_CAP = 50_000  # rows kept for key measurement; more than this is measured on the first rows
MAX_POOL = 8
MAX_COMBO = 3
ID_SUFFIXES = ("id", "key", "code", "no", "nr", "number", "num", "ref", "sku", "ssn", "vat", "cvr", "uuid", "guid")
DATE_TYPES = ("date", "datetime")


def _norm(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def _identifier_like(col: Dict[str, Any]) -> bool:
    return col["inferred_type"] in ("integer", "text") and _norm(col["name"]).endswith(ID_SUFFIXES)


def _clean(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def measure_keys(table: Dict[str, Any], rows: Sequence[Sequence[Any]]) -> Optional[Dict[str, Any]]:
    cols = table["columns"]
    n = len(rows)
    if n < 2 or not cols:
        return None
    ids = [i for i, c in enumerate(cols) if _identifier_like(c) and c["distinct_count"] >= 2]
    dates = [i for i, c in enumerate(cols) if c["inferred_type"] in DATE_TYPES and c["distinct_count"] >= 2]
    combo_pool = (ids + dates)[:MAX_POOL + 2]

    unique_columns = [c["name"] for c in cols if c.get("all_values_unique")]
    cleaned = [[_clean(v) for v in r] for r in rows]

    # Unique combinations, smallest first; a combination that contains a unique subset is skipped.
    unique_sets: List[Tuple[int, ...]] = []
    best: List[Tuple[float, Tuple[int, ...], int]] = []
    unique_idx = {i for i, c in enumerate(cols) if c.get("all_values_unique")}
    for size in range(2, MAX_COMBO + 1):
        for combo in itertools.combinations(combo_pool, size):
            if not any(i in ids for i in combo) or any(u in unique_idx for u in combo) or any(set(u) <= set(combo) for u in unique_sets):
                continue
            seen: Set[Tuple[Optional[str], ...]] = {tuple(r[i] for i in combo) for r in cleaned}
            if len(seen) == n:
                unique_sets.append(combo)
            else:
                best.append((len(seen) / n, combo, len(seen)))
    best.sort(key=lambda t: (-t[0], len(t[1])))
    non_unique = [{"columns": [cols[i]["name"] for i in combo], "distinct": distinct, "rows": n}
                  for _, combo, distinct in best[:5] if not any(set(u) <= set(combo) for u in unique_sets)]

    # How identifier-like columns relate to each other (same entity named twice, or a hierarchy).
    pairs = []
    id_pool = ids[:6]
    for a, b in itertools.combinations(id_pool, 2):
        a_to_b: Dict[str, Set[str]] = defaultdict(set)
        b_to_a: Dict[str, Set[str]] = defaultdict(set)
        for r in cleaned:
            if r[a] is not None and r[b] is not None:
                a_to_b[r[a]].add(r[b])
                b_to_a[r[b]].add(r[a])
        if not a_to_b:
            continue
        a_many = sum(1 for s in a_to_b.values() if len(s) > 1)
        b_many = sum(1 for s in b_to_a.values() if len(s) > 1)
        kind = ("one-to-one" if not a_many and not b_many else
                "many-to-one" if not a_many else "one-to-many" if not b_many else "many-to-many")
        pairs.append({"a": cols[a]["name"], "b": cols[b]["name"], "kind": kind,
                      "a_distinct": len(a_to_b), "b_distinct": len(b_to_a),
                      "a_with_several_b": a_many, "b_with_several_a": b_many})
    out = {
        "rows_checked": n,
        "sampled": n < table["row_count"],
        "unique_columns": unique_columns,
        "unique_combinations": [{"columns": [cols[i]["name"] for i in u], "rows": n} for u in unique_sets],
        "closest_combinations": non_unique,
        "identifier_pairs": pairs,
    }
    return out
