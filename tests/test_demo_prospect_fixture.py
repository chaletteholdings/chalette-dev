#!/usr/bin/env python3
"""Demo prospect workspace fixture — contract lock (demo1 train, unit 01).

The fixture at tests/fixtures/demo_prospect_workspace/ is the REFERENCE SHAPE
for the future demo-prospect-workspace generator skill: a miniature, fully
synthetic prospect workspace (real workspaces mix real research with
clearly-marked synthesized operating data; the fixture is synthetic
end-to-end). Whatever this test asserts IS the contract the generator must
reproduce. Covers (house convention: check(name, cond) prints OK/FAIL, exit 1
on any failure, auto-discovered by run_all.py; stdlib + jsonschema):

  - find_workspace_root resolves a child path to the fixture root (the
    _hq/data/entities.json anchor works)
  - brand.get_brand(fixture_root) returns the two demo brand values:
    an accent OUTSIDE the standard palette + the exact demo footer line
  - _hq/data/demo_manifest.json exists with generator id
    "demo-prospect-workspace", a created date, and expires = created + 7 days
  - PRIMARY SEAT (demo1 train, unit 03): the manifest names the primary seat
    via primary_person_id (must resolve to a person record) and carries
    primary_is_real_person: true. The person it points at represents the REAL
    call attendee and renders CLEAN — canonical_name does NOT end " (Demo)" —
    exactly as the real prospect org renders clean, because both are true
    data. Disclosure for that person is carried by their synthesized items
    (all "[DEMO]"-prefixed), the document footer, the workspace CLAUDE.md,
    and the manifest.
  - ILLUSTRATIVE MARKER on every synthesized record, in the VISIBLE text the
    surfaces actually render (never a side field):
      * events: every rendered text field starts with "[DEMO] "
        (meeting title/summary, decision text AND rationale, commitment
        title, interaction summary, note text)
      * threads: display_name AND next_step start with "[DEMO] "
      * people: every INVENTED person's canonical_name ends with " (Demo)" —
        a suffix, not a prefix, so names stay sortable, alias-resolvable, and
        readable mid-sentence ("met with Sam Sample (Demo)") while still
        rendering the marker anywhere the canonical name renders. The one
        exception is the manifest's primary seat (above), which stays
        unmarked because it is a real person, not an invention.
  - no real names: person first names come from the guard's approved
    placeholder roster, surnames are Sample/Stone, and every email domain is
    an RFC 2606 example.* domain (consistent with
    run_no_real_customer_names_test.py, which also scans this fixture)
  - substrate shapes match main's CURRENT schema: entities.json /
    aliases.json / every events.jsonl line validate against
    shared/data-schemas/*.schema.json, and event data payloads satisfy the
    per-type alias-groups in event-payloads.schema.json
  - content contract: 1 prospect org, ~10 people, 4 threads, ~3 weeks of
    events anchored to the manifest's fixed reference_date (never today's
    clock), 8 OPEN commitments, monotonic seq
  - _hq/BUSINESS_CONTEXT.md exists and is non-empty: the Layer 1 research
    landing place (true, publicly sourced, UNMARKED, prospect's point of
    view), same name and location command-room-onboarding uses
  - CLAUDE.md at the fixture root instructs sessions to open every reply
    with "read from Demos/<Prospect>" and states the data is illustrative
"""
from __future__ import annotations

import json
import re
import sys

import pytest
from datetime import date, datetime, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
PLUGIN = REPO / "chalette-dev"

