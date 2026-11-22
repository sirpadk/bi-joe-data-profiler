import copy
import json
import re
from pathlib import Path

import pytest

from htmlutil import unframe
from progress_stub import ProgressStub

from bijoe import descriptions, wiki
from bijoe.cli import main
from bijoe.wiki import fmt_seconds

STORY_FOOTER = re.compile(r"^<i>Profiled in .+\.</i>$", re.M)
INDEX_FOOTER = re.compile(r"^<i>Profiling took .+\.</i>$", re.M)
SCHEMA_FOOTER = re.compile(r"^<i>Its tables took .+ to profile\.</i>$", re.M)


@pytest.mark.parametrize("value,expected", [
    (0, "<0.1 s"), (0.05, "<0.1 s"), (0.0999, "<0.1 s"), (0.1, "0.1 s"), (4.2, "4.2 s"),
    (9.94, "9.9 s"), (10, "10 s"), (42.0, "42 s"), (59.4, "59 s"),
    (59.6, "1 min 0 s"), (60, "1 min 0 s"), (212, "3 min 32 s"), (3599, "59 min 59 s"),
    (3600, "1 h 00 min"), (4000, "1 h 06 min"),
])
def test_fmt_seconds(value, expected):
    assert fmt_seconds(value) == expected


def test_fmt_seconds_9_95_rounds_consistently():
    # 9.95 is a boundary: it must show either 9.9 s / 10 s style, never something longer than 4 chars of number
    assert fmt_seconds(9.95) in ("9.9 s", "10 s", "10.0 s")


def test_fmt_seconds_just_under_ten_does_not_show_ten_point_zero():
    # 9.96 rounds to "10.0 s" while 10 shows "10 s": inconsistent formats (cosmetic)
    assert fmt_seconds(9.96) == "10 s", "9.96 s is shown as '10.0 s' (format switch at 10 s is inconsistent)"


def _run(*args):
    return main([str(a) for a in args])


def _profile_stub(tmp_path, tables, out_name="out"):
    ProgressStub.TABLES = list(tables)
    out = tmp_path / out_name
    assert _run("profile", "stubprog://x", "--out", out) == 0
    return out


@pytest.fixture(autouse=True)
def _reset_stub():
    saved = ProgressStub.TABLES
    yield
    ProgressStub.TABLES = saved


def _pj(out: Path):
    return json.loads((out / "_bijoe" / "profile.json").read_text(encoding="utf-8"))


def test_profile_json_has_timings_and_schema_version_unchanged(tmp_path):
    out = _profile_stub(tmp_path, ["alpha", "beta", "gamma"])
    prof = _pj(out)
    t = prof["timings"]
    assert set(t) == {"total_seconds", "connect_seconds", "list_seconds", "tables_seconds", "relationships_seconds"}
    assert all(isinstance(v, float) and v >= 0 for v in t.values())
    assert all("profile_seconds" in x for x in prof["tables"])
    assert wiki.SCHEMA_VERSION == 2
    # consistency: the per-table sum is within the tables total, which is within the grand total
    assert sum(x["profile_seconds"] for x in prof["tables"]) <= t["tables_seconds"] + 0.01
    assert t["total_seconds"] + 0.01 >= t["connect_seconds"] + t["list_seconds"] + t["tables_seconds"] + t["relationships_seconds"]


def test_footers_present_and_metadata_last(tmp_path):
    out = _profile_stub(tmp_path, ["alpha", "beta", "gamma"])
    for md in (out / "data-stories").glob("*.md"):
        text = md.read_text(encoding="utf-8")
        assert len(STORY_FOOTER.findall(text)) == 1
        body = unframe(text)
        assert body.rindex("<i>Profiled in") < body.index("## Metadata") == body.rindex("## Metadata")
        meta = body.split("## Metadata", 1)[1]
        assert "profile_seconds:" in meta
        assert meta.rstrip().endswith("```")
    index = (out / "index.md").read_text(encoding="utf-8")
    assert len(INDEX_FOOTER.findall(index)) == 1
    assert re.search(r"\(connecting .+, tables .+, relationships .+\)\.</i>", index)
    body = unframe(index)
    assert body.rindex("<i>Profiling took") < body.index("## Metadata")
    meta = body.split("## Metadata", 1)[1]
    for key in ("profile_seconds", "connect_seconds", "tables_seconds", "relationships_seconds"):
        assert f"\n{key}: " in meta


def test_static_copies_have_no_footer(tmp_path):
    out = _profile_stub(tmp_path, ["alpha"])
    for name in ("beam-annotations.md", "how-to-read.md"):
        text = (out / name).read_text(encoding="utf-8")
        assert "Profiled in" not in text and "Profiling took" not in text and "profile_seconds" not in text


