import json
import re
from pathlib import Path
from typing import Any, Iterator, List, Optional, Sequence

from bijoe import descriptions, wiki
from bijoe.cli import main
from bijoe.connectors import ColumnInfo, Connector, TableInfo, register


@register
class FakeMetadataConnector(Connector):
    """A plugin-style connector with system metadata, proving the extension point works."""

    name = "fake-meta"
    label = "test only"
    source_type = "database"

    @classmethod
    def can_handle(cls, source: str) -> bool:
        return source == "fake://meta"

    def list_tables(self) -> List[str]:
        return ["dim_customer", "Fakta Salg"]

    def describe_table(self, table: str) -> TableInfo:
        comment = "Customer master data, one row per customer, from the CRM." if table == "dim_customer" else None
        return TableInfo(table, [ColumnInfo("id", "INT", primary_key=True, comment="Surrogate key")], comment, 2)

    def iter_rows(self, table: str, limit: Optional[int] = None) -> Iterator[Sequence[Any]]:
        yield from [(1,), (2,)][:limit]

    def display_source(self) -> str:
        return "fake://meta"


def _run(*args) -> int:
    return main([str(a) for a in args])


def test_profile_builds_linked_wiki(shop_csv, tmp_path):
    out = tmp_path / "wiki"
    assert _run("profile", shop_csv, "--out", out, "--purpose", "build a sales dashboard") == 0
    index = (out / "index.md").read_text(encoding="utf-8")
    assert index.startswith("---\nbijoe: \"data-profile-index\"")
    assert "build a sales dashboard" in index
    for link in re.findall(r"\]\((data-stories/[^)]+)\)", index):
        story = out / link
        assert story.is_file()
        assert "](../index.md)" in story.read_text(encoding="utf-8")
    assert (out / "_bijoe" / "profile.json").is_file()
    data = descriptions.load(out)
    assert data["tables"]["orders"]["source"] == "pending"


def test_system_metadata_is_used_verbatim(tmp_path):
    out = tmp_path / "wiki"
    assert _run("profile", "fake://meta", "--out", out) == 0
    data = descriptions.load(out)
    assert data["tables"]["dim_customer"]["source"] == "system_metadata"
    assert data["tables"]["Fakta Salg"]["source"] == "pending"
    story = (out / "data-stories" / "dim-customer.md").read_text(encoding="utf-8")
    assert "Customer master data, one row per customer, from the CRM." in story
    assert "word for word" in story
    assert (out / "data-stories" / "fakta-salg.md").is_file()


def test_descriptions_survive_reprofile_and_render(shop_csv, tmp_path):
    out = tmp_path / "wiki"
    _run("profile", shop_csv, "--out", out)
    data = descriptions.load(out)
    data["dataset"].update(summary="Two linked tables from a small web shop: `customers` and their `orders`.", source="inferred")
    data["tables"]["orders"].update(
        description="One row per order line keyed by `order_id`, linked to `customers` via `cust_id`; one line is an exact duplicate.",
        source="inferred", confidence="medium",
        evidence=["`order_id` 100-102 with 102 repeated", "1 duplicate row of 4"],
        open_questions=["Is `amount` in DKK?"],
    )
    descriptions.save(out, data)
    _run("profile", shop_csv, "--out", out)  # re-profile keeps the text
    assert descriptions.load(out)["tables"]["orders"]["confidence"] == "medium"
    assert _run("render", out) == 0
    story = (out / "data-stories" / "orders.md").read_text(encoding="utf-8")
    assert "Confidence: **medium**" in story and "Is `amount` in DKK?" in story
    assert 'description_source: "inferred"' in story
    index = (out / "index.md").read_text(encoding="utf-8")
    assert "One row per order line keyed by" in index and "web shop" in index


def _lint(profile, tables):
    return descriptions.lint(profile, {"dataset": {"summary": "x"}, "tables": tables})


def test_lint_catches_invented_and_obvious(shop_csv, tmp_path):
    out = tmp_path / "wiki"
    _run("profile", shop_csv, "--out", out)
    profile = wiki.load_profile(out)
    base = descriptions.empty_entry()

    problems = _lint(profile, {
        "customers": {**base, "description": "This table contains information about customers and their `loyalty_tier` in various markets.",
                      "source": "inferred", "confidence": "high", "evidence": []},
        "orders": {**base, "description": "Orders.", "source": "inferred"},
    })
    msgs = " | ".join(m for _, _, m in problems)
    levels = {(lvl, where.split()[-1]) for lvl, where, _ in problems}
    assert "weak phrase" in msgs and "various" in msgs
    assert "`loyalty_tier` is not a table, column or observed value" in msgs
    assert ("error", "customers") in levels  # inferred without evidence
    assert ("error", "orders") in levels  # inferred without confidence
    assert "only 7 characters" in msgs


def test_lint_system_metadata_must_be_verbatim(tmp_path):
    out = tmp_path / "wiki"
    _run("profile", "fake://meta", "--out", out)
    profile = wiki.load_profile(out)
    data = descriptions.load(out)
    data["tables"]["dim_customer"]["description"] = "Improved wording of the CRM description."
    errors = [m for lvl, _, m in descriptions.lint(profile, data) if lvl == "error"]
    assert any("quoted exactly" in m for m in errors)
    descriptions.save(out, data)
    assert _run("render", out) == 1  # refuses to publish
    assert _run("check", out) == 1


def test_evidence_command(shop_csv, tmp_path, capsys):
    out = tmp_path / "wiki"
    _run("profile", shop_csv, "--out", out)
    capsys.readouterr()
    assert _run("evidence", out, "--table", "orders") == 0
    text = capsys.readouterr().out
    assert "## orders" in text and "## customers" not in text
    assert "mixed: decimal 1, integer 1, text 2" in text


def test_profile_json_is_valid(shop_csv, tmp_path):
    out = tmp_path / "wiki"
    _run("profile", shop_csv, "--out", out, "--no-values")
    profile = json.loads((out / "_bijoe" / "profile.json").read_text(encoding="utf-8"))
    assert profile["schema_version"] == 1 and profile["settings"]["include_values"] is False
    assert [t["slug"] for t in profile["tables"]] == ["customers", "orders"]
