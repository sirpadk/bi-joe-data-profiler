"""Key measurement: unique combinations and how identifier columns map onto each other."""

from bijoe.keys import measure_keys


def _table(names, types, rows):
    cols = []
    for i, (name, typ) in enumerate(zip(names, types)):
        vals = [r[i] for r in rows]
        cols.append({"name": name, "inferred_type": typ, "distinct_count": len(set(vals)),
                     "all_values_unique": len(set(vals)) == len(vals)})
    return {"columns": cols, "row_count": len(rows)}


def test_unique_combination_is_found_and_supersets_skipped():
    rows = [["E1", "P1", "2022-01-01"], ["E1", "P1", "2022-07-01"], ["E1", "P2", "2022-01-01"],
            ["E2", "P1", "2022-01-01"]]
    t = _table(["EmployeeID", "ProjectID", "StartDate"], ["text", "text", "date"], rows)
    k = measure_keys(t, rows)
    assert [u["columns"] for u in k["unique_combinations"]] == [["EmployeeID", "ProjectID", "StartDate"]]
    assert k["closest_combinations"][0]["columns"] == ["EmployeeID", "ProjectID"]
    assert k["closest_combinations"][0]["distinct"] == 3


def test_identifier_pairs_report_how_they_map():
    rows = [["V1", "A1"], ["V2", "A2"], ["V3", "A3"], ["V3", "A4"]]
    t = _table(["VATNumber", "AccountNo"], ["text", "text"], rows)
    k = measure_keys(t, rows)
    assert k["identifier_pairs"][0]["kind"] == "one-to-many"
    assert k["identifier_pairs"][0]["a_with_several_b"] == 1