# --- cr1 payload resolution -------------------------------------------------
# This skill lives in chalette-dev but leans on THREE helpers that belong to
# the Command Room payload (brand, workspace_root, and the entities schema).
# chalette-dev cannot vendor them — a second copy would drift from the real
# one, which is the whole failure class the shared/ helpers exist to prevent.
# So resolve cr1 the way every other chalette-dev skill does: operator profile
# first, sensible defaults after, env escape hatch, and NEVER a hardcoded
# machine path. `cygpath -m` equivalence matters on Windows (an MSYS
# `/c/Users/...` path resolves to a phantom `C:\c\Users\...`).
#
# If cr1 cannot be found this test SKIPS rather than fails: a contractor
# operator with no cr1 clone has not broken anything. A skip is loud in pytest
# output, which is the honesty bar — it never reports as a pass.
def _resolve_cr1() -> Path | None:
    import json as _json
    import os as _os

    candidates = []
    env = _os.environ.get("CR1_CLONE")
    if env:
        candidates.append(Path(env).expanduser())
    for cfg_name in ("operator.json", "operator.local.json"):
        cfg = PLUGIN / "config" / cfg_name
        if cfg.is_file():
            try:
                val = (_json.loads(cfg.read_text(encoding="utf-8")) or {}).get("cr1_clone")
                if val:
                    candidates.append(Path(val).expanduser())
            except Exception:
                pass
    candidates.append(Path("~/repos/cr1-canonical").expanduser())
    candidates.extend(sorted(
        Path("~/.claude/plugins/marketplaces").expanduser().glob("*/command-room/..")
    ))
    for c in candidates:
        for payload in (c / "command-room", c):
            if (payload / "shared" / "scripts" / "workspace_root.py").is_file():
                return payload
    return None


CR1 = _resolve_cr1()
if CR1 is None:
    pytest.skip(
        "cr1 payload not found — set CR1_CLONE, or add cr1_clone to "
        "chalette-dev/config/operator.json. This fixture test needs Command "
        "Room's brand/workspace_root helpers and entities schema.",
        allow_module_level=True,
    )

sys.path.insert(0, str(CR1 / "shared" / "scripts"))

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import jsonschema  # noqa: E402
from brand import DEFAULT_BRAND, get_brand, validate_brand  # noqa: E402
from workspace_root import find_workspace_root  # noqa: E402

FIXTURE = PLUGIN / "skills" / "demo-prospect-workspace" / "fixtures" / "demo_prospect_workspace"
DATA = FIXTURE / "_hq" / "data"
SCHEMAS = CR1 / "shared" / "data-schemas"

GENERATOR_ID = "demo-prospect-workspace"
DEMO_FOOTER = "DEMO · illustrative data"
EVENT_MARKER = "[DEMO] "
PERSON_MARKER = " (Demo)"

# Mirrors run_no_real_customer_names_test.py APPROVED_FIRST_NAMES /
# APPROVED_SURNAMES (source: references/PRIVACY_POLICY.md). Deliberately
# restated rather than imported: if the guard's roster ever shrinks, this
# fixture must fail HERE with a demo-contract message, not only in the guard.
APPROVED_FIRST_NAMES = frozenset({
    "Sam", "Bo", "Rio", "Skyler", "Mira", "Aria",
    "Bowie", "Lyra", "Quinn", "Dustin",
})
APPROVED_SURNAMES = frozenset({"Sample", "Stone"})
_EXAMPLE_DOMAIN_RE = re.compile(r"(^|\.)example\.(com|org|net)$")

# Which data fields each event type renders as visible text. A marker in a
# side field nothing prints is not a marker — these are the fields the
# existing surfaces (briefs, trackers, decision log, commitment views)
# actually show, per references/DATA_CONTRACT.md + event-payloads.schema.json
# alias groups (decision text lives under one of decision~summary~title;
# commitment text under title).
RENDERED_TEXT_FIELDS = {
    "meeting": ["title", "summary"],
    "decision": ["decision", "summary", "title", "rationale"],
    "commitment": ["title"],
    "interaction": ["summary"],
    "note": ["text"],
}

_failures: list = []


