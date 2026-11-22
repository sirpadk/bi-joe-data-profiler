"""Small helpers for reading the HTML tables the wiki writes."""

import html
import re
from typing import Any, Dict, List, Optional


def strip(s: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def property_rows(page: str) -> Dict[str, str]:
    """label -> value (HTML) for the property table at the top of a page."""
    return {strip(label): value for label, value in
            re.findall(r'<th scope="row"[^>]*>(.*?)</th><td[^>]*>(.*?)</td>', page, re.S)}


def matrix(page: str) -> List[Dict[str, Any]]:
    """The columns matrix as a list of rows: {"label", "group", "cells": [(attrs, content)]}."""
    m = re.search(r'<table style="border-collapse:separate.*?</table>\s*</div>', page, re.S)
    assert m, "no columns matrix found"
    # the mini histograms are tables inside cells: leave them out when reading the matrix rows
    nested = re.sub(r'<table style="border-collapse:collapse;border:0.*?</table>', "", m.group(0), flags=re.S)
    rows: List[Dict[str, Any]] = []
    group: Optional[str] = None
    remaining = 0
    for tr in re.findall(r"<tr>(.*?)</tr>", nested, re.S):
        cells = [(a, c) for _, a, c in re.findall(r"<(td|th)\b([^>]*)>(.*?)</\1>", tr, re.S)]
        i = 0
        if "background:transparent" in cells[0][0]:  # the empty corner above the group column
            cells = cells[1:]
            label_row = True
        else:
            label_row = False
        if label_row or (len(rows) < 3 and "rowspan" not in cells[0][0]):
            label, data, row_group = strip(cells[0][1]), cells[1:], None
        else:
            if "rowspan" in cells[0][0]:
                group = strip(cells[0][1])
                remaining = int(re.search(r'rowspan="(\d+)"', cells[0][0]).group(1))
                i = 1
            label, data, row_group = strip(cells[i][1]), cells[i + 1:], group
            remaining -= 1
            if remaining <= 0:
                group = None
        rows.append({"label": label, "group": row_group, "cells": data})
    return rows


def matrix_row(page: str, label: str, group: Optional[str] = None) -> List[str]:
    """Plain text of the data cells of the first matrix row with this label (and group)."""
    for row in matrix(page):
        if row["label"] == label and (group is None or row["group"] == group):
            return [strip(c) for _, c in row["cells"]]
    raise AssertionError(f"matrix row {label!r} not found")


def headings(page: str) -> List[str]:
    """Markdown headings outside code fences, as written (without the # marks)."""
    out, fenced = [], False
    for line in page.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"^#{1,6} ", line):
            out.append(line.lstrip("#").strip())
    return out


def notitle(s: str) -> str:
    """Drop the hover text (title="...") so assertions can focus on links and structure."""
    s = re.sub(r' title="[^"]*"', "", s)
    s = re.sub(r'(<a [^>]*?) style="color:[^"]*"', lambda m: m.group(1), s)  # theme link colour
    return re.sub(r'(\]\([^)\s"]+) "[^"]*"\)', lambda m: m.group(1) + ")", s)  # Markdown link titles


def unframe(page: str) -> str:
    """The page without the themed wrapper div."""
    lines = page.rstrip().split("\n")
    if lines and lines[0].startswith('<div style="background:'):
        lines = lines[1:]
    if lines and lines[-1].strip() == "</div>":
        lines = lines[:-1]
    return "\n".join(lines).strip("\n") + "\n"
