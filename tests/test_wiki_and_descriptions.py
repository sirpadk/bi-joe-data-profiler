import json
import re
from pathlib import Path
from typing import Any, Iterator, List, Optional, Sequence

from htmlutil import headings, matrix, matrix_row, property_rows, strip, notitle, unframe

from bijoe import beam, descriptions, wiki
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


def _read(out: Path, *parts: str) -> str:
    return out.joinpath(*parts).read_text(encoding="utf-8")


def _filled_wiki(shop_csv, tmp_path) -> Path:
    """A wiki where the customers table has every field filled in."""
    out = tmp_path / "wiki"
    _run("profile", shop_csv, "--out", out, "--purpose", "build a sales dashboard")
    data = descriptions.load(out)
    data["dataset"].update(summary="Sales records for a small web shop.", source="inferred")
    data["tables"]["customers"].update(
        description="A person who has signed up with the shop and is known by a customer number.",
        grain="One row for each person who is a customer",
        source="inferred", confidence="medium",
        evidence=["`cust_id` unique and never missing across 4 rows"],
        ai_notes="`zip` is stored as text with leading zeros.",
        open_questions=["Why is `country` sometimes empty?"],
        beam={"table": ["CV"], "table_why": "One row per customer, no validity dates.", "columns": {}},
    )
    descriptions.save(out, data)
    assert _run("render", out) == 0
    return out


def test_profile_builds_linked_wiki(shop_csv, tmp_path):
    out = tmp_path / "wiki"
    assert _run("profile", shop_csv, "--out", out, "--purpose", "build a sales dashboard") == 0
    index = _read(out, "index.md")
    assert unframe(index).startswith("# Shop: Data Profile")
    meta = unframe(index).split("## Metadata", 1)[1]
    assert '```yaml\nbijoe: "data-profile-index"' in meta and meta.rstrip().endswith("```")
    assert property_rows(index)["Purpose"] == "build a sales dashboard"
    for link in re.findall(r"\]\((data-stories/[^)]+)\)", index):
        story = out / link
        assert story.is_file()
        assert "](../index.md)" in story.read_text(encoding="utf-8")
    assert (out / "_bijoe" / "profile.json").is_file()
    assert descriptions.load(out)["tables"]["orders"]["source"] == "pending"


def test_system_metadata_is_used_verbatim(tmp_path):
    out = tmp_path / "wiki"
    assert _run("profile", "fake://meta", "--out", out) == 0
    data = descriptions.load(out)
    assert data["tables"]["dim_customer"]["source"] == "system_metadata"
    assert data["tables"]["Fakta Salg"]["source"] == "pending"
    story = _read(out, "data-stories", "dim-customer.md")
    props = property_rows(story)
    assert props["Description"] == "Customer master data, one row per customer, from the CRM."
    assert "word for word" in props["Description Source"]
    assert (out / "data-stories" / "fakta-salg.md").is_file()


def test_descriptions_survive_reprofile_and_render(shop_csv, tmp_path):
    out = _filled_wiki(shop_csv, tmp_path)
    data = descriptions.load(out)
    data["tables"]["customers"]["definition"] = "old field"
    descriptions.save(out, data)
    _run("profile", shop_csv, "--out", out)  # re-profile keeps the text
    data = descriptions.load(out)
    assert data["tables"]["customers"]["confidence"] == "medium"
    assert "definition" not in data["tables"]["customers"]  # merged into description
    assert _run("render", out) == 0
    story = _read(out, "data-stories", "customers.md")
    assert property_rows(story)["Confidence"] == "medium"
    assert 'description_source: "inferred"' in story
    assert property_rows(_read(out, "index.md"))["About"].startswith("Sales records for a small web shop.")


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


