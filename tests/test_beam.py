import re

from bijoe import beam, descriptions, wiki
from bijoe.cli import main


def test_parse_scopes_and_anchors():
    assert beam.parse("CV", "table").anchor == "t-cv"
    assert beam.parse("[CV]", "table").text == "[CV]"
    assert beam.parse("CV", "column").anchor == "c-cv"
    assert beam.parse("C30", "column").anchor == "c-c"
    assert beam.parse("N7.2", "column").base == "N"
    assert beam.parse("DC1,2", "column").anchor == "c-dc"
    assert beam.parse("DF=UnitPrice-UnitCost", "column").anchor == "c-df"
    assert beam.parse("[when]", "column").anchor == "w-when"
    assert beam.parse("[Stores]", "column", ["Stores"]).anchor == "c-dim"
    assert beam.parse("[USD]", "column", ["Stores"]).anchor == "c-uom"
    struck = beam.parse("~~MD~~", "column")
    assert struck.struck and struck.anchor == "c-unavailable"
    assert beam.parse("ZZ", "column") is None
    assert beam.parse("FA", "table") is None


def test_links_escape_brackets():
    assert beam.parse("CV", "table").link("../") == "[\\[CV\\]](../beam-annotations.md#t-cv)"
    assert beam.links(["FA", "[USD]"], "column") == \
        "[FA](beam-annotations.md#c-fa) [\\[USD\\]](beam-annotations.md#c-uom)"


def test_prose_links_only_known_codes():
    text = "A current value [CV] dimension; see [docs](x.md); the [when] of it; [CV, HM]; [foo]."
    out = beam.link_prose(text)
    assert "[\\[CV\\]](beam-annotations.md#t-cv)" in out
    assert "[docs](x.md)" in out and "[foo]" in out
    assert "(beam-annotations.md#w-when)" in out
    assert "[HM](beam-annotations.md#t-hm)" in out


def test_every_anchor_exists_on_reference_page():
    page = beam.ASSET.read_text(encoding="utf-8")
    anchors = set(re.findall(r'<a id="([^"]+)"></a>', page))
    needed = {f"t-{c.lower()}" for c in beam.TABLE_CODES} | {f"c-{c.lower()}" for c in beam.COLUMN_CODES}
    needed |= {f"w-{w}" for w in beam.W_TYPES}
    needed |= {"t-source", "c-source", "c-dim", "c-uom", "c-unavailable", "c-suspect", "c-important"}
    assert needed - anchors == set()


def test_measured_codes():
    table = {"name": "T"}
    assert beam.data_type_code({"inferred_type": "text", "max_length": 6}) == "C6"
    assert beam.data_type_code({"inferred_type": "text", "max_length": 900}) == "T900"
    assert beam.data_type_code({"inferred_type": "decimal", "precision": 6, "scale": 2}) == "N6.2"
    assert beam.data_type_code({"inferred_type": "boolean"}) is None
    uniq = {"name": "id", "inferred_type": "integer", "all_values_unique": True, "missing_count": 0}
    assert beam.measured_column_codes(table, uniq, []) == ["ND"]
    money = {**uniq, "inferred_type": "decimal"}
    assert beam.measured_column_codes(table, money, []) == []


def _wiki(shop_csv, tmp_path):
    out = tmp_path / "wiki"
    assert main(["profile", str(shop_csv), "--out", str(out)]) == 0
    return out


def test_relationship_measured_and_page_copied(shop_csv, tmp_path):
    out = _wiki(shop_csv, tmp_path)
    profile = wiki.load_profile(out)
    rels = profile["relationships"]
    assert any(r["from_table"] == "orders" and r["from_column"] == "cust_id" and r["to_table"] == "customers"
               and r["coverage_pct"] == 100 for r in rels)
    assert (out / beam.PAGE).read_text(encoding="utf-8") == beam.ASSET.read_text(encoding="utf-8")
    story = (out / "data-stories" / "orders.md").read_text(encoding="utf-8")
    assert "## Relationships (measured)" in story and "[FK](../beam-annotations.md#c-fk)" in story
    assert "{orders.csv}" in story
    index = (out / "index.md").read_text(encoding="utf-8")
    assert "## Data model" in index and "```mermaid\nerDiagram" in index
    assert "    customers ||--o{ orders : \"\"" in index  # table level, no column names
    assert "cust_id" not in index.split("## Data model")[1].split("## Metadata")[0]
    assert "](beam-annotations.md)" in index and "](how-to-read.md)" in index
    assert (out / "how-to-read.md").is_file()


def test_suggestions_render_as_links_and_md_is_struck(shop_csv, tmp_path):
    out = _wiki(shop_csv, tmp_path)
    data = descriptions.load(out)
    data["tables"]["customers"].update(
        description="One row per customer keyed by `cust_id`, a current value [CV] dimension with sign-up dates.",
        source="inferred", confidence="medium", evidence=["`cust_id` unique"],
        beam={"table": ["CV"], "table_why": "One row per `cust_id`, no validity dates.",
              "columns": {"country": {"codes": ["MD", "?"], "why": "Every customer should have a country."},
                          "signup_date": {"codes": ["FV"], "why": "Sign-up date should not change."}}},
        open_questions=["Why is `country` sometimes empty?"],
    )
    descriptions.save(out, data)
    assert main(["render", str(out)]) == 0
    story = (out / "data-stories" / "customers.md").read_text(encoding="utf-8")
    assert "| **BEAM✲** | [\\[CV\\]](../beam-annotations.md#t-cv) _(suggested by AI)_ |" in story
    assert "[~~MD~~](../beam-annotations.md#c-unavailable)" in story  # country has a gap
    assert "[FV](../beam-annotations.md#c-fv)" in story
    assert "[C2](../beam-annotations.md#c-c)" in story  # measured data type
    assert "a current value [\\[CV\\]](../beam-annotations.md#t-cv) dimension" in story
    assert 'beam_table_codes:\n  - "[CV]"' in story
    index = (out / "index.md").read_text(encoding="utf-8")
    assert "| [customers](data-stories/customers.md) | [\\[CV\\]](beam-annotations.md#t-cv) | _pending_ |" in index


def test_lint_beam(shop_csv, tmp_path):
    out = _wiki(shop_csv, tmp_path)
    profile = wiki.load_profile(out)
    entry = {**descriptions.empty_entry(), "description": "One row per order line keyed by `order_id`, with amounts.",
             "source": "inferred", "confidence": "high", "evidence": ["`order_id`"],
             "beam": {"table": ["ZZ"], "columns": {"amount": {"codes": ["N7.2", "QQ", "?"]},
                                                     "nope": {"codes": ["FA"], "why": "x"}}}}
    problems = descriptions.lint(profile, {"dataset": {"summary": "x"}, "tables": {"orders": entry}})
    msgs = [f"{lvl}: {m}" for lvl, _, m in problems]
    text = " | ".join(msgs)
    assert "error: 'ZZ' is not a BEAM table code" in text
    assert "error: N7.2 is measured by the engine" in text
    assert "error: 'QQ' is not a BEAM column code" in text
    assert "error: column does not exist" in text
    assert "warning: say why" in text
    assert "marked ? (suspect) but no open question" in text