def test_footer_absent_without_timings(tmp_path):
    out = _profile_stub(tmp_path, ["alpha", "beta"])
    prof = _pj(out)
    prof.pop("timings")
    for t in prof["tables"]:
        t.pop("profile_seconds")
    (out / "_bijoe" / "profile.json").write_text(json.dumps(prof), encoding="utf-8")
    assert _run("render", out) == 0
    for md in list((out / "data-stories").glob("*.md")) + [out / "index.md"]:
        text = md.read_text(encoding="utf-8")
        assert "<i>Profil" not in text and "profile_seconds" not in text and "connect_seconds" not in text, md.name
        assert "## Metadata" in text


def test_partial_timings_do_not_crash(tmp_path):
    out = _profile_stub(tmp_path, ["alpha", "beta"])
    prof = _pj(out)
    prof["timings"] = {"total_seconds": 3.0}  # an older / hand-made profile with only a total
    (out / "_bijoe" / "profile.json").write_text(json.dumps(prof), encoding="utf-8")
    assert _run("render", out) == 0
    index = (out / "index.md").read_text(encoding="utf-8")
    assert "<i>Profiling took 3.0 s.</i>" in index  # no empty parentheses
    prof["timings"] = {}
    (out / "_bijoe" / "profile.json").write_text(json.dumps(prof), encoding="utf-8")
    assert _run("render", out) == 0
    assert "Profiling took" not in (out / "index.md").read_text(encoding="utf-8")


def test_null_values_do_not_crash(tmp_path):
    out = _profile_stub(tmp_path, ["alpha"])
    prof = _pj(out)
    prof["timings"] = {"total_seconds": None, "connect_seconds": None}
    prof["tables"][0]["profile_seconds"] = None
    (out / "_bijoe" / "profile.json").write_text(json.dumps(prof), encoding="utf-8")
    assert _run("render", out) == 0
    assert "<i>Profil" not in (out / "index.md").read_text(encoding="utf-8")


def test_render_never_remeasures_and_reprofile_replaces(tmp_path):
    out = _profile_stub(tmp_path, ["alpha", "beta"])
    prof = _pj(out)  # plant sentinel numbers a real measurement could never give
    prof["timings"].update(total_seconds=999.0, connect_seconds=111.0)
    for t in prof["tables"]:
        t["profile_seconds"] = 123.0
    (out / "_bijoe" / "profile.json").write_text(json.dumps(prof), encoding="utf-8")
    assert _run("render", out) == 0
    assert _run("render", out) == 0
    again = _pj(out)
    assert [t["profile_seconds"] for t in again["tables"]] == [123.0, 123.0]
    assert again["timings"]["total_seconds"] == 999.0
    assert "Profiled in 2 min 3 s." in (out / "data-stories" / "alpha.md").read_text(encoding="utf-8")
    assert "Profiling took 16 min 39 s (connecting 1 min 51 s" in (out / "index.md").read_text(encoding="utf-8")
    # a second profile into the same folder replaces them with new measurements
    assert _run("profile", "stubprog://x", "--out", out) == 0
    third = _pj(out)
    assert [t["profile_seconds"] for t in third["tables"]] != [123.0, 123.0]
    assert third["timings"]["total_seconds"] < 50
    assert "Profiled in 2 min" not in (out / "data-stories" / "alpha.md").read_text(encoding="utf-8")


def test_schema_page_footer(tmp_path):
    names = [f"{s}.t{i}" for s in ("s1", "s2") for i in range(12)]
    out = _profile_stub(tmp_path, names)
    pages = list((out / "schemas").glob("*.md"))
    assert pages, "25 tables over 2 schemas should produce schema pages"
    prof = _pj(out)
    for page in pages:
        text = page.read_text(encoding="utf-8")
        assert len(SCHEMA_FOOTER.findall(text)) == 1
        body = unframe(text)
        assert body.rindex("<i>Its tables took") < body.index("## Metadata")
        assert text.rstrip().endswith("</div>")
    total = sum(t["profile_seconds"] for t in prof["tables"])
    assert total <= prof["timings"]["tables_seconds"] + 0.01


def test_footer_text_is_numbers_only(tmp_path):
    ProgressStub.VALUE = "SECRET_PERSON_Zz9"
    try:
        out = _profile_stub(tmp_path, ["alpha", "beta"])
    finally:
        ProgressStub.VALUE = "plain"
    for p in out.rglob("*.md"):
        for ln in p.read_text(encoding="utf-8").splitlines():
            if ln.startswith("<i>Profil") or ln.startswith("<i>Its tables took"):
                assert "SECRET" not in ln
                assert re.fullmatch(r"<i>(Profiled in|Profiling took|Its tables took)[ 0-9a-z.<(),]*</i>", ln), ln