def test_lint_never_state_the_obvious(shop_csv, tmp_path):
    out = tmp_path / "wiki"
    _run("profile", shop_csv, "--out", out)
    profile = wiki.load_profile(out)
    base = {**descriptions.empty_entry(), "source": "inferred", "confidence": "high", "evidence": ["x"]}

    def messages(description, grain="One row for each person who is a customer", name="customers"):
        tables = {name: {**base, "description": description, "grain": grain}}
        return " | ".join(m for lvl, _, m in _lint(profile, tables) if lvl == "warning")

    # circular: repeats the table name in other words
    assert "only repeats the table name" in messages("Customer information.")
    assert "only repeats the table name" in messages("A person who has signed up.", grain="One row per customer")
    assert "only repeats the table name" not in messages("A person who has signed up with the shop and has a customer number.")
    # backticks (code styling) do not belong in a description
    assert "backticks" in messages("A person identified by `cust_id` in the shop.")
    assert "backticks" not in messages("A person identified by cust_id in the shop.")  # plain text is fine
    # it also has to fit on the landing page
    assert "characters; keep it under" in messages("A person who has signed up. " * 30)
    # grain wording, and "More context needed." is accepted
    assert "grain should read 'One row for each" in messages("A person who has signed up.", grain="Each customer")
    assert not messages("More context needed.", grain="More context needed.")
    # the summary talks about the data as a whole
    assert descriptions.lint(profile, {"dataset": {"summary": "The `orders` and customers tables of a shop."}, "tables": {}})
    summary_msgs = " | ".join(m for _, _, m in descriptions.lint(
        profile, {"dataset": {"summary": "The `orders` and customers tables of a shop."}, "tables": {}}))
    assert "summary names tables or columns in `backticks`" in summary_msgs
    assert "summary names tables (customers, orders)" in summary_msgs


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
    profile = json.loads(_read(out, "_bijoe", "profile.json"))
    assert profile["schema_version"] == 2 and profile["settings"]["include_values"] is False
    assert [t["slug"] for t in profile["tables"]] == ["customers", "orders"]


# ---- layout -------------------------------------------------------------------

def test_landing_page_layout(shop_csv, tmp_path):
    out = _filled_wiki(shop_csv, tmp_path)
    index = _read(out, "index.md")
    assert index.index("## At a Glance") < index.index("## Data Stories") < index.index("## Data Model")
    props = property_rows(index)
    assert list(props) == ["About", "Source", "Tables", "Sampled Rows", "Profiled", "Purpose", "How to Read"]
    assert props["About"] == "Sales records for a small web shop. <i>(written by AI)</i>"
    assert props["Sampled Rows"] == "8"
    assert 'href="how-to-read.md"' in notitle(props["How to Read"]) and 'href="beam-annotations.md"' in notitle(props["How to Read"])
    # no Markdown property table (it would show an empty header row), no leftovers
    assert "| | |" not in index and "<th></th>" not in index
    assert "One page per table" not in index and "How to read this wiki" not in index.replace("How to Read This Wiki", "")
    # the list of data stories is a themed HTML table whose header sits at the bottom of its cell
    heads = re.findall(r'<th style="[^"]*vertical-align:bottom;[^"]*">([^<]*)</th>', index)
    assert heads == ["Table", "BEAM✲", "Grain", "Description", "Sampled Rows", "Columns"]
    assert "One row for each person who is a customer</td>" in index
    assert "A person who has signed up with the shop and is known by a customer number.</td>" in index


def test_story_layout_and_order(shop_csv, tmp_path):
    out = _filled_wiki(shop_csv, tmp_path)
    story = _read(out, "data-stories", "customers.md")
    props = property_rows(story)
    # the description comes first, then the grain; there is no separate definition
    assert list(props)[:3] == ["Description", "Grain", "BEAM✲"]
    assert "Definition" not in props
    assert props["Grain"] == "One row for each person who is a customer"
    assert props["Description"].startswith("A person who has signed up with the shop")
    assert list(props)[-3:] == ["Columns", "Description Source", "Confidence"]
    assert "<th></th>" not in story and "| | |" not in story
    # sections that must not exist any more
    for gone in ("Based on", "Why the suggestions", "Why the Suggestions", "## Sample Rows", "## Description", "Definition"):
        assert gone not in story.split("## Metadata")[0], gone
    # order: columns, relationships, additional context, open questions, metadata
    order = ["## Columns", "## Relationships (Measured)", "## Additional Context (Written by AI)",
             "## Open Questions for the Data Owner", "## Metadata"]
    positions = [story.index(h) for h in order]
    assert positions == sorted(positions)
    # the evidence is metadata for AI agents, not page content
    body, meta = story.split("## Metadata")
    assert "never missing across 4 rows" not in body and "never missing across 4 rows" in meta


