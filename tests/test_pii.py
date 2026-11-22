"""Personal data is measured but never saved or shown."""

import json

from bijoe import pii
from bijoe.cli import main


def test_classify_by_name_and_by_values():
    assert pii.classify("FirstName", "text", ["Anne"])["class"] == "person name"
    assert pii.classify("Fødselsdato", "date", [])["class"] == "birth date"
    assert pii.classify("Telefon", "text", [])["class"] == "phone"
    assert pii.classify("CPR", "text", [])["class"] == "national id"
    # identifiers, flags and ordinary columns are not personal
    for name, typ in [("CustomerID", "text"), ("AddressID", "integer"), ("EmailOptIn", "boolean"),
                      ("ProductName", "text"), ("ZipCode", "text"), ("OrderDate", "date")]:
        assert pii.classify(name, typ, ["x"] * 5) is None
    # a neutral name but the values give it away
    assert pii.classify("Contact", "text", ["a@b.dk", "c@d.com", "e@f.org"])["reason"] == "the shape of the values"
    assert pii.classify("Ref", "text", ["010203-1234", "111180-2345", "280590-3456"])["class"] == "national id"
    assert pii.classify("Ref", "text", ["4111111111111111", "5500005555555559", "340000000000009"])["class"] == "bank or card number"
    assert pii.classify("Ref", "integer", ["0102031234", "1111802345", "2805903456"]) is None  # plain digits: too common
    assert pii.classify("Ref", "text", ["x1", "x2", "x3"]) is None


def test_profile_never_stores_the_values(tmp_path):
    src = tmp_path / "people.csv"
    src.write_text("PersonID,FirstName,Email,BirthDate,City\n" + "\n".join(
        f"P{i},Anne{i},anne{i}@example.dk,19{50 + i % 40}-05-0{1 + i % 9},Aarhus" for i in range(30)), encoding="utf-8")
    out = tmp_path / "wiki"
    main(["profile", str(src), "--out", str(out)])
    raw = (out / "_bijoe" / "profile.json").read_text(encoding="utf-8")
    assert "anne1@example" not in raw and "Anne1" not in raw and "1955-05" not in raw
    profile = json.loads(raw)
    cols = {c["name"]: c for c in profile["tables"][0]["columns"]}
    assert cols["Email"]["pii"]["class"] == "email" and "top_values" not in cols["Email"] and "min_value" not in cols["Email"]
    assert cols["Email"]["distinct_count"] == 30 and cols["Email"]["missing_count"] == 0  # measures stay
    assert cols["BirthDate"]["min_value"] == "1950" and "min" not in cols["BirthDate"]  # years only
    assert "pii" not in cols["City"] and cols["City"]["top_values"][0]["value"] == "Aarhus"  # a city is not personal
    assert all(row[1] == pii.MASK and row[2] == pii.MASK and row[0].startswith("P") for row in profile["tables"][0]["sample_rows"])
    story = (out / "data-stories" / "people.md").read_text(encoding="utf-8")
    assert "anne1@example" not in story and "masked" in story and "🔒" in story


def test_mask_option_forces_a_column(tmp_path):
    src = tmp_path / "t.csv"
    src.write_text("Id,Notes\n1,secret one\n2,secret two\n3,secret three\n", encoding="utf-8")
    out = tmp_path / "wiki"
    main(["profile", str(src), "--out", str(out), "--mask", "t.Notes"])
    raw = (out / "_bijoe" / "profile.json").read_text(encoding="utf-8")
    assert "secret" not in raw


def test_check_fails_when_personal_data_is_in_the_wiki(tmp_path):
    src = tmp_path / "t.csv"
    src.write_text("Id,City\n1,Aarhus\n2,Odense\n", encoding="utf-8")
    out = tmp_path / "wiki"
    main(["profile", str(src), "--out", str(out)])
    assert main(["check", str(out)]) == 0
    page = out / "data-stories" / "t.md"
    page.write_text(page.read_text(encoding="utf-8") + "\nContact: anne@example.dk\n", encoding="utf-8")
    assert main(["check", str(out)]) == 1
    assert pii.scan_text("CPR 010203-1234") and pii.scan_text("DK5000400440116243") and not pii.scan_text("Order 12345-6789")


def test_flags_and_secrets():
    assert pii.classify("EmailPromotion", "integer", {"0": 1, "1": 1, "2": 1}.keys()) is None  # a small code, not an address
    assert pii.classify("PasswordHash", "text", ["x"] * 5)["class"] == "credential"
    assert pii.classify("au_id", "text", ["172-32-1176", "213-46-8915", "238-95-7766"])["class"] == "national id"


def test_scan_ignores_decimals_guids_and_coordinates_but_finds_card_numbers():
    assert not pii.scan_text('"iqr": 12.174999999999997, "q3": 4111111111111.1111')
    assert not pii.scan_text("rowguid 4149-8600-5955-5555-4111111111111111-ab")
    assert not pii.scan_text("POINT (4111111111111111.5 55.1234)")
    assert pii.scan_text("card 4111111111111111 expires 12/26") == ["a card number"]
    assert pii.scan_text("card 4111 1111 1111 1111") == ["a card number"]
    assert pii.scan_text("card 4111-1111-1111-1111.") == ["a card number"]


def test_person_names_by_role_and_by_table():
    for col in ("ReviewerName", "AuthorName", "customer_name", "EmployeeName", "CardholderName"):
        assert pii.classify(col, "text", ["x"] * 5)["class"] == "person name", col
    assert pii.classify("Name", "text", ["a", "b", "c"], table="Sales.Customers")["class"] == "person name"
    assert pii.classify("Name", "text", ["a", "b", "c"], table="Production.Product") is None  # not a table about people
    for col in ("CompanyName", "ProductName", "StoreName", "ReviewerID", "FileName"):
        assert pii.classify(col, "text", ["x"] * 5) is None, col