def check(name: str, cond: bool, extra: str = "") -> None:
    print(f"  {'OK  ' if cond else 'FAIL'} {name}"
          f"{(' — ' + extra) if extra and not cond else ''}")
    if not cond:
        _failures.append(name)


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _payload_ok(event: dict, payload_schemas: dict) -> str:
    """'' if the event's data payload satisfies event-payloads.schema.json
    (a custom mini-schema: required is a list of alias-GROUPS, a group is
    satisfied if ANY key in it is present; properties type-check when
    present). Otherwise a short problem description."""
    spec = payload_schemas.get(event.get("type"))
    if not isinstance(spec, dict):
        return ""  # type not covered by the payload schema — nothing to check
    data = event.get("data")
    if not isinstance(data, dict):
        return "data is not an object"
    for group in spec.get("required", []):
        if not any(key in data for key in group):
            return f"no key from required group {group}"
    type_map = {"string": str, "number": (int, float), "boolean": bool,
                "array": list, "object": dict}
    for key, tname in spec.get("properties", {}).items():
        if key in data and tname in type_map \
                and not isinstance(data[key], type_map[tname]):
            return f"data.{key} is not a {tname}"
    return ""


def main() -> int:
    print("=== demo prospect workspace fixture contract ===")

    # ---- fixture exists at all (the red-first gate) ----
    entities_path = DATA / "entities.json"
    check("fixture dir exists", FIXTURE.is_dir(), str(FIXTURE))
    check("substrate anchor _hq/data/entities.json exists",
          entities_path.is_file())
    if _failures:
        # Nothing else can run without the anchor — fail fast, stay readable.
        print(f"\n{len(_failures)} check(s) failed (fixture missing)")
        return 1

    # ---- workspace-root resolution ----
    resolved = find_workspace_root(DATA)
    check("find_workspace_root(child) resolves to the fixture root",
          resolved == FIXTURE.resolve(), f"got {resolved}")

    # ---- brand: the two demo values ----
    brand = get_brand(FIXTURE)
    accent = brand["palette"]["accent"]
    check("demo accent is not any standard-palette color",
          accent not in set(DEFAULT_BRAND["palette"].values()), accent)
    check("footer is exactly the demo disclosure line",
          brand["footer_line"] == DEMO_FOOTER, repr(brand["footer_line"]))
    entities = _load_json(entities_path)
    ws_brand = (entities.get("workspace") or {}).get("brand")
    check("workspace.brand present at entities.json top level (where "
          "brand.get_brand reads it)", isinstance(ws_brand, dict))
    check("workspace.brand passes validate_brand",
          validate_brand(ws_brand) == [], "; ".join(validate_brand(ws_brand)))

    # ---- manifest ----
    manifest_path = DATA / "demo_manifest.json"
    check("manifest _hq/data/demo_manifest.json exists",
          manifest_path.is_file())
    manifest = _load_json(manifest_path) if manifest_path.is_file() else {}
    check("manifest generator id", manifest.get("generator") == GENERATOR_ID,
          repr(manifest.get("generator")))
    created = expires = None
    try:
        created = date.fromisoformat(manifest.get("created", ""))
        expires = date.fromisoformat(manifest.get("expires", ""))
    except ValueError:
        pass
    check("manifest created/expires are ISO dates",
          created is not None and expires is not None)
    check("expires is exactly created + 7 days",
          created is not None and expires == created + timedelta(days=7))
    ref_date = None
    try:
        ref_date = date.fromisoformat(manifest.get("reference_date", ""))
    except ValueError:
        pass
    check("manifest carries a fixed reference_date (events never depend on "
          "today's clock)", ref_date is not None)
    primary_person_id = manifest.get("primary_person_id")
    check("manifest names the primary seat (primary_person_id is a string)",
          isinstance(primary_person_id, str) and bool(primary_person_id),
          repr(primary_person_id))
    check("manifest carries primary_is_real_person: true",
          manifest.get("primary_is_real_person") is True,
          repr(manifest.get("primary_is_real_person")))

    # ---- entities.json: schema + content contract ----
    jsonschema.validate(entities, _load_json(SCHEMAS / "entities.schema.json"))
    check("entities.json validates against entities.schema.json", True)
    inner = entities["entities"]
    people = inner.get("people", [])
    # entities.schema.json's canonical inner key is "projects" (readers fold
    # "threads" as a legacy alias; the schema requires "projects").
    threads = inner.get("projects", [])
    orgs = inner.get("orgs", [])
    check("exactly one prospect org", len(orgs) == 1, f"got {len(orgs)}")
    check("roughly 10 people", 8 <= len(people) <= 12, f"got {len(people)}")
    check("4 threads (projects)", len(threads) == 4, f"got {len(threads)}")

    org = orgs[0] if orgs else {}
    check("prospect org is primary focus with an active status",
          org.get("is_primary_focus") is True and org.get("status") == "active")

    # ---- markers + name safety: people ----
    # The manifest's primary seat is the REAL call attendee: their record
    # renders clean (no " (Demo)" suffix), like the org. Everyone else is
    # invented and stays marked.
    check("manifest primary_person_id resolves to a person record",
          primary_person_id in {p.get("id") for p in people},
          repr(primary_person_id))
    for p in people:
        name = p.get("canonical_name", "")
        if p.get("id") == primary_person_id:
            check(f"primary person {p.get('id')} renders CLEAN "
                  "(no ' (Demo)' suffix)",
                  not name.endswith(PERSON_MARKER), repr(name))
        else:
            check(f"person {p.get('id')} name carries the ' (Demo)' marker",
                  name.endswith(PERSON_MARKER), repr(name))
        bare = name[: -len(PERSON_MARKER)] if name.endswith(PERSON_MARKER) else name
        parts = bare.split()
        check(f"person {p.get('id')} uses approved placeholder name",
              len(parts) == 2 and parts[0] in APPROVED_FIRST_NAMES
              and parts[1] in APPROVED_SURNAMES, bare)
        email = p.get("email", "")
        domain = email.rsplit("@", 1)[-1] if "@" in email else ""
        check(f"person {p.get('id')} email is on an example.* domain",
              bool(_EXAMPLE_DOMAIN_RE.search(domain)), email)

    # ---- markers: threads ----
    for t in threads:
        check(f"thread {t.get('id')} display_name carries the '[DEMO] ' marker",
              t.get("display_name", "").startswith(EVENT_MARKER),
              repr(t.get("display_name")))
        check(f"thread {t.get('id')} next_step carries the '[DEMO] ' marker",
              isinstance(t.get("next_step"), str)
              and t["next_step"].startswith(EVENT_MARKER),
              repr(t.get("next_step")))
        check(f"thread {t.get('id')} carries the folder_name key (nullable, "
              "FOLDERGUARD)", "folder_name" in t)

    # ---- events.jsonl: schema, markers, dates, commitments ----
    events_schema = _load_json(SCHEMAS / "events.schema.json")
    payload_schemas = _load_json(SCHEMAS / "event-payloads.schema.json")
    lines = (DATA / "events.jsonl").read_text(encoding="utf-8").splitlines()
    events = [json.loads(ln) for ln in lines if ln.strip()]
    check("events.jsonl has a realistic volume (>= 20 events)",
          len(events) >= 20, f"got {len(events)}")

    bad_schema = bad_payload = bad_marker = 0
    seqs, times = [], []
    open_commitments = 0
    for ev in events:
        try:
            jsonschema.validate(ev, events_schema)
        except jsonschema.ValidationError as e:
            bad_schema += 1
            print(f"    schema: seq {ev.get('seq')}: {e.message[:100]}")
        problem = _payload_ok(ev, payload_schemas)
        if problem:
            bad_payload += 1
            print(f"    payload: seq {ev.get('seq')}: {problem}")
        seqs.append(ev.get("seq"))
        times.append(datetime.fromisoformat(ev["ts"]))
        fields = RENDERED_TEXT_FIELDS.get(ev.get("type"), [])
        for f in fields:
            val = ev.get("data", {}).get(f)
            if isinstance(val, str) and not val.startswith(EVENT_MARKER):
                bad_marker += 1
                print(f"    marker: seq {ev.get('seq')} data.{f}: {val[:60]!r}")
        if ev.get("type") == "commitment" \
                and ev.get("data", {}).get("status") == "open":
            open_commitments += 1
    check("every event validates against events.schema.json", bad_schema == 0)
    check("every event data payload satisfies event-payloads.schema.json",
          bad_payload == 0)
    check("every rendered event text field starts with '[DEMO] '",
          bad_marker == 0)
    check("seq is monotonically increasing",
          all(b > a for a, b in zip(seqs, seqs[1:])))
    check("exactly 8 open commitments", open_commitments == 8,
          f"got {open_commitments}")

    span = (max(times) - min(times)).days if times else 0
    check("events span roughly 3 weeks", 14 <= span <= 28, f"{span} days")
    if ref_date is not None and times:
        check("all events dated on/before the fixed reference_date",
              max(times).date() <= ref_date)
        check("events end within a week of the reference_date (fresh demo)",
              (ref_date - max(times).date()).days <= 7)

    # ---- aliases.json ----
    aliases = _load_json(DATA / "aliases.json")
    jsonschema.validate(aliases, _load_json(SCHEMAS / "aliases.schema.json"))
    check("aliases.json validates against aliases.schema.json", True)
    known_ids = {p["id"] for p in people} | {t["id"] for t in threads} \
        | {o["id"] for o in orgs}
    all_maps = [m for lst in aliases.get("mappings", {}).values() for m in lst]
    check("aliases.json has mappings and every canonical_id resolves",
          len(all_maps) > 0
          and all(m["canonical_id"] in known_ids for m in all_maps))

    # ---- BUSINESS_CONTEXT.md: the Layer 1 research landing place ----
    # The generated workspace carries its true, publicly-sourced research as
    # _hq/BUSINESS_CONTEXT.md, mirroring command-room-onboarding's convention
    # (same name, same location). Unmarked by design: it is the true layer,
    # written from the prospect's point of view. In the fixture the content
    # is fictional-plausible, but the file must exist and carry substance.
    biz_ctx_path = FIXTURE / "_hq" / "BUSINESS_CONTEXT.md"
    check("_hq/BUSINESS_CONTEXT.md exists (Layer 1 research landing place)",
          biz_ctx_path.is_file(), str(biz_ctx_path))
    biz_ctx = biz_ctx_path.read_text(encoding="utf-8").strip() \
        if biz_ctx_path.is_file() else ""
    check("_hq/BUSINESS_CONTEXT.md is non-empty", len(biz_ctx) > 0)

    # ---- CLAUDE.md ----
    claude_md_path = FIXTURE / "CLAUDE.md"
    check("CLAUDE.md exists at the fixture root", claude_md_path.is_file())
    claude_md = claude_md_path.read_text(encoding="utf-8") \
        if claude_md_path.is_file() else ""
    check("CLAUDE.md instructs opening every reply with 'read from Demos/"
          "<Prospect>'", "read from Demos/" in claude_md)
    check("CLAUDE.md states the data is illustrative",
          "illustrative" in claude_md.lower())

    print()
    if _failures:
        print(f"{len(_failures)} check(s) failed")
        return 1
    print("all checks passed")
    return 0


def test_demo_prospect_fixture_contract() -> None:
    """The whole contract, unchanged from cr1 — one pytest entry point.

    Deliberately NOT re-split into per-check pytest cases: the 60+ checks and
    their exact wording ARE the contract Eric wrote, and a rewrite is where a
    check quietly goes missing. main() already returns non-zero on any failure
    and prints which one.
    """
    assert main() == 0, "demo prospect workspace fixture contract failed — see output above"


if __name__ == "__main__":
    sys.exit(main())