def test_relationships_section_is_a_diagram_or_na(shop_csv, tmp_path):
    out = _filled_wiki(shop_csv, tmp_path)
    story = _read(out, "data-stories", "orders.md")
    section = story.split("## Relationships (Measured)")[1].split("## Metadata")[0]
    assert "```mermaid\n%%{init:" in section and "\nflowchart LR" in section
    assert "<div style='text-align:left'><b>orders</b><hr/>order_id<br/>cust_id<br/>amount<br/>status</div>" in section
    assert 't_customers["customers"]' in section  # linked tables are plain boxes, with no columns
    assert "t_orders --- t_customers" in section and "||" not in section
    assert "- " not in section.replace("──────────", "").split("```")[0]  # no text list

    out2 = tmp_path / "wiki2"
    _run("profile", "fake://meta", "--out", out2)
    story2 = _read(out2, "data-stories", "dim-customer.md")
    assert story2.split("## Relationships (Measured)")[1].split("---")[0].strip() == "N/A"


def _table(names, key=None):
    return {"name": "t", "columns": [{"name": n, **({"primary_key": True} if n == key else {})} for n in names]}


def _rel(frm, col=None, to="u", to_col="id", incoming=None):
    if incoming:
        return {"from_table": "u", "from_column": "x", "to_table": "t", "to_column": incoming}
    return {"from_table": "t", "from_column": col, "to_table": to, "to_column": to_col}


def test_diagram_columns_follow_the_agreed_rule():
    names = [f"c{i}" for i in range(1, 31)]
    table = _table(names, key="c1")
    rels = [_rel("t", "c5"), _rel("t", "c6"), _rel("t", "c12"), _rel("t", "c28")]
    shown = wiki.diagram_columns(table, {}, rels)
    # priority: 1, 5, 6, 12, 28; then the earliest others, 15 of them: 2-4, 7-11, 13-19
    assert shown == [f"c{i}" for i in range(1, 20)] + [None, "c28", None]
    assert len([c for c in shown if c]) == 20

    # a table of 28 columns ends on a relationship column: no "..." at the end
    table28 = _table(names[:28], key="c1")
    assert wiki.diagram_columns(table28, {}, rels)[-2:] == [None, "c28"]

    # up to 20 columns: everything, with no "..."
    assert wiki.diagram_columns(_table(names[:20]), {}, rels) == names[:20]

    # more priority columns than places: show all of them (in table order), still marking the gaps
    many = [_rel("t", f"c{i}") for i in range(2, 27, 1) if i % 1 == 0][:25]
    shown = wiki.diagram_columns(_table(names, key="c1"), {}, many)
    assert [c for c in shown if c] == [f"c{i}" for i in range(1, 27)] and shown[-1] is None


def test_diagram_priority_includes_incoming_relationships_and_suggested_keys():
    names = [f"c{i}" for i in range(1, 31)]
    entry = {"beam": {"columns": {"c25": {"codes": ["BK", "MD"]}, "c26": {"codes": ["FV"]}}}}
    rels = [{"from_table": "u", "from_column": "x", "to_table": "t", "to_column": "c30"}]
    shown = wiki.diagram_columns(_table(names), entry, rels)
    assert "c30" in shown and "c25" in shown and "c26" not in shown  # c26 is not a key, c25 is a business key
    assert [c for c in shown if c][:2] == ["c1", "c2"]


# ---- the columns matrix ------------------------------------------------------

