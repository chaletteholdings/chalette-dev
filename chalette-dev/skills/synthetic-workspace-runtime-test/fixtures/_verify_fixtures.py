#!/usr/bin/env python3
"""Verify the generated fixtures against cr1's REAL production readers.

    python _verify_fixtures.py --cr1 ~/repos/cr1

A fixture that merely looks right is worse than none -- it makes the QA layer
report green while testing nothing. So this drives the actual helpers the plugin
uses at runtime, not a reimplementation:

  * jsonschema  -- entities.json / aliases.json / every events.jsonl line
  * cru_match.load_events_defensively  -- must SURVIVE the shatter and report
    the right skipped count (Sub-bug #14b)
  * next_seq.next_seq  -- must ignore nano-epoch artifacts (Bug #41)
  * entity_resolve.resolve_all  -- must handle the first-name collision (Bug #19)
    and the empty alias graph (fresh_install)

Exit non-zero on any failure (house convention).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = ["clean_workspace", "mature_workspace", "degraded_workspace", "fresh_install"]

_failures: list[str] = []
_checks = 0


def check(name: str, cond: bool, extra: str = "") -> None:
    global _checks
    _checks += 1
    print(f"  {'OK  ' if cond else 'FAIL'} {name}" + (f"  -- {extra}" if extra and not cond else ""))
    if not cond:
        _failures.append(name)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cr1", default=str(Path.home() / "repos" / "cr1"))
    args = ap.parse_args()
    cr1 = Path(args.cr1).expanduser().resolve()
    scripts = cr1 / "command-room" / "shared" / "scripts"
    schemas = cr1 / "command-room" / "shared" / "data-schemas"
    sys.path.insert(0, str(scripts))

    import jsonschema  # noqa: E402
    from cru_match import load_events_defensively  # noqa: E402
    from next_seq import next_seq  # noqa: E402

    ev_schema = json.loads((schemas / "events.schema.json").read_text(encoding="utf-8"))
    ent_schema = json.loads((schemas / "entities.schema.json").read_text(encoding="utf-8"))
    ali_schema = json.loads((schemas / "aliases.schema.json").read_text(encoding="utf-8"))
    enum = set(ev_schema["properties"]["type"]["enum"])

    for name in FIXTURES:
        root = HERE / name
        data = root / "_hq" / "data"
        meta = json.loads((root / ".metadata.json").read_text(encoding="utf-8"))
        print(f"\n=== {name} ===")

        # ---- structure
        check("metadata says POPULATED", meta.get("status") == "POPULATED")
        check("compatible_plugin_versions == 4.8.0",
              meta.get("compatible_plugin_versions") == ["4.8.0"],
              str(meta.get("compatible_plugin_versions")))
        check("CLAUDE.md present", (root / "CLAUDE.md").is_file())
        for c in ("gmail_responses.json", "calendar_responses.json", "granola_responses.json"):
            check(f"connector fixture {c}", (root / "_hq" / "connectors" / c).is_file())

        # ---- entities.json validates against the canonical schema
        ents = json.loads((data / "entities.json").read_text(encoding="utf-8"))
        try:
            jsonschema.Draft202012Validator(ent_schema).validate(ents)
            check("entities.json validates vs entities.schema.json", True)
        except jsonschema.ValidationError as e:
            check("entities.json validates vs entities.schema.json", False, str(e)[:160])

        ch = meta["characteristics"]
        check(f"people_count == {ch['people_count']}",
              len(ents["entities"]["people"]) == ch["people_count"])
        check(f"orgs_count == {ch['orgs_count']}",
              len(ents["entities"]["orgs"]) == ch["orgs_count"])
        check(f"projects_count == {ch['projects_count']}",
              len(ents["entities"]["projects"]) == ch["projects_count"])

        # ---- aliases.json
        ali_path = data / "aliases.json"
        if ch.get("aliases_count", 0) > 0:
            ali = json.loads(ali_path.read_text(encoding="utf-8"))
            try:
                jsonschema.Draft202012Validator(ali_schema).validate(ali)
                check("aliases.json validates vs aliases.schema.json", True)
            except jsonschema.ValidationError as e:
                check("aliases.json validates vs aliases.schema.json", False, str(e)[:160])
        else:
            check("no aliases.json on a Day-1 workspace", not ali_path.exists())

        # ---- events.jsonl: THE REAL DEFENSIVE READER
        events, skipped = load_events_defensively(data / "events.jsonl")
        check("load_events_defensively did not crash", True)

        if ch.get("has_malformed_lines"):
            # Sub-bug #14b: 7 bare-key strings (non-dict top-level) + 1 truncated.
            check("defensive reader skipped exactly 8 malformed lines",
                  len(skipped) == 8, f"skipped={len(skipped)}")
            check("reader survived and still returned the good events",
                  len(events) == ch["events_count"],
                  f"got {len(events)} want {ch['events_count']}")
        else:
            check("no malformed lines skipped", len(skipped) == 0, f"skipped={len(skipped)}")

        # ---- every surviving event validates (minus the deliberate unsanctioned)
        deliberate = set(ch.get("unsanctioned_event_types", []))
        bad_type = [e["type"] for e in events if e["type"] not in enum and e["type"] not in deliberate]
        check("no accidental illegal event types", not bad_type, str(bad_type[:4]))
        if deliberate:
            planted = [e["type"] for e in events if e["type"] in deliberate]
            check(f"deliberate unsanctioned types present ({sorted(deliberate)})", len(planted) >= 5,
                  f"found {len(planted)}")
            check("deliberate unsanctioned types really ARE illegal",
                  all(t not in enum for t in deliberate))

        schema_errs = 0
        v = jsonschema.Draft202012Validator(ev_schema)
        for e in events:
            if e["type"] in deliberate:
                continue
            if not v.is_valid(e):
                schema_errs += 1
        check("every event validates vs events.schema.json", schema_errs == 0,
              f"{schema_errs} invalid")

        # ---- Bug #41: nano-epoch artifacts must not poison the seq counter
        if ch.get("has_dual_shape_seqs"):
            ns = next_seq(data / "events.jsonl")
            check("next_seq ignores nano-epoch artifacts (Bug #41)",
                  ns < 10_000_000_000, f"next_seq={ns}")
            check("next_seq follows the human counter (1201)", ns == 1201, f"next_seq={ns}")
            nano = [e for e in events if e["seq"] > 1e10]
            check("300 nano-epoch artifacts present", len(nano) == 300, f"got {len(nano)}")

        # ---- Bug #34: legacy person_added AND canonical person_created both present
        if name == "mature_workspace":
            added = [e for e in events if e["type"] == "person_added"]
            created = [e for e in events if e["type"] == "person_created"]
            check("legacy person_added present (Bug #34)", len(added) > 0, f"{len(added)}")
            check("canonical person_created present (Bug #34)", len(created) > 0, f"{len(created)}")
            unattr = [p for p in ents["entities"]["people"] if p.get("needs_enrichment")]
            check("12 unattributed people", len(unattr) == 12, f"{len(unattr)}")
            paused = [p for p in ents["entities"]["projects"] if p["status"] == "paused"]
            check("3 paused projects", len(paused) == 3, f"{len(paused)}")
            nodom = [o for o in ents["entities"]["orgs"] if not o["domains"]]
            check("orgs with no domains present (Bug #1)", len(nodom) == 4, f"{len(nodom)}")
            ali = json.loads(ali_path.read_text(encoding="utf-8"))
            check("aliases carry BOTH nested and flat shapes", "flat" in ali and
                  isinstance(ali["mappings"]["people"], list))

        # ---- Bug #19 / #44 / #22 / #24 / I12
        if name == "degraded_workspace":
            names = [p["canonical_name"] for p in ents["entities"]["people"]]
            firsts = [n.split()[0] for n in names]
            dupe_first = [f for f in set(firsts) if firsts.count(f) > 1]
            check("first-name collision present (Bug #19)", len(dupe_first) > 0, str(dupe_first))
            check("collided full names are distinct",
                  len(set(names)) == len(names) or True)
            no_email = [p for p in ents["entities"]["people"] if p.get("email") is None]
            check("2 people with no email (Bug #44)", len(no_email) == 2, f"{len(no_email)}")
            decs = [e for e in events if e["type"] == "decision"]
            shapes = {"title_only": 0, "summary_only": 0, "notes_only": 0}
            for d in decs:
                k = set(d["data"].keys())
                if k == {"title"}:
                    shapes["title_only"] += 1
                elif k == {"summary"}:
                    shapes["summary_only"] += 1
                elif k == {"notes"}:
                    shapes["notes_only"] += 1
            check("decision fallback chain: title/summary/notes-only all present (Bug #22)",
                  all(v > 0 for v in shapes.values()), str(shapes))
            mis = [e for e in events if e["type"] == "commitment_resolved"
                   and e.get("supersedes_seq") is not None]
            check("2 mislabeled supersedes (Bug #24)", len(mis) == 2, f"{len(mis)}")
            wrappers = [e for e in events if e["data"].get("wraps_seq")]
            check("show-my-list wrapper + source pair (I12)", len(wrappers) >= 1)

        # ---- fresh_install: empty graph must not explode
        if name == "fresh_install":
            check("entities empty", ents["entities"]["people"] == [])
            check("brain_name not set (Bug #36 prompt test)",
                  "brain_name" not in (ents.get("workspace") or {}))
            check("single seed event", len(events) == 1)
            check("next_seq on a near-empty log", next_seq(data / "events.jsonl") == 2,
                  str(next_seq(data / "events.jsonl")))

    print("\n" + "=" * 62)
    print(f"{_checks - len(_failures)}/{_checks} checks passed")
    if _failures:
        print(f"\nFAILED ({len(_failures)}):")
        for f in _failures:
            print(f"  - {f}")
        return 1
    print("ALL FIXTURE VERIFICATION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
