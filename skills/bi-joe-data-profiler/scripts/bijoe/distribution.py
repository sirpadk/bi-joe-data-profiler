"""Distributions: the bins, the counts, the shape, the outliers and the gaps of a column.

Everything here is counted from the values the profiler read, never guessed. The agent reasons on
the result (what a long right tail or a gap means), the wiki draws it as a small histogram.

Which columns get a chart is a judgement about relevance, not only about the data type:
  * numbers      -> a histogram with round bin edges, or one bar per value when there are few values
  * dates        -> a histogram by day, month, quarter, year or decade (birth dates: decades only)
  * categories   -> the most frequent values, with the rare ones folded into "Other"
  * not charted  -> unique keys, identifiers, free text, names and other personal data (only the
                    share of the most common value is kept, never the value)
"""

from __future__ import annotations

import datetime as dt
import math
from collections import Counter
from typing import Any, Dict, List, Optional, Sequence, Tuple

DISCRETE_LIMIT = 12  # up to this many distinct numbers: one bar per number
MIN_BINS, MAX_BINS = 8, 20
MAX_TIME_BINS = 40
CATEGORY_LIMIT = 30  # more distinct values than this is not a category
TOP_CATEGORIES = 10
SMALL_GROUP = 5  # a category with fewer rows than this is folded into "Other"
OUTLIER_FENCE = 1.5  # times the interquartile range (Tukey)

SHAPES = {
    "symmetric": "Symmetric: values cluster around the middle and thin out evenly on both sides.",
    "right-skewed": "Right-skewed: most values are low, with a long tail of a few high ones. The average is pulled above the median.",
    "left-skewed": "Left-skewed: most values are high, with a long tail of a few low ones. The average is pulled below the median.",
    "uniform": "Uniform: every range holds about the same number of rows, so no value or range is favoured.",
    "bimodal": "Bimodal: two separate peaks, which often means two different groups or processes in the data.",
    "multimodal": "Multimodal: several separate peaks, which often means several groups or processes in the data.",
    "one dominant value": "One dominant value: at least half of the rows share the same value.",
    "concentrated": "Concentrated: a few values hold most of the rows.",
    "evenly spread": "Evenly spread: the values occur about equally often.",
    "mixed": "Mixed: some values are common and others rare, without a clear pattern.",
}


# ---- small helpers ----------------------------------------------------------------

def quantile(sorted_values: Sequence[float], q: float) -> float:
    pos = (len(sorted_values) - 1) * q
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def _skewness(values: Sequence[float]) -> float:
    n = len(values)
    mean = sum(values) / n
    m2 = sum((v - mean) ** 2 for v in values) / n
    if m2 <= 0:
        return 0.0
    m3 = sum((v - mean) ** 3 for v in values) / n
    return m3 / m2 ** 1.5


def _nice_step(raw: float) -> float:
    if raw <= 0:
        return 1.0
    exp = math.floor(math.log10(raw))
    base = raw / 10 ** exp
    for m in (1, 2, 2.5, 5, 10):
        if base <= m:
            return m * 10 ** exp
    return 10 ** (exp + 1)


def _fmt(x: float, step: float = 1.0) -> str:
    decimals = max(0, -int(math.floor(math.log10(step)))) if step > 0 else 0
    if abs(x) >= 1000 and decimals == 0:
        return f"{x:,.0f}"
    text = f"{x:.{min(decimals + 1, 6)}f}".rstrip("0").rstrip(".")
    return text or "0"


def _modes(counts: Sequence[int]) -> int:
    """Number of separate peaks in a list of bin counts (lightly smoothed; shallow dips do not count)."""
    n = len(counts)
    if n < 3:
        return 1
    smooth = [(counts[max(i - 1, 0)] + 2 * counts[i] + counts[min(i + 1, n - 1)]) / 4 for i in range(n)]
    top = max(smooth)
    if top <= 0:
        return 0
    peaks = []
    for i in range(n):
        left = smooth[i - 1] if i else -1.0
        right = smooth[i + 1] if i < n - 1 else -1.0
        if smooth[i] >= 0.25 * top and smooth[i] >= left and smooth[i] >= right:
            peaks.append(i)
    kept: List[int] = []
    for p in peaks:
        if kept:
            valley = min(smooth[kept[-1]:p + 1])
            if valley >= 0.6 * min(smooth[kept[-1]], smooth[p]):  # barely a dip: the same peak
                if smooth[p] > smooth[kept[-1]]:
                    kept[-1] = p
                continue
        kept.append(p)
    return max(len(kept), 1)