def test_column_matrix_follows_the_modelstormer_layout(shop_csv, tmp_path):
    out = tmp_path / "wiki"
    _run("profile", shop_csv, "--out", out)
    story = _read(out, "data-stories", "customers.md")
    rows = matrix(story)
    assert [(r["group"], r["label"]) for r in rows] == (
        [(None, "Column Name"), (None, "Data Type"), (None, "BEAM✲")]
        + [("Data Profiling Results", l) for l in ["Sample Count", "Missing", "Unique Values", "Min Value", "Min Count",
                                                    "Max Value", "Max Count", "Min Length", "Max Length"]]
        + [("Variation", l) for l in ["Typical", "Different", "Repeat", "Missing", "Range", "Change"]]
        + [("Distribution", l) for l in ["Histogram", "Shape", "Median", "Spread", "Outliers", "Gaps"]]
        + [("Sample Data", "")] * 4)  # the table has 4 rows, so 4 sample rows
    assert [strip(c) for _, c in rows[0]["cells"]] == ["cust_id", "name", "country", "signup_date", "zip"]
    # the groups are spanning, rotated labels; both label columns are frozen
    assert story.count('rowspan="9"') == 1 and story.count('rowspan="6"') == 2 and story.count('rowspan="4"') == 1
    assert "writing-mode:vertical-rl" in story and "position:sticky;left:0" in story
    assert "position:sticky;left:34px" in story and "white-space:nowrap" in story
    assert "overflow-x:auto" in story
    # numbers are right-aligned in Sample Count and the length rows, not in the others
    by_label = {(r["group"], r["label"]): r for r in rows}
    assert "text-align:right" in by_label[("Data Profiling Results", "Sample Count")]["cells"][0][0]
    assert "text-align:right" not in by_label[("Data Profiling Results", "Missing")]["cells"][0][0]

    group = "Data Profiling Results"
    assert matrix_row(story, "Sample Count", group) == ["4"] * 5
    assert matrix_row(story, "Unique Values", group)[2] == "2 (50%)"  # country: DK, SE
    assert matrix_row(story, "Min Value", group)[3] == "2024-01-03"
    assert matrix_row(story, "Max Count", group)[2] == "1 (25%)"  # SE
    assert matrix_row(story, "Repeat", "Variation")[2] == "DK ×2"
    assert matrix_row(story, "Range", "Variation")[0] == "1 → 4"
    assert matrix_row(story, "Missing", "Variation")[2] == "empty ×1"
    assert matrix_row(story, "Change", "Variation") == ["—"] * 5
    sample = [r for r in rows if r["group"] == "Sample Data"]
    assert [strip(c) for _, c in sample[0]["cells"]][:2] == ["1", "Ann"]
    assert "## Sample Rows" not in story


def test_placeholders_and_hidden_values(tmp_path):
    d = tmp_path / "src"
    d.mkdir()
    (d / "t.csv").write_text("code,city\nA,N/A\nB,Oslo\nC,N/A\nD,Bergen\n", encoding="utf-8")
    out = tmp_path / "wiki"
    _run("profile", d, "--out", out)
    story = _read(out, "data-stories", "t.md")
    assert "N/A ×2" in matrix_row(story, "Missing", "Variation")[1]
    _run("profile", d, "--out", out, "--no-values")
    story = _read(out, "data-stories", "t.md")
    assert matrix_row(story, "Typical", "Variation") == ["hidden", "hidden"]
    assert all(r["group"] != "Sample Data" for r in matrix(story))
    assert "Example values and sample rows are hidden" in story


# ---- Title Case and the HTML tables ------------------------------------------

def test_title_case():
    assert wiki.title_case("At a glance") == "At a Glance"
    assert wiki.title_case("Open questions for the data owner") == "Open Questions for the Data Owner"
    assert wiki.title_case("How to read this wiki") == "How to Read This Wiki"
    assert wiki.title_case("Relationships (measured)") == "Relationships (Measured)"
    assert wiki.title_case("Additional context (written by AI)") == "Additional Context (Written by AI)"
    assert wiki.title_case("Shoe company: data profile") == "Shoe Company: Data Profile"
    assert wiki.title_case("Column codes: events and facts") == "Column Codes: Events and Facts"
    assert wiki.title_case("The 7Ws") == "The 7Ws" and wiki.title_case("BEAM✲ annotations") == "BEAM✲ Annotations"
    assert wiki.title_case("What it is for") == "What It Is For"  # the last word is always capitalised


def test_every_heading_title_and_header_is_title_case(shop_csv, tmp_path):
    out = _filled_wiki(shop_csv, tmp_path)
    pages = [out / "index.md", out / "how-to-read.md", out / "beam-annotations.md",
             *sorted((out / "data-stories").glob("*.md"))]
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for i, heading in enumerate(headings(text)):
            if page.parent.name == "data-stories" and i == 0:
                continue  # the table's own name
            assert wiki.title_case(heading) == heading, f"{page.name}: {heading!r}"
        for line in text.splitlines():  # Markdown table header rows
            if line.startswith("| ") and re.match(r"^\|[-:| ]+\|$", text.splitlines()[text.splitlines().index(line) + 1]
                                                   if text.splitlines().index(line) + 1 < len(text.splitlines()) else ""):
                for cell in [c.strip() for c in line.strip("|").split("|")]:
                    assert wiki.title_case(cell) == cell, f"{page.name}: header {cell!r}"
        for label in re.findall(r'<th (?:scope="row"|colspan="2")[^>]*>(.*?)</th>', text, re.S):  # not column names
            plain = strip(label)
            if plain:
                assert wiki.title_case(plain) == plain or plain.startswith("Why "), f"{page.name}: label {plain!r}"


