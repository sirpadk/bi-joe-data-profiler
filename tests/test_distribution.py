"""Distributions: bins, shape, outliers, gaps, and which columns deserve a chart."""

import datetime as dt
import json
import random
from collections import Counter

from bijoe import distribution as d
from bijoe.cli import main


def _rng():
    return random.Random(7)


def test_shapes_are_recognised():
    r = _rng()
    assert d.numeric([r.gauss(50, 10) for _ in range(3000)], False)["shape"] == "symmetric"
    assert d.numeric([r.expovariate(1 / 1000) for _ in range(3000)], False)["shape"] == "right-skewed"
    assert d.numeric([1000 - r.expovariate(1 / 200) for _ in range(3000)], False)["shape"] == "left-skewed"
    assert d.numeric([r.uniform(0, 100) for _ in range(3000)], False)["shape"] == "uniform"
    two = [r.gauss(20, 3) for _ in range(1500)] + [r.gauss(60, 4) for _ in range(1500)]
    assert d.numeric(two, False)["shape"] == "bimodal"
    assert d.numeric([0.0] * 2000 + [5.0] * 300 + [10.0] * 200, False)["shape"] == "one dominant value"


def test_bins_have_round_edges_and_counts_add_up():
    r = _rng()
    values = [r.gauss(50, 10) for _ in range(2000)]
    out = d.numeric(values, False)
    assert out["kind"] == "numeric" and MIN_BINS <= len(out["bins"]) <= MAX_BINS + 2
    assert sum(b["count"] for b in out["bins"]) == len(values)
    step = out["bin_width"]
    assert step in (1, 2, 2.5, 5, 10, 20, 25, 50)  # a round width
    few = d.numeric([float(r.randint(1, 5)) for _ in range(500)], True)
    assert few["kind"] == "discrete" and [b["label"] for b in few["bins"]] == ["1", "2", "3", "4", "5"]


MIN_BINS, MAX_BINS = d.MIN_BINS, d.MAX_BINS


def test_outliers_are_clipped_into_their_own_bin_and_gaps_are_flagged():
    r = _rng()
    out = d.numeric([r.gauss(100, 10) for _ in range(500)] + [900.0, 1200.0, 1500.0], False)
    assert out["outliers"]["above"] >= 3
    assert out["bins"][-1].get("outlier") and out["bins"][-1]["label"].startswith("above")
    assert out["bins"][-1]["count"] == out["outliers"]["above"]
    base = dt.date(2023, 1, 1).toordinal()
    days = [base + r.randint(0, 100) for _ in range(400)] + [base + r.randint(300, 400) for _ in range(400)]
    t = d.dates(days)
    assert t["unit"] == "month" and t["gap_runs"] == 1 and any(b.get("gap") for b in t["bins"])


def test_dates_pick_a_sensible_unit_and_birth_dates_use_decades():
    base = dt.date(1960, 1, 1).toordinal()
    days = [base + i * 30 for i in range(600)]
    assert d.dates(days)["unit"] in ("year", "decade")
    births = d.dates(days, decades_only=True)
    assert births["unit"] == "decade" and births["bins"][0]["label"].endswith("0s")


def test_categories_fold_small_groups_and_cap_the_labels():
    c = Counter({"Aarhus": 500, "Odense": 200, "Esbjerg": 50, "Rare": 2, "Tiny": 1})
    out = d.categories(c, 753)
    labels = [b["label"] for b in out["bins"]]
    assert labels[:3] == ["Aarhus", "Odense", "Esbjerg"] and labels[-1].startswith("Other (2 values)")
    assert "Rare" not in labels and out["shape"] == "one dominant value"
    assert d.categories(Counter({str(i): 5 for i in range(40)}), 200) is None  # too many for a chart


def test_only_relevant_columns_are_charted(tmp_path):
    r = _rng()
    rows = ["RowID,Amount,City,Zip,Email,BirthDate,Status"]
    for i in range(400):
        rows.append(f"{i},{round(r.expovariate(1 / 500), 2)},{r.choice(['Aarhus'] * 5 + ['Odense'] * 2 + ['Esbjerg'])},"
                    f"{r.choice([8000, 8000, 5000, 6700])},u{i}@example.dk,19{50 + i % 40}-0{1 + i % 9}-1{i % 9},{r.choice(['Open', 'Closed'])}")
    src = tmp_path / "t.csv"
    src.write_text("\n".join(rows), encoding="utf-8")
    out = tmp_path / "wiki"
    main(["profile", str(src), "--out", str(out)])
    profile = json.loads((out / "_bijoe" / "profile.json").read_text(encoding="utf-8"))
    cols = {c["name"]: c.get("distribution") for c in profile["tables"][0]["columns"]}
    assert cols["RowID"] is None  # unique: a key, not a distribution
    assert cols["Amount"]["kind"] == "numeric" and cols["Amount"]["shape"] == "right-skewed"
    assert cols["City"]["kind"] == "categories" and cols["City"]["bins"][0]["label"] == "Aarhus"
    assert cols["Zip"]["kind"] == "categories"  # a zip code is a label, not a quantity
    assert cols["Email"] == {"kind": "none", "reason": "personal data", "top_share_pct": 0.2} or cols["Email"]["kind"] == "none"
    assert "u1@example" not in json.dumps(cols)
    assert cols["BirthDate"]["unit"] == "decade"
    story = (out / "data-stories" / "t.md").read_text(encoding="utf-8")
    assert "Distribution" in story and "Aarhus" in story and 'title="Aarhus:' in story
    assert "not charted: personal data" in story


def test_no_values_keeps_numbers_but_drops_category_labels(tmp_path):
    src = tmp_path / "t.csv"
    src.write_text("Id,Amount,City\n" + "\n".join(f"{i},{i % 50},{'A' if i % 3 else 'B'}" for i in range(300)), encoding="utf-8")
    out = tmp_path / "wiki"
    main(["profile", str(src), "--out", str(out), "--no-values"])
    cols = {c["name"]: c.get("distribution") for c in json.loads(
        (out / "_bijoe" / "profile.json").read_text(encoding="utf-8"))["tables"][0]["columns"]}
    assert cols["Amount"] and cols["City"] is None
