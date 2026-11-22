"""Command line: bijoe profile | evidence | check | render | connectors"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import SCHEMA_VERSION, __version__, descriptions, wiki
from .connectors import ConnectorError, available, open_connector, plugin_errors
from . import beam, distribution, pii, themes
from .profiler import profile_dataset


def _say(msg: str = "") -> None:
    print(msg, flush=True)


# ---- profile ------------------------------------------------------------------

def cmd_profile(args: argparse.Namespace) -> int:
    out_dir = Path(args.out)
    source = os.path.expandvars(args.source)  # lets credentials live in env vars: postgresql://u:${PGPASS}@h/db
    options: Dict[str, Any] = {}
    if args.schema:
        options["schema"] = args.schema
    tables = [t.strip() for t in args.tables.split(",") if t.strip()] if args.tables else None

    with open_connector(source, args.connector, **options) as conn:
        display = conn.display_source()
        names = conn.list_tables()
        if tables:
            missing = sorted({t.lower() for t in tables} - {n.lower() for n in names})
            if missing:
                raise ConnectorError(f"Tables not found: {', '.join(missing)}. Available: {', '.join(names)}")
        _say(f"Profiling {display} with the '{conn.name}' connector...")
        results, relationships = profile_dataset(
            conn, tables, args.sample_rows, include_values=not args.no_values,
            progress=lambda name: _say(f"  - {name}"),
            mask=pii.parse_forced(args.mask),
        )
        connector_name, source_type = conn.name, conn.source_type

    if not results:
        raise ConnectorError("No tables found in the source.")
    taken: set = set()
    for t in results:
        t["slug"] = wiki.slugify(t["name"], taken)

    name = args.name or _default_name(args.source, display)
    profile = {
        "bijoe_version": __version__,
        "schema_version": SCHEMA_VERSION,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "dataset": {"name": name, "source": display, "source_type": source_type, "connector": connector_name},
        "settings": {
            "sample_rows": args.sample_rows,
            "include_values": not args.no_values,
            "tables": tables,
            "purpose": args.purpose,
            "audience": args.audience,
            "focus": args.focus,
            "theme": themes.resolve(args.theme),
            "mask": args.mask,
        },
        "tables": results,
        "relationships": relationships,
    }
    profile["settings"] = {k: v for k, v in profile["settings"].items() if v is not None}
    wiki.save_profile(out_dir, profile)
    data = descriptions.merge(descriptions.load(out_dir), profile)
    descriptions.save(out_dir, data)
    wiki.render(out_dir, profile, data)

    from_system = sum(1 for t in results if data["tables"][t["name"]]["source"] == "system_metadata")
    pending = sum(1 for t in results if data["tables"][t["name"]]["source"] == "pending")
    _say()
    _say(f"Profiled {len(results)} table(s), {sum(t['row_count'] for t in results):,} rows -> {out_dir / 'index.md'}")
    if from_system:
        _say(f"{from_system} table description(s) taken from source system metadata.")
    if pending:
        _say(f"{pending} description(s) still to write. Next:")
        _say(f"  1. bijoe evidence {out_dir}        (facts to base descriptions on)")
        _say(f"  2. edit {descriptions.path_for(out_dir)}")
        _say(f"  3. bijoe check {out_dir}  then  bijoe render {out_dir}")
    return 0


def _default_name(source: str, display: str) -> str:
    p = Path(source)
    if p.exists():
        return (p.stem if p.is_file() else p.resolve().name) or "dataset"
    tail = display.rstrip("/").split("/")[-1].split("?")[0]
    return tail or "dataset"


# ---- evidence ---------------------------------------------------------------

def _range(c: Dict[str, Any]) -> str:
    if "min" in c:
        return f"{c['min']} → {c['max']}"
    if "min_length" in c:
        return f"len {c['min_length']}–{c['max_length']}"
    return ""


def _flags(c: Dict[str, Any]) -> str:
    flags = []
    if c.get("pii"):
        flags.append(f"PERSONAL DATA ({c['pii']['class']}): values masked, never shown")
    if c.get("primary_key"):
        flags.append("PK")
    if c.get("all_values_unique") and not c.get("missing_count"):
        flags.append("unique")
    if c.get("type_consistency_pct"):
        flags.append(f"{c['type_consistency_pct']}% fit type")
    if c.get("value_kinds"):
        flags.append("mixed: " + ", ".join(f"{k} {v}" for k, v in c["value_kinds"].items()))
    if c.get("leading_zero_count"):
        flags.append(f"{c['leading_zero_count']} leading zeros")
    if c.get("whitespace_padded_count"):
        flags.append(f"{c['whitespace_padded_count']} padded")
    return "; ".join(flags)


def _n(x: Any) -> str:
    return distribution._fmt(float(x), 0.01 if abs(float(x)) < 100 else 1.0)


def _distribution_markdown(t: Dict[str, Any]) -> List[str]:
    out = []
    for c in t["columns"]:
        d = c.get("distribution")
        if not d or d.get("kind") == "none":
            continue
        parts = [d["kind"] + (f" by {d['unit']}" if d.get("unit") else ""), f"shape: {d['shape']}"]
        if d.get("median") is not None:
            parts.append(f"median {_n(d['median'])}, middle half {_n(d['q1'])} to {_n(d['q3'])}")
        o = d.get("outliers")
        if o:
            parts.append("outliers: " + ", ".join(
                x for x in (f"{o['below']:,} below {_n(o['low_fence'])}" if o["below"] else "",
                            f"{o['above']:,} above {_n(o['high_fence'])}" if o["above"] else "") if x))
        if d.get("gap_runs"):
            parts.append(f"{d['gap_runs']} gap(s) with no rows")
        if d["kind"] == "categories":
            top = d["bins"][0]
            parts.append(f"most frequent: {top['label']} {top['pct']:g}%")
        elif d.get("top_share_pct") and d["top_share_pct"] >= 20:
            parts.append(f"most common value holds {d['top_share_pct']:g}% of rows")
        if d.get("sampled"):
            parts.append("from the sample")
        out.append(f"- {c['name']}: " + "; ".join(parts))
    if not out:
        return []
    return ["", "### Distributions (measured)"] + out


def _keys_markdown(t: Dict[str, Any]) -> List[str]:
    k = t.get("keys")
    if not k:
        return []
    scope = f" (first {k['rows_checked']:,} rows only)" if k.get("sampled") else ""
    out = ["", f"### What Identifies a Row (measured{scope})"]
    if k["unique_columns"]:
        out.append("- unique on their own: " + ", ".join(k["unique_columns"]))
    for u in k["unique_combinations"]:
        out.append("- unique together: " + " + ".join(u["columns"]))
    if not k["unique_columns"] and not k["unique_combinations"]:
        out.append("- no column or small combination of the likely columns is unique")
    for c in k["closest_combinations"]:
        out.append(f"- not unique together: {' + '.join(c['columns'])} ({c['distinct']:,} distinct of {c['rows']:,} rows)")
    for p in k["identifier_pairs"]:
        out.append(f"- {p['a']} and {p['b']}: {p['kind']} ({p['a_distinct']:,} and {p['b_distinct']:,} distinct; "
                   f"{p['a_with_several_b']:,} of the first have several of the second, "
                   f"{p['b_with_several_a']:,} of the second have several of the first)")
    return out


def evidence_markdown(profile: Dict[str, Any], table_filter: Optional[str] = None) -> str:
    def cell(v: Any) -> str:
        return str(v).replace("|", "\\|").replace("\n", " ")

    all_names = [t["name"] for t in profile["tables"]]
    out = [f"# Evidence for {profile['dataset']['name']}",
           f"Source: {profile['dataset']['source']} ({profile['dataset']['connector']}) · "
           f"tables: {', '.join(all_names)}"]
    settings = profile.get("settings") or {}
    for key in ("purpose", "audience", "focus"):
        if settings.get(key):
            out.append(f"User-stated {key}: {settings[key]}")
    for t in profile["tables"]:
        if table_filter and t["name"].lower() != table_filter.lower():
            continue
        out += ["", f"## {t['name']}"]
        sample = f" (statistics from first {t['profiled_rows']:,})" if t.get("sampled") else ""
        out.append(f"- rows: {t['row_count']:,}{sample} · columns: {t['column_count']} · "
                   f"duplicate rows: {t.get('duplicate_rows', 0)}")
        out.append(f"- system table comment: {t['comment']!r}" if t.get("comment") else "- system table comment: none")
        if t.get("details"):
            out.append("- details: " + ", ".join(f"{k}={v}" for k, v in t["details"].items()))
        rels = profile.get("relationships") or []
        out.append(f"- BEAM measured: {beam.source_code(t, profile['dataset'])}")
        has_comments = any(c.get("comment") for c in t["columns"])
        head = "| column | declared | inferred | BEAM measured | missing % | distinct | range | flags | top values |"
        if has_comments:
            head += " comment |"
        out += ["", head, "|" + "---|" * (head.count("|") - 1)]
        for c in t["columns"]:
            tops = ", ".join(f"{v['value']} ({v['count']})" for v in c.get("top_values", [])[:5])
            measured = " ".join(x for x in [beam.data_type_code(c)] + beam.measured_column_codes(t, c, rels) if x)
            row = (f"| {cell(c['name'])} | {cell(c.get('declared_type', ''))} | {c['inferred_type']} | "
                   f"{measured} | {c.get('missing_pct', 0)} | {c['distinct_count']:,} | {cell(_range(c))} | "
                   f"{cell(_flags(c))} | {cell(tops)} |")
            if has_comments:
                row += f" {cell(c.get('comment', ''))} |"
            out.append(row)
        out += _keys_markdown(t)
        out += _distribution_markdown(t)
        mine = [r for r in rels if table_filter is None or table_filter.lower() in
                (r["from_table"].lower(), r["to_table"].lower())]
        if mine and (table_filter or t is profile["tables"][-1]):
            out += ["", "### Relationships (measured)"]
            for r in mine:
                out.append(f"- {r['from_table']}.{r['from_column']} → {r['to_table']}.{r['to_column']}: "
                           f"{r['matched_values']} of {r['checked_values']} values found ({r['coverage_pct']}%)"
                           + (" [sampled]" if r.get("sampled") else ""))
    if not table_filter and not (profile.get("relationships") or []):
        out += ["", "### Relationships (measured)", "- none found by column name and value matching"]
    return "\n".join(out) + "\n"


def cmd_evidence(args: argparse.Namespace) -> int:
    profile = wiki.load_profile(Path(args.dir))
    if args.table and args.table.lower() not in {t["name"].lower() for t in profile["tables"]}:
        raise ConnectorError(f"Table '{args.table}' is not in the profile")
    sys.stdout.write(evidence_markdown(profile, args.table))
    return 0


# ---- check / render ---------------------------------------------------------

def _report(problems: List[tuple]) -> Dict[str, int]:
    counts = {"error": 0, "warning": 0, "todo": 0}
    for level, where, msg in problems:
        counts[level] += 1
        _say(f"{level.upper():8} {where}: {msg}")
    _say(f"{counts['error']} error(s), {counts['warning']} warning(s), {counts['todo']} still to write")
    return counts


def cmd_check(args: argparse.Namespace) -> int:
    out_dir = Path(args.dir)
    problems = descriptions.lint(wiki.load_profile(out_dir), descriptions.load(out_dir))
    for rel, what in pii.scan_wiki(out_dir):
        problems.append(("error", rel, f"looks like it contains {what}; personal data must never be saved in the wiki. "
                         "Remove it, and re-run profile with --mask Table.Column for the column it came from"))
    counts = _report(problems)
    return 1 if counts["error"] or (args.strict and (counts["warning"] or counts["todo"])) else 0


def cmd_render(args: argparse.Namespace) -> int:
    out_dir = Path(args.dir)
    profile = wiki.load_profile(out_dir)
    data = descriptions.load(out_dir)
    counts = _report(descriptions.lint(profile, data))
    if counts["error"] and not args.force:
        _say("Not rendered: fix the errors first (or pass --force).")
        return 1
    if args.theme:
        profile.setdefault("settings", {})["theme"] = themes.resolve(args.theme)
        wiki.save_profile(out_dir, profile)
    written = wiki.render(out_dir, profile, data)
    _say(f"Theme: {wiki.current_theme()}")
    _say(f"Wrote {len(written)} page(s). Start at {written[0]}")
    return 0


def cmd_connectors(args: argparse.Namespace) -> int:
    for cls in available():
        missing = cls.missing_requirements()
        status = "ready" if not missing else f"needs: pip install {cls.install_hint or ' '.join(missing)}"
        _say(f"{cls.name:12} {cls.label}\n{'':12} [{status}]")
    for name, err in plugin_errors().items():
        _say(f"{name:12} plugin failed to load: {err}")
    return 0


# ---- entry point --------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="bijoe", description="BI Joe data profiler: profile data into a Markdown wiki of data stories.")
    p.add_argument("--version", action="version", version=f"bijoe {__version__}")
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("profile", help="profile a source and write the wiki")
    pr.add_argument("source", help="CSV file or folder, .xlsx file, SQLite file, or database URL (env vars like ${PGPASSWORD} are expanded)")
    pr.add_argument("--out", "-o", default="bijoe-profile", help="output folder for the wiki (default: bijoe-profile)")
    pr.add_argument("--name", help="dataset name shown in the wiki (default: from the source)")
    pr.add_argument("--connector", help="force a connector instead of auto-detecting (see `bijoe connectors`)")
    pr.add_argument("--tables", help="comma-separated list of tables to profile (default: all)")
    pr.add_argument("--schema", help="database schema(s) to read: one name, a comma-separated list, or 'all' for every non-system schema (database sources only)")
    pr.add_argument("--sample-rows", type=int, default=100_000, help="max rows per table used for statistics (default: 100000)")
    pr.add_argument("--no-values", action="store_true", help="do not record example values (use for sensitive data)")
    pr.add_argument("--purpose", help="why the profile is being made, in the user's words")
    pr.add_argument("--audience", help="who will read it, in the user's words")
    pr.add_argument("--focus", help="what matters most to the user, in their words")
    pr.add_argument("--mask", help="comma-separated Table.Column names to mask as personal data, on top of what is detected automatically")
    pr.add_argument("--theme", help=f"colour theme of the tables: {', '.join(themes.names())}, or 'light' (default: light-gray)")
    pr.set_defaults(func=cmd_profile)

    ev = sub.add_parser("evidence", help="print the facts to base descriptions on")
    ev.add_argument("dir")
    ev.add_argument("--table", help="only this table")
    ev.set_defaults(func=cmd_evidence)

    ck = sub.add_parser("check", help="check descriptions.json for invented or weak descriptions")
    ck.add_argument("dir")
    ck.add_argument("--strict", action="store_true", help="also fail on warnings and unwritten descriptions")
    ck.set_defaults(func=cmd_check)

    rd = sub.add_parser("render", help="rebuild the wiki pages from profile.json + descriptions.json")
    rd.add_argument("dir")
    rd.add_argument("--force", action="store_true", help="render even if the check finds errors")
    rd.add_argument("--theme", help=f"switch the colour theme: {', '.join(themes.names())}, or 'light'; it is remembered for later renders")
    rd.set_defaults(func=cmd_render)

    co = sub.add_parser("connectors", help="list available data connectors")
    co.set_defaults(func=cmd_connectors)
    return p


def main(argv: Optional[List[str]] = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")  # Windows consoles default to a legacy code page
        except (AttributeError, ValueError):
            pass
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except (ConnectorError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
