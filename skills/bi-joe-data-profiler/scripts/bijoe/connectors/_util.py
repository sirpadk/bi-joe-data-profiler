from __future__ import annotations

from typing import Iterable, List


def unique_names(raw: Iterable[object]) -> List[str]:
    """Clean header names: blank -> column_N, duplicates -> name_2, name_3..."""
    names: List[str] = []
    seen: set = set()
    for i, value in enumerate(raw):
        base = ("" if value is None else str(value)).strip() or f"column_{i + 1}"
        name, n = base, 2
        while name.lower() in seen:
            name = f"{base}_{n}"
            n += 1
        seen.add(name.lower())
        names.append(name)
    return names
