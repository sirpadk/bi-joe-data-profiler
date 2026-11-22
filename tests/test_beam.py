import re

from htmlutil import matrix_row, property_rows, strip, notitle

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
    assert notitle(beam.parse("CV", "table").link("../")) == "[\\[CV\\]](../beam-annotations.md#t-cv)"
    assert notitle(beam.links(["FA", "[USD]"], "column")) == \
        "[FA](beam-annotations.md#c-fa) [\\[USD\\]](beam-annotations.md#c-uom)"


def test_prose_links_only_known_codes():
    text = "A current value [CV] dimension; see [docs](x.md); the [when] of it; [CV, HM]; [foo]."
    out = beam.link_prose(text)
    assert "[\\[CV\\]](beam-annotations.md#t-cv)" in notitle(out)
    assert "[docs](x.md)" in out and "[foo]" in out
    assert "(beam-annotations.md#w-when)" in notitle(out)
    assert "[HM](beam-annotations.md#t-hm)" in notitle(out)


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


def test_html_links():
    assert notitle(beam.links_html(["CV"], "table", "../")) == '<a href="../beam-annotations.md#t-cv">[CV]</a>'
    assert notitle(beam.links_html(["~~MD~~"], "column")) == '<a href="beam-annotations.md#c-unavailable"><s>MD</s></a>'
    assert notitle(beam.links_html(["FV"], "column", italic=True)) == '<i><a href="beam-annotations.md#c-fv">FV</a></i>'
    out = beam.link_prose_html("a current value [CV] dimension, the [when], and [foo]")
    assert '<a href="beam-annotations.md#t-cv">[CV]</a>' in notitle(out) and "#w-when" in notitle(out) and "[foo]" in notitle(out)


def test_relationship_measured_and_page_copied(shop_csv, tmp_path):
    out = _wiki(shop_csv, tmp_path)
    profile = wiki.load_profile(out)
    rels = profile["relationships"]
    assert any(r["from_table"] == "orders" and r["from_column"] == "cust_id" and r["to_table"] == "customers"
               and r["coverage_pct"] == 100 for r in rels)
    assert (out / beam.PAGE).read_text(encoding="utf-8") == beam.ASSET.read_text(encoding="utf-8")
    assert (out / "how-to-read.md").read_text(encoding="utf-8") == (beam.ASSET.parent / "how-to-read.md").read_text(encoding="utf-8")
    story = (out / "data-stories" / "orders.md").read_text(encoding="utf-8")
    assert "## Relationships (Measured)" in story
    assert 'href="../beam-annotations.md#c-fk">FK</a>' in notitle(story)  # measured, in the matrix BEAM row
    assert "{orders.csv}" in story
    index = (out / "index.md").read_text(encoding="utf-8")
    model = index.split("## Data Model")[1].split("## Metadata")[0]
    assert "```mermaid\n%%{init:" in model and "\nflowchart LR" in model
    assert "    t_customers --- t_orders" in model  # plain line: no cardinality, no column names
    assert "||" not in model and "cust_id" not in model
    assert 'href="beam-annotations.md"' in index and 'href="how-to-read.md"' in index


def test_suggestions_render_as_links_and_md_is_struck(shop_csv, tmp_path):
    out = _wiki(shop_csv, tmp_path)
    data = descriptions.load(out)
    data["tables"]["customers"].update(
        description="A person who has signed up with the shop, a current value [CV] dimension.",
        grain="One row for each person who is a customer",
        source="inferred", confidence="medium", evidence=["`cust_id` unique"],
        beam={"table": ["CV"], "table_why": "One row per `cust_id`, no validity dates.",
              "columns": {"country": {"codes": ["MD", "?"], "why": "Every customer should have a country."},
                          "signup_date": {"codes": ["FV"], "why": "Sign-up date should not change."}}},
        open_questions=["Why is `country` sometimes empty?"],
    )
    descriptions.save(out, data)
    assert main(["render", str(out)]) == 0
    story = (out / "data-stories" / "customers.md").read_text(encoding="utf-8")
    props = property_rows(story)
    assert notitle(props["BEAM✲"]) == '<a href="../beam-annotations.md#t-cv">[CV]</a> <i>(suggested by AI)</i>'
    assert 'a current value <a href="../beam-annotations.md#t-cv">[CV]</a> dimension' in notitle(props["Description"])
    assert '<i><a href="../beam-annotations.md#c-unavailable"><s>MD</s></a></i>' in notitle(story)  # country has a gap
    assert '<i><a href="../beam-annotations.md#c-fv">FV</a></i>' in notitle(story)
    assert '<a href="../beam-annotations.md#c-c">C2</a> text' in notitle(story)  # measured data type
    assert 'beam_table_codes:\n  - "[CV]"' in story
    assert "evidence:\n  - \"`cust_id` unique\"" in story  # evidence lives in the metadata for AI agents
    assert "country MD ?: Every customer should have a country." in story  # reasons live there too
    assert "Why the Suggestions" not in story and "Why the suggestions" not in story
    index = (out / "index.md").read_text(encoding="utf-8")
    assert '<a href="data-stories/customers.md">customers</a>' in notitle(index)
    assert '<a href="beam-annotations.md#t-cv">[CV]</a>' in notitle(index) and "One row for each person who is a customer</td>" in index


def test_lint_beam(shop_csv, tmp_path):
    out = _wiki(shop_csv, tmp_path)
    profile = wiki.load_profile(out)
    entry = {**descriptions.empty_entry(), "description": "A purchase placed by a customer, with amounts.",
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


def test_every_code_and_measure_has_hover_text(shop_csv, tmp_path):
    from bijoe import wiki
    # every anchor on the reference page gives a hover text
    anchors = re.findall(r'<a id="([^"]+)"></a>', beam.ASSET.read_text(encoding="utf-8"))
    hover = beam._load_hover()
    assert anchors and all(hover.get(a) for a in anchors if a != "c-unavailable")
    c = beam.parse("BK", "column")
    assert beam.explain(c).startswith("Business Key:") and beam.explain(c, suggested=True).endswith("(Suggested by AI.)")
    assert "(Measured from the data.)" in beam.explain(beam.parse("C9", "column"))
    assert beam.explain(beam.parse("~~MD~~", "column")).startswith("Not met by the data.")
    assert 'title="Current Value:' in beam.links_html(["CV"], "table")
    assert '"Current Value:' in beam.links(["CV"], "table")  # Markdown links carry it as a link title
    # the matrix labels explain themselves
    out = tmp_path / "wiki"
    main(["profile", str(shop_csv), "--out", str(out)])
    story = (out / "data-stories" / "customers.md").read_text(encoding="utf-8")
    for label in wiki.MEASURE_HELP:
        shown = label if label != "Variation Missing" else "Missing"
        assert f'title="{wiki.MEASURE_HELP[label]}"'.replace("&", "&amp;") in story.replace("&#x27;", "'") or shown in story
    for label, text in wiki.GROUP_HELP.items():
        assert text in story
    assert story.count("Min Count") >= 1 and 'cursor:help' in story