def _shape(counts: Sequence[int], values: Optional[Sequence[float]], top_share: float) -> str:
    if top_share >= 0.5:
        return "one dominant value"
    modes = _modes(counts)
    if modes == 2:
        return "bimodal"
    if modes >= 3:
        return "multimodal"
    nonzero = [c for c in counts if c]
    if len(counts) >= 5 and len(nonzero) == len(counts):
        mean = sum(counts) / len(counts)
        sd = math.sqrt(sum((c - mean) ** 2 for c in counts) / len(counts))
        if mean and sd / mean <= 0.3:
            return "uniform"
    skew = _skewness(values) if values else 0.0
    if skew >= 0.5:
        return "right-skewed"
    if skew <= -0.5:
        return "left-skewed"
    return "symmetric"


def _gaps(counts: Sequence[int]) -> Tuple[List[bool], int]:
    """Flags for empty bins that sit between filled ones, and the number of separate gaps."""
    filled = [i for i, c in enumerate(counts) if c]
    flags = [False] * len(counts)
    if len(filled) < 2:
        return flags, 0
    runs, in_run = 0, False
    for i in range(filled[0], filled[-1] + 1):
        if counts[i] == 0:
            flags[i] = True
            if not in_run:
                runs += 1
            in_run = True
        else:
            in_run = False
    return flags, runs


def _bin(label: str, lo: Any, hi: Any, count: int, n: int, **flags: bool) -> Dict[str, Any]:
    out: Dict[str, Any] = {"label": label, "from": lo, "to": hi, "count": count,
                           "pct": round(100 * count / n, 2) if n else 0}
    out.update({k: True for k, v in flags.items() if v})
    return out


# ---- numbers -----------------------------------------------------------------------

def numeric(values: List[float], integer: bool) -> Optional[Dict[str, Any]]:
    n = len(values)
    if n < 2:
        return None
    vs = sorted(values)
    lo, hi = vs[0], vs[-1]
    if lo == hi:
        return None
    q1, med, q3 = quantile(vs, 0.25), quantile(vs, 0.5), quantile(vs, 0.75)
    iqr = q3 - q1
    low_fence, high_fence = q1 - OUTLIER_FENCE * iqr, q3 + OUTLIER_FENCE * iqr
    below = sum(1 for v in vs if v < low_fence) if iqr > 0 else 0
    above = sum(1 for v in vs if v > high_fence) if iqr > 0 else 0
    top_share = Counter(vs).most_common(1)[0][1] / n
    distinct = sorted(set(vs))

    bins: List[Dict[str, Any]]
    if len(distinct) <= DISCRETE_LIMIT:
        kind, counts = "discrete", Counter(vs)
        bins = [_bin(_fmt(v), v, v, counts[v], n) for v in distinct]
        main_counts = [counts[v] for v in distinct]
        if integer:
            full = range(int(distinct[0]), int(distinct[-1]) + 1)
            if len(full) <= 3 * DISCRETE_LIMIT:
                bins = [_bin(str(v), v, v, counts.get(v, 0), n) for v in full]
                main_counts = [counts.get(v, 0) for v in full]
        step = 1.0
    else:
        kind = "numeric"
        clip_lo = max(lo, low_fence) if below else lo
        clip_hi = min(hi, high_fence) if above else hi
        inside = [v for v in vs if clip_lo <= v <= clip_hi]
        if iqr > 0:
            width = 2 * iqr / (n ** (1 / 3))
            target = (clip_hi - clip_lo) / width if width > 0 else MAX_BINS
        else:
            target = math.log2(n) + 1
        target = max(MIN_BINS, min(MAX_BINS, int(round(target))))
        step = _nice_step((clip_hi - clip_lo) / target)
        if integer:
            step = max(step, 1.0)
        start = math.floor(clip_lo / step) * step
        nb = max(1, int(math.ceil((clip_hi - start) / step - 1e-9)))
        counts_list = [0] * nb
        for v in inside:
            counts_list[min(int((v - start) / step), nb - 1)] += 1
        bins = []
        for i, c in enumerate(counts_list):
            a, b = start + i * step, start + (i + 1) * step
            label = _fmt(a, step) if (integer and step == 1) else f"{_fmt(a, step)}–{_fmt(b - 1 if integer else b, step)}"
            bins.append(_bin(label, a, b, c, n))
        main_counts = list(counts_list)
        if below:
            bins.insert(0, _bin(f"below {_fmt(start, step)}", None, start, below, n, outlier=True))
        if above:
            end = start + nb * step
            bins.append(_bin(f"above {_fmt(end, step)}", end, None, above, n, outlier=True))

    gap_flags, gap_runs = _gaps(main_counts)
    offset = 1 if (kind == "numeric" and below) else 0
    for i, g in enumerate(gap_flags):
        if g:
            bins[i + offset]["gap"] = True
    shape = _shape(main_counts, vs if len(vs) <= 100_000 else None, top_share)
    return {
        "kind": kind, "bins": bins, "bin_width": step if kind == "numeric" else None, "values": n,
        "shape": shape, "skewness": round(_skewness(vs), 2),
        "median": med, "q1": q1, "q3": q3, "iqr": iqr,
        "outliers": {"below": below, "above": above, "low_fence": low_fence, "high_fence": high_fence} if (below or above) else None,
        "gap_runs": gap_runs, "gap_bins": sum(gap_flags),
        "top_share_pct": round(100 * top_share, 1),
    }