def test_two_column_tables_are_html_everywhere(shop_csv, tmp_path):
    out = _filled_wiki(shop_csv, tmp_path)
    for page in [out / "index.md", out / "how-to-read.md", *sorted((out / "data-stories").glob("*.md"))]:
        text = page.read_text(encoding="utf-8")
        assert "| | |" not in text and "|---|---|\n" not in text, page.name  # no Markdown two-column tables
        assert "<th></th>" not in text, page.name
    props = property_rows(_read(out, "data-stories", "customers.md"))
    assert notitle(props["Source"]).startswith('<a href="../beam-annotations.md#t-source">{customers.csv}</a>')
    assert beam.PAGE in _read(out, "how-to-read.md")


def test_theme_is_chosen_remembered_and_switchable(shop_csv, tmp_path):
    out = tmp_path / "wiki"
    _run("profile", shop_csv, "--out", out)  # default: light gray
    story = _read(out, "data-stories", "customers.md")
    assert "#e4e7eb" in story and "#161616" not in story
    _run("render", out, "--theme", "dark")
    dark = _read(out, "data-stories", "customers.md")
    assert "#161616" in dark and "#e4e7eb" not in dark and "border-left:3px solid #2de2c9" in dark
    _run("render", out)  # remembered
    assert "#161616" in _read(out, "data-stories", "customers.md")
    _run("render", out, "--theme", "light-blue")
    assert "#d4e6f8" in _read(out, "data-stories", "customers.md")
    assert _run("render", out, "--theme", "neon") != 0


def _big_profile(n_per_schema=8, schemas=("Sales", "Person", "Production")):
    tables = []
    for s in schemas:
        for i in range(n_per_schema):
            name = f"{s}.T{i}"
            tables.append({"name": name, "slug": wiki.slugify(name, set()), "details": {"schema": s},
                           "profiled_rows": 10, "column_count": 2, "columns": []})
    rels = [{"from_table": "Sales.T0", "from_column": "a", "to_table": "Person.T0", "to_column": "a",
             "matched_values": 1, "checked_values": 1, "coverage_pct": 100},
            {"from_table": "Sales.T1", "from_column": "a", "to_table": "Sales.T2", "to_column": "a",
             "matched_values": 1, "checked_values": 1, "coverage_pct": 100}]
    return {"dataset": {"name": "Big", "source": "x", "source_type": "database", "connector": "sqlalchemy"},
            "tables": tables, "relationships": rels, "generated_at": "2026-01-01T00:00:00+00:00", "bijoe_version": "0",
            "settings": {}}


def test_big_database_is_split_by_schema():
    profile = _big_profile()
    assert wiki.use_schema_split(profile) and not wiki.use_schema_split(_big_profile(2))  # 6 tables stay in one diagram
    overview = "\n".join(wiki.schema_overview_diagram(profile))
    assert 'Sales<br/>8 tables' in overview and overview.count("---") == 1  # Sales and Person are linked
    page = "\n".join(wiki.schema_diagram("Sales", profile))
    assert 't_Person_T0["Person.T0"]' in page and "classDef ext stroke-dasharray" in page  # other schema: dashed
    assert "Production.T0" not in page  # not linked, not shown
    index = wiki.render_index(profile, {"dataset": {}, "tables": {}})
    assert "### Sales (8 tables)" in index and "schemas/sales.md" in index
    assert index.count("```mermaid") == 1  # the overview only, not a 24-box diagram


def test_schema_pages_and_the_whole_page_follow_the_theme(tmp_path):
    profile = _big_profile()
    wiki.set_theme("dark")
    try:
        page = wiki.render_schema_page("Sales", wiki.schema_groups(profile)[0][1], profile, {"tables": {}})
        assert page.startswith('<div style="background:#101010;color:#eaeaea;') and page.rstrip().endswith("</div>")
        assert '"primaryColor": "#1d1d1d"' in page and 'style="color:#4cc2ff"' in page  # diagram and links themed
        assert 'vertical-align:bottom;' in page  # table headers sit at the bottom
    finally:
        wiki.set_theme(None)
