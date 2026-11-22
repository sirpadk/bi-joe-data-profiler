import json
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from progress_stub import ProgressStub

from bijoe.cli import main
from bijoe.connectors import open_connector
from bijoe.profiler import profile_dataset

SKILL_SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "bi-joe-data-profiler" / "scripts" / "run_bijoe.py"
MARKER = "SECRET_PERSON_Zz9"
EMAIL = "zz9@secret.example"


def bijoe_lines(text: str):
    return [ln for ln in text.splitlines() if ln.startswith("BIJOE ")]


def expected_milestones(n: int):
    return sorted({i for i in range(1, n + 1) if i == 1 or i == n or i % max(1, n // 10) == 0})


def run_stub(monkeypatch, capsys, tmp_path, tables, *extra):
    monkeypatch.setattr(ProgressStub, "TABLES", list(tables))
    code = main(["profile", "stubprog://x", "--out", str(tmp_path / "out"), *extra])
    cap = capsys.readouterr()
    return code, cap


# ---- events at the profiler level -----------------------------------------------------------

def test_profiler_events_order_and_indices():
    events = []
    with open_connector("stubprog://x") as conn:
        profile_dataset(conn, progress=events.append)
    kinds = [e["event"] for e in events]
    assert kinds == ["plan"] + ["table_start", "table_done"] * 3 + ["relationships"]
    assert events[0]["total"] == 3
    starts = [e for e in events if e["event"] == "table_start"]
    dones = [e for e in events if e["event"] == "table_done"]
    assert [e["index"] for e in starts] == [1, 2, 3] == [e["index"] for e in dones]
    assert all(e["total"] == 3 for e in starts + dones)
    assert [e["table"] for e in dones] == ["alpha", "beta", "gamma"]
    assert all(set(e) <= {"event", "index", "total", "table", "rows", "cols", "secs", "elapsed"} for e in dones)


def test_profiler_prints_nothing(capsys):
    with open_connector("stubprog://x") as conn:
        profile_dataset(conn, progress=lambda e: None)
    cap = capsys.readouterr()
    assert cap.out == "" and cap.err == ""


def test_profiler_without_callback_or_timings():
    with open_connector("stubprog://x") as conn:
        tables, rels = profile_dataset(conn)
    assert len(tables) == 3 and all("profile_seconds" in t for t in tables)


def test_failed_event_has_class_only(monkeypatch):
    monkeypatch.setattr(ProgressStub, "FAIL_ON", "beta")
    monkeypatch.setattr(ProgressStub, "FAIL_MSG", MARKER)
    events = []
    with open_connector("stubprog://x") as conn:
        with pytest.raises(RuntimeError, match=MARKER):
            profile_dataset(conn, progress=events.append)
    failed = [e for e in events if e["event"] == "table_failed"]
    assert len(failed) == 1 and failed[0]["error"] == "RuntimeError" and failed[0]["index"] == 2
    assert MARKER not in repr(events)
    assert events[-1]["event"] == "table_failed"  # nothing after the failure


# ---- the printed lines ----------------------------------------------------------------------

def test_cli_line_sequence(monkeypatch, capsys, tmp_path):
    code, cap = run_stub(monkeypatch, capsys, tmp_path, ["alpha", "beta", "gamma"])
    assert code == 0
    lines = bijoe_lines(cap.out)
    assert re.fullmatch(r"BIJOE connect connector=stubprog source=stubprog://x", lines[0])
    assert lines[1] == "BIJOE plan tables=3"
    shapes = []
    for ln in lines[2:]:
        m = re.fullmatch(r"BIJOE table (\d+)/3 start (\w+)", ln)
        if m:
            shapes.append(("start", int(m[1]), m[2]))
            continue
        m = re.fullmatch(r"BIJOE table (\d+)/3 done rows=3 cols=2 secs=\d+\.\d elapsed=\d+\.\d (\w+)", ln)
        if m:
            shapes.append(("done", int(m[1]), m[2]))
            continue
        m = re.fullmatch(r"BIJOE progress (\d+)/3 pct=(\d+) elapsed=\d+\.\d", ln)
        if m:
            shapes.append(("progress", int(m[1]), int(m[2])))
            continue
        if re.fullmatch(r"BIJOE relationships secs=\d+\.\d", ln):
            shapes.append(("rel",))
        elif re.fullmatch(r"BIJOE done tables=3 failed=0 secs=\d+\.\d", ln):
            shapes.append(("done-all",))
        else:
            pytest.fail(f"unexpected line: {ln}")
    assert shapes == [
        ("start", 1, "alpha"), ("done", 1, "alpha"), ("progress", 1, 33),
        ("start", 2, "beta"), ("done", 2, "beta"), ("progress", 2, 66),
        ("start", 3, "gamma"), ("done", 3, "gamma"), ("progress", 3, 100),
        ("rel",), ("done-all",),
    ]


def test_tables_option_plans_two(monkeypatch, capsys, tmp_path):
    code, cap = run_stub(monkeypatch, capsys, tmp_path, ["alpha", "beta", "gamma"], "--tables", "alpha,gamma")
    assert code == 0
    lines = bijoe_lines(cap.out)
    assert "BIJOE plan tables=2" in lines
    assert any(ln.startswith("BIJOE table 2/2 done") and ln.endswith(" gamma") for ln in lines)
    assert lines[-1].startswith("BIJOE done tables=2 failed=0")


@pytest.mark.parametrize("n", [1, 2, 3, 9, 10, 11, 25, 100])
def test_milestones(monkeypatch, capsys, tmp_path, n):
    code, cap = run_stub(monkeypatch, capsys, tmp_path, [f"t{i:03d}" for i in range(1, n + 1)])
    assert code == 0
    got = []
    for ln in bijoe_lines(cap.out):
        m = re.match(r"BIJOE progress (\d+)/(\d+) ", ln)
        if m:
            got.append(int(m[1]))
    assert got == expected_milestones(n)  # ascending, no duplicates, first and last always present
    assert len(set(got)) == len(got) and got[0] == 1 and got[-1] == n
    assert [ln for ln in bijoe_lines(cap.out) if ln.startswith(f"BIJOE progress {n}/{n} ")][0].count("pct=100 ") == 1


def test_empty_source_reports_plan_zero_then_error(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(ProgressStub, "TABLES", [])
    code = main(["profile", "stubprog://x", "--out", str(tmp_path / "out")])
    cap = capsys.readouterr()
    assert "BIJOE plan tables=0" in cap.out
    assert code == 2 and "No tables found" in cap.err  # existing error path; note: no BIJOE done line


def test_failure_line_class_only_and_exception_propagates(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(ProgressStub, "TABLES", ["alpha", "beta", "gamma"])
    monkeypatch.setattr(ProgressStub, "FAIL_ON", "beta")
    monkeypatch.setattr(ProgressStub, "FAIL_MSG", "kaboom")
    with pytest.raises(RuntimeError, match="kaboom"):  # main() only catches ConnectorError/FileNotFound/ValueError
        main(["profile", "stubprog://x", "--out", str(tmp_path / "out")])
    out = capsys.readouterr().out
    lines = bijoe_lines(out)
    failed = [ln for ln in lines if " failed " in ln]
    assert len(failed) == 1
    assert re.fullmatch(r"BIJOE table 2/3 failed secs=\d+\.\d error=RuntimeError beta", failed[0])
    assert not any(ln.startswith("BIJOE done") for ln in lines)
    assert "kaboom" not in out
    assert not (tmp_path / "out" / "index.md").exists()


def test_failure_with_secret_message_valueerror(monkeypatch, capsys, tmp_path):
    """ValueError IS caught by main(): the message may go to stderr (existing path), never to a BIJOE line."""
    monkeypatch.setattr(ProgressStub, "TABLES", ["alpha", "beta"])
    monkeypatch.setattr(ProgressStub, "FAIL_ON", "beta")
    monkeypatch.setattr(ProgressStub, "FAIL_EXC", ValueError)
    monkeypatch.setattr(ProgressStub, "FAIL_MSG", f"bad value {MARKER} {EMAIL}")
    code = main(["profile", "stubprog://x", "--out", str(tmp_path / "out")])
    cap = capsys.readouterr()
    assert code == 2
    assert MARKER not in cap.out and EMAIL not in cap.out
    assert "error=ValueError beta" in cap.out
    assert not any(ln.startswith("BIJOE done") for ln in bijoe_lines(cap.out))


def test_table_name_with_space_and_non_ascii(monkeypatch, capsys, tmp_path):
    code, cap = run_stub(monkeypatch, capsys, tmp_path, ["Fakta Salg", "Prøve_ÆØÅ"])
    assert code == 0
    lines = bijoe_lines(cap.out)
    assert "BIJOE table 1/2 start Fakta Salg" in lines
    assert "BIJOE table 2/2 start Prøve_ÆØÅ" in lines


def test_table_name_with_newline_stays_one_line(monkeypatch, capsys, tmp_path):
    code, cap = run_stub(monkeypatch, capsys, tmp_path, ["a\nBIJOE done tables=9 failed=0 secs=0.0"])
    lines = bijoe_lines(cap.out)
    assert sum(1 for ln in lines if ln.startswith("BIJOE done")) == 1


def test_csv_non_ascii_file_name(tmp_path, capsys):
    d = tmp_path / "src"
    d.mkdir()
    (d / "Prøve_ÆØÅ.csv").write_text("id,v\n1,a\n", encoding="utf-8")
    (d / "with space.csv").write_text("id,v\n1,a\n", encoding="utf-8")
    assert main(["profile", str(d), "--out", str(tmp_path / "o")]) == 0
    out = capsys.readouterr().out
    assert "BIJOE table 1/2 start Prøve_ÆØÅ" in out
    assert "BIJOE table 2/2 start with space" in out


# ---- CSV end to end ---------------------------------------------------------------------------

def _csv_folder(tmp_path: Path) -> Path:
    d = tmp_path / "people"
    d.mkdir()
    (d / "customers.csv").write_text(
        f"cust_id,name,email,note\n1,{MARKER},{EMAIL},hello\n2,Ann Other,{EMAIL},x\n3,Bo,b@b.test,y\n", encoding="utf-8")
    (d / "orders.csv").write_text(f"order_id,cust_id,memo\n1,1,{MARKER}\n2,2,ok\n", encoding="utf-8")
    (d / "Prøve_ÆØÅ.csv").write_text(f"id,who\n1,{MARKER}\n", encoding="utf-8")
    (d / "line items.csv").write_text("id,order_id\n1,1\n2,2\n", encoding="utf-8")
    return d


@pytest.mark.parametrize("extra", [[], ["--no-values"], ["--mask", "customers.note,orders.memo"]])
def test_cli_csv_end_to_end_and_no_row_values(tmp_path, capsys, extra):
    src = _csv_folder(tmp_path)
    out = tmp_path / "out"
    assert main(["profile", str(src), "--out", str(out), *extra]) == 0
    cap = capsys.readouterr()
    lines = bijoe_lines(cap.out)
    assert lines[0].startswith("BIJOE connect") and lines[1] == "BIJOE plan tables=4"
    assert lines[-1].startswith("BIJOE done tables=4 failed=0")
    idx = []
    for ln in lines:
        m = re.match(r"BIJOE table (\d+)/4 done", ln)
        if m:
            idx.append(int(m[1]))
    assert idx == [1, 2, 3, 4]
    for text in (cap.out, cap.err):
        assert MARKER not in text and "zz9@" not in text and "Ann Other" not in text
    prof = json.loads((out / "_bijoe" / "profile.json").read_text(encoding="utf-8"))
    new_fields = json.dumps([prof["timings"], [t["profile_seconds"] for t in prof["tables"]]])
    assert MARKER not in new_fields and "zz9" not in new_fields
    assert set(prof["timings"]) == {"total_seconds", "connect_seconds", "list_seconds", "tables_seconds",
                                    "relationships_seconds"}
    assert main(["render", str(out)]) == 0
    capsys.readouterr()
    stories = list((out / "data-stories").glob("*.md"))
    assert len(stories) == 4
    for md in stories:
        text = md.read_text(encoding="utf-8")
        assert re.search(r"^<i>Profiled in .*.</i>$", text, re.M), md.name
    footers = [ln for p in out.rglob("*.md") for ln in p.read_text(encoding="utf-8").splitlines()
               if ln.startswith("<i>Profil")]
    assert footers and all(MARKER not in f and "zz9" not in f for f in footers)
    assert re.search(r"^<i>Profiling took .*\(connecting .*, tables .*, relationships .*\)\.</i>$",
                     (out / "index.md").read_text(encoding="utf-8"), re.M)


def test_secret_exception_not_on_stdout(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(ProgressStub, "TABLES", ["alpha", "beta"])
    monkeypatch.setattr(ProgressStub, "FAIL_ON", "alpha")
    monkeypatch.setattr(ProgressStub, "FAIL_EXC", ValueError)
    monkeypatch.setattr(ProgressStub, "FAIL_MSG", f"bad value {MARKER} {EMAIL}")
    assert main(["profile", "stubprog://x", "--out", str(tmp_path / "o")]) == 2
    cap = capsys.readouterr()
    assert MARKER not in cap.out and EMAIL not in cap.out


# ---- live output through a real process ----------------------------------------------------

def test_lines_arrive_before_process_exits(tmp_path):
    """Stdout is a pipe: the plan and first-table-start lines must be readable while the process still runs."""
    d = tmp_path / "big"
    d.mkdir()
    rows = "\n".join(f"{i},name{i},{i * 7 % 1000}" for i in range(400_000))
    (d / "a_big.csv").write_text("id,name,n\n" + rows + "\n", encoding="utf-8")
    (d / "b_small.csv").write_text("id,x\n1,2\n", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, str(SKILL_SCRIPT), "profile", str(d), "--out", str(tmp_path / "o"),
         "--sample-rows", "400000"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8")
    alive_at_start = None
    seen = []
    try:
        for line in proc.stdout:
            seen.append(line.rstrip())
            if line.startswith("BIJOE table 1/2 start"):
                alive_at_start = proc.poll() is None
        proc.wait(timeout=180)
    finally:
        if proc.poll() is None:
            proc.kill()
    assert any(s == "BIJOE plan tables=2" for s in seen)
    assert alive_at_start, "the table-start line only became readable after the process ended"
    assert proc.returncode == 0
    assert any(s.startswith("BIJOE done") for s in seen)


# ---- the Monitor filter quoted in SKILL.md ---------------------------------------------------

MONITOR_FILTER = r"BIJOE (plan|progress|relationships|done|table [0-9]+/[0-9]+ failed)"


def test_skill_md_quotes_the_filter():
    skill = (SKILL_SCRIPT.parents[1] / "SKILL.md").read_text(encoding="utf-8")
    assert MONITOR_FILTER in skill


def test_monitor_filter_matches_only_the_milestone_lines(monkeypatch, capsys, tmp_path):
    code, cap = run_stub(monkeypatch, capsys, tmp_path, ["alpha", "beta", "gamma"])
    matched = [ln for ln in cap.out.splitlines() if re.search(MONITOR_FILTER, ln)]
    kinds = [ln.split()[1] for ln in matched]
    assert kinds == ["plan", "progress", "progress", "progress", "relationships", "done"]
    assert not any(" start " in ln or " done rows=" in ln for ln in matched)
    assert not any(re.search(MONITOR_FILTER, ln) for ln in cap.out.splitlines() if not ln.startswith("BIJOE"))


def test_monitor_filter_matches_failed_line(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(ProgressStub, "TABLES", ["alpha", "beta"])
    monkeypatch.setattr(ProgressStub, "FAIL_ON", "beta")
    with pytest.raises(RuntimeError):
        main(["profile", "stubprog://x", "--out", str(tmp_path / "o")])
    matched = [ln for ln in capsys.readouterr().out.splitlines() if re.search(MONITOR_FILTER, ln)]
    assert [ln.split()[1] for ln in matched] == ["plan", "progress", "table"]
    assert " failed " in matched[-1]


def test_monitor_filter_is_not_fooled_by_table_names(monkeypatch, capsys, tmp_path):
    code, cap = run_stub(monkeypatch, capsys, tmp_path, ["order failed log"])
    assert not any(re.search(MONITOR_FILTER, ln) for ln in cap.out.splitlines() if " start " in ln or " done rows=" in ln)


def test_monitor_filter_in_grep_E(monkeypatch, capsys, tmp_path):
    import shutil
    grep = shutil.which("grep") or r"C:\Program Files\Git\usr\bin\grep.exe"
    if not Path(grep).exists() and not shutil.which("grep"):
        pytest.skip("grep not available")
    monkeypatch.setattr(ProgressStub, "TABLES", ["alpha", "beta"])
    monkeypatch.setattr(ProgressStub, "FAIL_ON", "beta")
    with pytest.raises(RuntimeError):
        main(["profile", "stubprog://x", "--out", str(tmp_path / "o")])
    text = capsys.readouterr().out
    got = subprocess.run([grep, "-E", MONITOR_FILTER], input=text, capture_output=True, text=True).stdout.splitlines()
    assert got == [ln for ln in text.splitlines() if re.search(MONITOR_FILTER, ln)]
    assert len(got) == 3