# ---- dates -------------------------------------------------------------------------

def _month_index(d: dt.date) -> int:
    return d.year * 12 + d.month - 1


def dates(ordinals: List[int], decades_only: bool = False) -> Optional[Dict[str, Any]]:
    n = len(ordinals)
    if n < 2:
        return None
    days = sorted(ordinals)
    first, last = dt.date.fromordinal(days[0]), dt.date.fromordinal(days[-1])
    if first == last:
        return None
    span_days = days[-1] - days[0]
    months = _month_index(last) - _month_index(first) + 1
    if decades_only:
        unit = "decade"
    elif span_days <= 45:
        unit = "day"
    elif months <= 30:
        unit = "month"
    elif months <= 120:
        unit = "quarter"
    elif last.year - first.year <= 40:
        unit = "year"
    else:
        unit = "decade"

    def index(d: dt.date) -> int:
        return {"day": d.toordinal(), "month": _month_index(d), "quarter": d.year * 4 + (d.month - 1) // 3,
                "year": d.year, "decade": d.year // 10}[unit]

    def label(i: int) -> str:
        if unit == "day":
            return dt.date.fromordinal(i).isoformat()
        if unit == "month":
            return f"{i // 12}-{i % 12 + 1:02d}"
        if unit == "quarter":
            return f"{i // 4} Q{i % 4 + 1}"
        if unit == "year":
            return str(i)
        return f"{i * 10}s"

    counts = Counter(index(dt.date.fromordinal(o)) for o in days)
    lo, hi = min(counts), max(counts)
    idx = list(range(lo, hi + 1))
    main_counts = [counts.get(i, 0) for i in idx]
    if len(idx) > MAX_TIME_BINS:  # still too many: merge neighbouring bins
        k = int(math.ceil(len(idx) / MAX_TIME_BINS))
        idx = idx[::k]
        main_counts = [sum(counts.get(j, 0) for j in range(i, i + k)) for i in idx]
    gap_flags, gap_runs = _gaps(main_counts)
    bins = [_bin(label(i), label(i), label(i), c, n, gap=g) for i, c, g in zip(idx, main_counts, gap_flags)]
    top_share = max(counts.values()) / n
    skew = _skewness([float(o) for o in days]) if n <= 100_000 else 0.0
    shape = _shape(main_counts, [float(o) for o in days] if n <= 100_000 else None, 0.0)
    return {
        "kind": "time", "unit": unit, "bins": bins, "values": n, "shape": shape, "skewness": round(skew, 2),
        "gap_runs": gap_runs, "gap_bins": sum(gap_flags),
        "top_share_pct": round(100 * top_share, 1),
    }


# ---- categories ----------------------------------------------------------------------

def categories(counter: Counter, n: int) -> Optional[Dict[str, Any]]:
    if n < 2 or len(counter) < 2 or len(counter) > CATEGORY_LIMIT:
        return None
    ranked = counter.most_common()
    shown, other, other_values = [], 0, 0
    for i, (value, c) in enumerate(ranked):
        if i < TOP_CATEGORIES and c >= SMALL_GROUP:
            shown.append(_bin(value if len(value) <= 40 else value[:39] + "…", value, value, c, n))
        else:
            other += c
            other_values += 1
    if other:
        shown.append(_bin(f"Other ({other_values} values)", None, None, other, n, other_group=True))
    top = ranked[0][1] / n
    counts = [c for _, c in ranked]
    top3 = sum(counts[:3]) / n
    if top >= 0.5:
        shape = "one dominant value"
    elif top3 >= 0.8 and len(counts) > 3:
        shape = "concentrated"
    elif max(counts) <= 2 * min(counts):
        shape = "evenly spread"
    else:
        shape = "mixed"
    return {"kind": "categories", "bins": shown, "values": n, "distinct": len(counter), "shape": shape,
            "top_share_pct": round(100 * top, 1)}
