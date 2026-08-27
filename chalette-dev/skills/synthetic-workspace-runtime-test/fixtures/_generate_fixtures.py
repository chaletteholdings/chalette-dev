#!/usr/bin/env python3
"""Deterministic generator for the four synthetic workspace fixtures.

    python _generate_fixtures.py --cr1 ~/repos/cr1        # regenerate all four
    python _generate_fixtures.py --cr1 ~/repos/cr1 --check # validate, write nothing

WHY A GENERATOR AND NOT HAND-WRITTEN JSON
-----------------------------------------
fixture-spec.md mandates a quarterly shape-refresh against the real workspace's
SHAPE (never its content). Hand-maintaining 1500 events across four fixtures
through a refresh is not realistic; regenerating from a spec is. The generator
is the fixture source of truth -- edit it, re-run, commit the output.

It is deterministic: a fixed seed and fixed base dates, so re-running produces a
byte-identical tree and a no-op diff. No wall-clock, no RNG-without-seed.

IT READS THE LIVE SCHEMA RATHER THAN TRUSTING THE SPEC
------------------------------------------------------
The 0.1-skeleton metadata was pinned to plugin 3.13.8-3.14.0 and its content
assumptions had rotted by 4.8.0. Concretely: degraded_workspace was specced to
use `followup_pack_drafted` as an UNSANCTIONED event type for the Bug #43
detection test -- but that type was since added to events.schema.json, so it is
legal now and would silently stop testing anything.

So this generator resolves "unsanctioned" against the live enum at generation
time and ASSERTS the types it plants are genuinely absent from it. If a future
schema addition legalises one, generation FAILS LOUDLY instead of quietly
producing a fixture that no longer tests the thing it exists to test. Same
principle as the guard-that-cannot-guard fix in cr1 #32.

SYNTHETIC DATA ONLY
-------------------
Names come from cr1's own approved placeholder allowlist, read live out of
tests/run_no_real_customer_names_test.py (APPROVED_FIRST_NAMES x
APPROVED_SURNAMES). Emails use example.com. Nothing here is derived from any
real workspace.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import random
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

# Fixed clock. Fixtures must be byte-stable across runs.
BASE_DATE = "2026-05-01"
BASE_TS = f"{BASE_DATE}T09:00:00"
SEED = 20260715


def _iso(day_offset: int, hour: int = 9, minute: int = 0) -> str:
    """Deterministic ISO-8601 timestamp, `day_offset` days after BASE_DATE."""
    import datetime as dt

    base = dt.datetime.fromisoformat(BASE_TS)
    return (base + dt.timedelta(days=day_offset, hours=hour - 9, minutes=minute)).isoformat(
        timespec="seconds"
    )


# ---------------------------------------------------------------- live schema

def load_schema_enum(cr1: Path) -> set[str]:
    p = cr1 / "command-room" / "shared" / "data-schemas" / "events.schema.json"
    if not p.is_file():
        sys.exit(f"FATAL: events.schema.json not found at {p}\nPass --cr1 <path-to-cr1-clone>.")
    return set(json.loads(p.read_text(encoding="utf-8"))["properties"]["type"]["enum"])


def load_approved_names(cr1: Path) -> tuple[list[str], list[str]]:
    """Read the placeholder allowlist out of cr1's own guard, so this generator
    cannot drift from the names that repo considers safe."""
    p = cr1 / "command-room" / "tests" / "run_no_real_customer_names_test.py"
    if not p.is_file():
        sys.exit(f"FATAL: name guard not found at {p}")
    spec = importlib.util.spec_from_file_location("_nameguard", p)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except SystemExit:
        pass
    return sorted(mod.APPROVED_FIRST_NAMES), sorted(mod.APPROVED_SURNAMES)


ORG_NAMES = [
    "Acme Co", "Northstar Partners", "Category Company", "Bluebird Group",
    "Cedar Works", "Harbor Labs", "Ivory Systems", "Juniper Holdings",
    "Keystone Partners", "Lantern Group", "Meridian Works", "Nimbus Labs",
    "Orchard Co", "Pinnacle Group", "Quarry Partners", "Ridgeline Co",
    "Summit Works", "Tidal Systems", "Vantage Group", "Wayfare Co",
]

PROJECT_NAMES = [
    "Series A Raise", "Board Cadence", "Hiring Slate", "Pricing Review",
    "Platform Migration", "Customer Advisory", "Annual Planning", "Vendor Consolidation",
    "Brand Refresh", "Data Hygiene", "Partner Program", "Support Rework",
    "Compliance Pass", "Market Expansion", "Retention Push",
]


def make_person(idx: int, first: str, last: str, *, email: bool = True,
                org_id: str | None = None, unattributed: bool = False) -> dict:
    p = {
        "id": f"person_{idx:03d}",
        "canonical_name": f"{first} {last}",
        "first_seen": _iso(idx % 30),
        "status": "active",
        "aliases": [],
        "nicknames": [],
        "project_ids": [],
        "emails": [],
        "phones": [],
        "affiliation_ids": [],
        "connections": [],
    }
    if email:
        p["email"] = f"{first.lower()}.{last.lower()}{idx}@example.com"
        p["emails"] = [p["email"]]
    else:
        # Bug #44 -- dead-chrome / send-class no-email case.
        p["email"] = None
    if unattributed:
        # No org, flagged for enrichment -- the backfill target shape.
        p["primary_org_id"] = None
        p["needs_enrichment"] = True
    elif org_id:
        p["primary_org_id"] = org_id
        p["org_id"] = org_id
    return p


def make_org(idx: int, name: str, *, domains: bool = True) -> dict:
    o = {
        "id": f"org_{idx:03d}",
        "canonical_name": name,
        "status": "active",
        "aliases": [],
        "domains": [],
        "inferred_from": [],
        "first_seen": _iso(idx % 20),
    }
    if domains:
        slug = name.lower().replace(" ", "")
        o["domains"] = [f"{slug}.example.com"]
    # else: Bug #1 backfill test -- org with no domains.
    return o


def make_project(idx: int, name: str, *, status: str = "active",
                 org_id: str | None = None, owner: str | None = None) -> dict:
    return {
        "id": f"project_{idx:03d}",
        "folder_name": name,
        "display_name": name,
        "status": status,
        "kind": "initiative",
        "first_seen": _iso(idx % 25),
        "org_id": org_id,
        "owner_person_id": owner,
        "stakeholder_person_ids": [],
        "cross_refs": [],
        "success_criteria": [],
    }


def event(seq: int, etype: str, source_skill: str, day: int, data: dict,
          *, person_ids: list[str] | None = None, org_ids: list[str] | None = None,
          thread: str | None = None, supersedes: int | None = None) -> dict:
    e = {
        "seq": seq,
        "ts": _iso(day),
        "type": etype,
        "source_skill": source_skill,
        "primary_thread_id": thread,
        "related_thread_ids": [],
        "classification_confidence": None,
        "person_ids": person_ids or [],
        "org_ids": org_ids or [],
        "data": data,
    }
    if supersedes is not None:
        e["supersedes_seq"] = supersedes
    return e


def entities_doc(people: list[dict], orgs: list[dict], projects: list[dict],
                 *, writer: str, workspace: dict | None = None) -> dict:
    d = {
        "version": 1,
        "last_updated": BASE_TS,
        "last_writer": writer,
        "entities": {"people": people, "projects": projects, "orgs": orgs},
    }
    if workspace is not None:
        d["workspace"] = workspace
    return d


def aliases_doc(people_maps: list[dict], org_maps: list[dict], project_maps: list[dict]) -> dict:
    return {
        "version": 1,
        "last_updated": BASE_TS,
        "last_writer": "workspace-manager",
        "mappings": {"people": people_maps, "projects": project_maps, "orgs": org_maps},
    }


def alias(raw: str, canonical_id: str, conf: float = 1.0) -> dict:
    return {
        "raw": raw,
        "canonical_id": canonical_id,
        "confidence": conf,
        "added_ts": BASE_TS,
        "added_by": "workspace-manager",
    }


def mark_primary(people: list[dict]) -> dict:
    """A production client install always has a workspace owner; benchmark Arm A
    (BENCH1, fixture v1.1) replicates a fanned-out install, and the capture
    gate's party-only mode needs the owner identity to route commitments.
    Prefers Sam so the degraded fixture keeps Sam Sample (not Sam Stone) as
    the owner of the collision pair."""
    primary = next((p for p in people if p["canonical_name"] == "Sam Sample"), None)
    if primary is None:
        primary = next((p for p in people if p["canonical_name"].split()[0] == "Sam"),
                       people[0])
    primary["is_primary_user"] = True
    return {
        "user_timezone": "America/Los_Angeles",
        "brain_name": "Atlas",
        "primary_user_id": primary["id"],
        "first_name": primary["canonical_name"].split()[0],
    }


CLAUDE_MD = """# Command Room workspace

Synthetic fixture workspace. Not a real customer workspace; every entity here is
generated placeholder data.

## Substrate

- `_hq/data/entities.json` -- people, orgs, projects
- `_hq/data/events.jsonl` -- append-only event log
- `_hq/data/aliases.json` -- canonical-name registry

## Rules

- events.jsonl is append-only. Never rewrite it.
- All writes go through `atomic_append_jsonl`.
- Superseded files move to `_archive/`; nothing is deleted.
"""


def client_claude_md(spec: dict) -> str:
    """Render the client-layer CLAUDE.md a fanned-out install ships (BENCH1
    amendment 2, 2026-08-26; source shape: cr1 references/claude-md-template.md).
    Populated fixtures get the client layer; a fixture with no primary user
    (fresh_install) keeps the pre-onboarding stub, which is faithful to Day-1.
    The four IMPORTANT bullets carry the template's idempotency marker phrases
    verbatim -- do not reword them here independently of the template."""
    ents = spec["entities"]["entities"]
    ws = spec["entities"].get("workspace") or {}
    people = ents["people"]
    primary = next((p for p in people if p.get("is_primary_user")), None)
    if primary is None:
        return CLAUDE_MD
    orgs = {o["id"]: o["canonical_name"] for o in ents["orgs"]}
    org = orgs.get(primary.get("org_id") or primary.get("primary_org_id") or "", "the company")
    first = ws.get("first_name", primary["canonical_name"].split()[0])
    others = [p for p in people if not p.get("is_primary_user")][:15]
    projects = [p for p in ents["projects"] if p.get("status") == "active"][:12]

    lines = [
        f"# {first}'s Command Room",
        "",
        "## Me",
        f"{primary['canonical_name']}, CEO at {org}. Synthetic fixture operator "
        "(placeholder roster; not a real customer).",
        "",
        "## Quick Commands",
        '- "let\'s work" → fast context load · "what\'s going on" → full briefing · '
        '"go [project]" → jump into a project · "end session" → save everything',
        "- Paste a meeting transcript → it gets processed automatically",
        "",
        "## Session Rules",
        "- On first activation each session: read _hq/MASTER_TRACKER.md. When the answer "
        "might be in the hot cache below, use it before reading files.",
        '- "end session" always updates session notes for every project touched — never skip. '
        "Ask 2-3 grounded questions per interaction — specific, not generic.",
        "- IMPORTANT: Every email — a draft, a reply, a follow-up, or one that comes up "
        "mid-task — goes through the **email-writer** skill, end to end; it carries my saved "
        "voice, length, and review rules, and composing anywhere else loses all of them. "
        "Never write email text directly with a mail connector tool.",
        "- IMPORTANT: Every Command Room widget — commitments, staff meeting, any row-list "
        "or action card — is produced by `widget_transport.render_and_persist` and its "
        "returned `html` passed to show_widget **byte-exact**; never hand-compose, restyle, "
        "or re-derive widget HTML — hand-built widgets skip the validators and have shipped "
        "stale rows and broken wire formats.",
        "- IMPORTANT: After a successful render, the show_widget call with `transport[\"html\"]` "
        "is not optional — relay the render_and_persist page before any prose (summarizing as "
        "text strips my one-tap actions); text-instead-of-widget only when the transport itself "
        "failed or `pagination[\"over_budget\"]` is set, and then say so explicitly.",
        '- IMPORTANT: Any research ask — "research [X]", "deep dive on [X]", "look into [X]", '
        '"background on [person]" — runs through the **research** skill, never the generic '
        "built-in deep-research skill; the built-in one can't see my workspace and its findings "
        "evaporate. The reply names which source tier actually ran, in one line.",
        "",
        "## Preferences",
        "- **Draft posture (queue-on-click):** Show the editable draft first — nothing touches "
        "your mail drafts until you click Save draft or Send; on that click it is saved to your "
        "mail Drafts (never auto-sent), with the draft record + voice snapshot written at the "
        "same moment.",
        "",
        "## People",
        "| Who | Full Name | Role / Context |",
        "|-----|-----------|----------------|",
    ]
    for p in others:
        nick = p["canonical_name"].split()[0]
        porg = orgs.get(p.get("org_id") or p.get("primary_org_id") or "", "—")
        lines.append(f"| **{nick}** | {p['canonical_name']} | {porg} |")
    lines += [
        "→ Full list: _hq/PEOPLE.md",
        "",
        "## Active Projects",
        "| Project | Status | Next Action |",
        "|---------|--------|-------------|",
    ]
    for pr in projects:
        lines.append(f"| **{pr['display_name']}** | {pr['status']} | — |")
    lines += [
        "→ Details: _hq/MASTER_TRACKER.md",
        "",
        "## Workspace",
        "- Tracker: _hq/MASTER_TRACKER.md · Context: _hq/BUSINESS_CONTEXT.md · "
        "People: _hq/PEOPLE.md",
        f"- Project notes: [Project Name]/SESSION_NOTES_{first.upper()}.md",
        "- Email holds: structured sender-scope overrides on your accounts — ask to add or "
        "remove a held sender/domain any time. Never stored in this file.",
        "",
    ]
    return "\n".join(lines)

SURFACE_SKILLS = [
    ("morning-briefing", "morning_brief"),
    ("orchestrator-inbox", "inbox"),
    ("orchestrator-commitments", "commitments"),
    ("orchestrator-dont-forget", "pulse"),
    ("orchestrator-upcoming-meetings", "upcoming_meetings"),
    ("orchestrator-past-meetings", "past_meetings"),
    ("orchestrator-friday-wrap", "friday_wrap"),
]


def _pack_run(seq: int, skill: str, kind: str, day: int) -> dict:
    """I3/I4 -- every surface fire writes exactly one pack_run with kind populated."""
    return event(seq, "pack_run", skill, day, {
        "kind": kind,
        "surfaced": 3,
        "duration_ms": 1200 + (seq % 400),
    })


# ------------------------------------------------------------ clean_workspace

def build_clean(firsts: list[str], lasts: list[str], enum: set[str]) -> dict:
    rng = random.Random(SEED)
    # 10 distinct first names -> no first-name collisions (metadata contract).
    people = [make_person(i + 1, firsts[i], lasts[0], org_id=f"org_{(i % 5) + 1:03d}")
              for i in range(10)]
    orgs = [make_org(i + 1, ORG_NAMES[i]) for i in range(5)]
    projects = [make_project(i + 1, PROJECT_NAMES[i], org_id=f"org_{i + 1:03d}",
                             owner=f"person_{i + 1:03d}") for i in range(3)]

    events: list[dict] = []
    seq = 1
    day = 0
    # 200 events, human-counter seqs, spread across the 7 canonical surfaces.
    while seq <= 200:
        skill, kind = SURFACE_SKILLS[seq % len(SURFACE_SKILLS)]
        pid = f"person_{(seq % 10) + 1:03d}"
        pick = seq % 5
        if pick == 0:
            events.append(_pack_run(seq, skill, kind, day))
        elif pick == 1:
            events.append(event(seq, "meeting", "meeting-notes", day, {
                "title": f"Sync {seq}", "duration_min": 30,
            }, person_ids=[pid], thread=f"project_{(seq % 3) + 1:03d}"))
        elif pick == 2:
            events.append(event(seq, "commitment", "meeting-notes", day, {
                "kind": "todo", "text": f"Follow up on item {seq}", "owner_id": pid,
            }, person_ids=[pid]))
        elif pick == 3:
            events.append(event(seq, "decision", "decision-log", day, {
                "title": f"Decision {seq}", "summary": f"Chose option A for item {seq}",
                "rationale": "Lower risk.",
            }, person_ids=[pid]))
        else:
            events.append(event(seq, "email_drafted", "email-writer", day, {
                "recipient_id": pid, "subject": f"Re: item {seq}", "register": "short_direct",
            }, person_ids=[pid]))
        seq += 1
        if seq % 7 == 0:
            day += 1

    # I11 -- canonical closure shape: commitment_resolved.data.commitment_id = closed seq.
    open_commitments = [e["seq"] for e in events if e["type"] == "commitment"][:6]
    for i, target in enumerate(open_commitments):
        events.append(event(200 + i + 1, "commitment_resolved", "apply-choices", day + 1, {
            "commitment_id": target, "id": f"cmt_{target:06d}", "resolution": "done",
        }))

    aliases_people = [alias(f"{firsts[i]}", f"person_{i + 1:03d}") for i in range(10)]
    aliases_people += [alias(f"{firsts[i].lower()}.{lasts[0].lower()}{i + 1}@example.com",
                             f"person_{i + 1:03d}") for i in range(10)]
    aliases_orgs = [alias(ORG_NAMES[i].split()[0], f"org_{i + 1:03d}") for i in range(5)]
    return {
        "entities": entities_doc(people, orgs, projects, writer="workspace-manager",
                                 workspace=mark_primary(people)),
        "events": events,
        "aliases": aliases_doc(aliases_people, aliases_orgs, []),
        "malformed": [],
    }


# ----------------------------------------------------------- mature_workspace

def build_mature(firsts: list[str], lasts: list[str], enum: set[str]) -> dict:
    rng = random.Random(SEED + 1)
    people = []
    for i in range(80):
        first = firsts[i % len(firsts)]
        last = lasts[i % len(lasts)]
        # 12 unattributed (no org, needs_enrichment) -- the backfill target shape.
        unattributed = i >= 68
        people.append(make_person(i + 1, first, last,
                                  org_id=None if unattributed else f"org_{(i % 20) + 1:03d}",
                                  unattributed=unattributed))
    # Bug #1 -- 4 orgs deliberately carry no domains.
    orgs = [make_org(i + 1, ORG_NAMES[i], domains=(i % 5 != 0)) for i in range(20)]
    projects = []
    for i in range(15):
        status = "paused" if i < 3 else "active"  # 3 paused, 12 active
        projects.append(make_project(i + 1, PROJECT_NAMES[i], status=status,
                                     org_id=f"org_{(i % 20) + 1:03d}",
                                     owner=f"person_{(i % 80) + 1:03d}"))

    events: list[dict] = []
    # 1200 human-counter seqs, then 300 nano-epoch artifacts (Bug #41 dual shape).
    day = 0
    for seq in range(1, 1201):
        skill, kind = SURFACE_SKILLS[seq % len(SURFACE_SKILLS)]
        pid = f"person_{(seq % 80) + 1:03d}"
        # Bug #34 -- legacy person_added for the first 500, canonical after.
        if seq % 11 == 0:
            etype = "person_added" if seq <= 500 else "person_created"
            events.append(event(seq, etype, "people-crm", day, {
                "person_id": pid, "name": people[(seq % 80)]["canonical_name"],
            }, person_ids=[pid]))
        elif seq % 5 == 0:
            events.append(_pack_run(seq, skill, kind, day))
        elif seq % 3 == 0:
            events.append(event(seq, "commitment", "meeting-notes", day, {
                "kind": "todo", "text": f"Mature item {seq}", "owner_id": pid,
            }, person_ids=[pid]))
        else:
            events.append(event(seq, "meeting", "meeting-notes", day, {
                "title": f"Mature sync {seq}", "duration_min": 30,
            }, person_ids=[pid], thread=f"project_{(seq % 15) + 1:03d}"))
        if seq % 6 == 0:
            day += 1
    # Nano-epoch artifacts: next_seq.py ignores anything above 1e10.
    nano_base = 1_770_000_000_000_000_000
    for i in range(300):
        events.append(event(nano_base + i * 1_000_000, "meeting", "meeting-notes", day, {
            "title": f"Nano-epoch artifact {i}", "duration_min": 15,
        }, person_ids=[f"person_{(i % 80) + 1:03d}"]))

    # Aliases: first half nested-shape entries, second half flat -- both read paths.
    ap = [alias(f"{firsts[i % len(firsts)]} {lasts[i % len(lasts)]}", f"person_{i + 1:03d}")
          for i in range(100)]
    ao = [alias(ORG_NAMES[i % 20].split()[0], f"org_{(i % 20) + 1:03d}") for i in range(50)]
    apr = [alias(PROJECT_NAMES[i % 15], f"project_{(i % 15) + 1:03d}") for i in range(50)]
    return {
        "entities": entities_doc(people, orgs, projects, writer="workspace-manager",
                                 workspace=mark_primary(people)),
        "events": events,
        "aliases": aliases_doc(ap, ao, apr),
        "flat_aliases": True,
        "malformed": "shatter",
    }


# --------------------------------------------------------- degraded_workspace

def build_degraded(firsts: list[str], lasts: list[str], enum: set[str]) -> dict:
    # Unsanctioned types resolved against the LIVE enum, then asserted.
    candidates = ["scaffold_proposed", "followup_pack_drafted", "widget_freelanced",
                  "legacy_note_added", "adhoc_export_made"]
    unsanctioned = [c for c in candidates if c not in enum]
    if len(unsanctioned) < 2:
        sys.exit(
            "FATAL: fewer than 2 genuinely-unsanctioned event types available.\n"
            f"  candidates: {candidates}\n"
            f"  still illegal: {unsanctioned}\n"
            "The schema grew and this fixture would no longer test Bug #43 detection.\n"
            "Add new genuinely-unsanctioned candidates above."
        )
    unsanctioned = unsanctioned[:2]

    people = []
    # Bug #19 -- first-name collision: same first name, distinct full names.
    people.append(make_person(1, "Sam", "Sample", org_id="org_001"))
    people.append(make_person(2, "Sam", "Stone", org_id="org_002"))
    # Bug #44 -- 2 people with no email on file.
    people.append(make_person(3, "Bo", "Sample", email=False, org_id="org_001"))
    people.append(make_person(4, "Rio", "Stone", email=False, org_id="org_003"))
    for i in range(4, 15):
        people.append(make_person(i + 1, firsts[i % len(firsts)], lasts[i % len(lasts)],
                                  org_id=f"org_{(i % 8) + 1:03d}"))
    orgs = [make_org(i + 1, ORG_NAMES[i]) for i in range(8)]
    projects = [make_project(i + 1, PROJECT_NAMES[i], org_id=f"org_{i + 1:03d}",
                             owner=f"person_{i + 1:03d}") for i in range(5)]

    events: list[dict] = []
    seq = 1
    day = 0
    # Bug #22 -- decision fallback chain: title-only / summary-only / notes-only.
    events.append(event(seq, "decision", "decision-log", day, {"title": "Title only decision"}))
    seq += 1
    events.append(event(seq, "decision", "decision-log", day, {"summary": "Summary only, no title"}))
    seq += 1
    events.append(event(seq, "decision", "decision-log", day, {"notes": "Notes only, no title or summary"}))
    seq += 1

    # Bug #24 -- commitment_resolved events that are really supersedes.
    events.append(event(seq, "commitment", "meeting-notes", day, {
        "kind": "todo", "text": "Original scope", "owner_id": "person_001",
    }, person_ids=["person_001"]))
    original = seq
    seq += 1
    events.append(event(seq, "commitment_resolved", "apply-choices", day + 1, {
        "commitment_id": original, "id": f"cmt_{original:06d}",
        "resolution": "superseded by revised scope",
        "_mislabeled": "actually a supersede, not a completion (Bug #24 detection target)",
    }, supersedes=original))
    seq += 1
    events.append(event(seq, "commitment", "meeting-notes", day + 1, {
        "kind": "todo", "text": "Revised scope", "owner_id": "person_001",
    }, person_ids=["person_001"]))
    second = seq
    seq += 1
    events.append(event(seq, "commitment_resolved", "apply-choices", day + 2, {
        "commitment_id": second, "id": f"cmt_{second:06d}",
        "resolution": "superseded again",
        "_mislabeled": "actually a supersede (Bug #24 detection target)",
    }, supersedes=second))
    seq += 1

    # I12 -- show_my_list cascade: a discuss-wrapper plus its source commitment.
    events.append(event(seq, "commitment", "meeting-notes", day + 2, {
        "kind": "todo", "text": "Source commitment for cascade", "owner_id": "person_002",
    }, person_ids=["person_002"]))
    source = seq
    seq += 1
    events.append(event(seq, "commitment", "show-my-list", day + 2, {
        "kind": "discuss", "text": "Discuss wrapper", "owner_id": "person_002",
        "wraps_seq": source,
    }, person_ids=["person_002"]))
    seq += 1

    # Bug #43 -- unsanctioned event types (verified illegal against the live enum).
    for i in range(5):
        events.append(event(seq, unsanctioned[i % 2], "follow-up-ritual", day + 3, {
            "note": f"Deliberately unsanctioned type for Bug #43 detection ({i})",
        }))
        seq += 1

    while seq <= 100:
        skill, kind = SURFACE_SKILLS[seq % len(SURFACE_SKILLS)]
        if seq % 4 == 0:
            events.append(_pack_run(seq, skill, kind, day + 3))
        else:
            events.append(event(seq, "meeting", "meeting-notes", day + 3, {
                "title": f"Degraded sync {seq}", "duration_min": 30,
            }, person_ids=[f"person_{(seq % 15) + 1:03d}"]))
        seq += 1

    ap = [alias("Sam", "person_001", 0.5), alias("Sam Sample", "person_001"),
          alias("Sam Stone", "person_002")]
    ap += [alias(f"{firsts[i % len(firsts)]} {lasts[i % len(lasts)]}", f"person_{i + 1:03d}")
           for i in range(4, 15)]
    ao = [alias(ORG_NAMES[i].split()[0], f"org_{i + 1:03d}") for i in range(8)]
    apr = [alias(PROJECT_NAMES[i], f"project_{i + 1:03d}") for i in range(5)]
    while len(ap) + len(ao) + len(apr) < 30:
        apr.append(alias(f"{PROJECT_NAMES[len(apr) % 5]} alt{len(apr)}",
                         f"project_{(len(apr) % 5) + 1:03d}", 0.7))
    return {
        "entities": entities_doc(people, orgs, projects, writer="workspace-manager",
                                 workspace=mark_primary(people)),
        "events": events,
        "aliases": aliases_doc(ap, ao, apr),
        "malformed": [],
        "unsanctioned_used": unsanctioned,
    }


# ------------------------------------------------------------- fresh_install

def build_fresh(firsts: list[str], lasts: list[str], enum: set[str]) -> dict:
    return {
        "entities": {
            "version": 1,
            "last_updated": BASE_TS,
            "last_writer": "command-room-onboarding",
            "entities": {"people": [], "projects": [], "orgs": []},
            # Bug #36 -- no brain_name set, so the first fire prompts for one.
            # workspace_settings stub is present but EMPTY: the schema types
            # user_timezone as string (not ["string","null"]), so an unset value
            # must be omitted, not written as null. A Day-1 workspace genuinely
            # has no timezone yet -- that is the shape onboarding fills in.
            "workspace": {},
        },
        "events": [event(1, "other", "command-room-onboarding", 0, {
            "note": "Workspace initialized. First event is a marker -- no data.",
        })],
        "aliases": None,  # no aliases.json on a Day-1 workspace
        "malformed": [],
    }


# ------------------------------------------------------------------- shatter

# Sub-bug #14b, from the real workspace's lines 1628-1636: a write tore mid-object
# and left the object's keys stranded as bare JSON strings, one per line, followed
# by a truncated event. Layer 1 (JSONDecodeError) only catches the last one; the
# seven bare strings parse FINE as top-level JSON strings, and pre-v3.13.8 readers
# then did `line.get(...)` on a str -> AttributeError. That is the actual crash
# class, and it is why load_events_defensively must reject non-dict top-level
# lines as well as unparseable ones. A fixture with only broken-JSON lines would
# not test the half that actually broke.
SHATTER_LINES = [
    '"seq"',
    '"ts"',
    '"type"',
    '"source_skill"',
    '"person_ids"',
    '"org_ids"',
    '"data"',
    '{"seq": 107, "ts": "2026-05-15T09:00:00", "type": "meeting", "source_skill": "meeting-not',
]


def write_events(path: Path, events: list[dict], malformed: str | list) -> int:
    """Write events.jsonl. Returns the count of malformed lines injected."""
    lines = [json.dumps(e, ensure_ascii=False) for e in events]
    injected = 0
    if malformed == "shatter":
        # Metadata contract: lines 100-107 carry the shatter pattern.
        at = 99
        lines[at:at] = SHATTER_LINES
        injected = len(SHATTER_LINES)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return injected


def write_fixture(name: str, spec: dict, out_root: Path, meta_updates: dict) -> dict:
    root = out_root / name
    # Rebuild from scratch so a removed key never lingers. .metadata.json is
    # regenerated below, so nothing is lost.
    if root.exists():
        shutil.rmtree(root)
    (root / "_hq" / "data").mkdir(parents=True, exist_ok=True)
    (root / "_hq" / "views").mkdir(parents=True, exist_ok=True)
    (root / "_hq" / "connectors").mkdir(parents=True, exist_ok=True)
    (root / "_hq" / ".system").mkdir(parents=True, exist_ok=True)

    data = root / "_hq" / "data"
    (data / "entities.json").write_text(
        json.dumps(spec["entities"], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    injected = write_events(data / "events.jsonl", spec["events"], spec.get("malformed", []))

    if spec.get("aliases") is not None:
        doc = spec["aliases"]
        if spec.get("flat_aliases"):
            # Second half flat: {raw: canonical_id} alongside the nested list, so
            # both defensive read paths get exercised in one file.
            flat = {}
            for m in doc["mappings"]["people"][50:]:
                flat[m["raw"]] = m["canonical_id"]
            doc = dict(doc)
            doc["mappings"] = dict(doc["mappings"])
            doc["mappings"]["people"] = doc["mappings"]["people"][:50]
            doc["flat"] = flat
        (data / "aliases.json").write_text(
            json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    (data / "classifier_feedback.jsonl").write_text("", encoding="utf-8")
    (root / "CLAUDE.md").write_text(client_claude_md(spec), encoding="utf-8")
    write_connectors(root / "_hq" / "connectors", spec)

    meta = dict(meta_updates)
    meta["_generated_by"] = "_generate_fixtures.py (deterministic; do not hand-edit)"
    (root / ".metadata.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "name": name,
        "people": len(spec["entities"]["entities"]["people"]),
        "orgs": len(spec["entities"]["entities"]["orgs"]),
        "projects": len(spec["entities"]["entities"]["projects"]),
        "events": len(spec["events"]),
        "malformed": injected,
    }


def write_connectors(cdir: Path, spec: dict) -> None:
    """Canned connector responses, sized so all 7 canonical surfaces can fire
    without touching an external API."""
    people = spec["entities"]["entities"]["people"]
    n = len(people)
    threads = []
    for i in range(min(50, max(1, n * 2))):
        p = people[i % n] if n else None
        threads.append({
            "thread_id": f"thread_{i + 1:03d}",
            "subject": f"Re: item {i + 1}",
            "from": (p.get("email") or "noreply@example.com") if p else "noreply@example.com",
            "snippet": f"Synthetic thread body {i + 1}.",
            "ts": _iso(i % 14),
        })
    events_ = []
    for i in range(min(30, max(1, n))):
        p = people[i % n] if n else None
        events_.append({
            "event_id": f"cal_{i + 1:03d}",
            "title": f"Sync {i + 1}",
            "start": _iso(i % 7, hour=10),
            "attendees": [p["email"]] if p and p.get("email") else [],
        })
    transcripts = {}
    for i in range(min(20, max(1, n // 2 or 1))):
        transcripts[f"doc_{i + 1:03d}"] = {
            "transcript": f"Synthetic transcript {i + 1}. Placeholder content only.",
            "attendees": [people[i % n]["canonical_name"]] if n else [],
            "duration": "30m",
        }
    (cdir / "gmail_responses.json").write_text(json.dumps(
        {"gmail_search": {"queries": {"in:inbox newer_than:1d": threads}}},
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (cdir / "calendar_responses.json").write_text(json.dumps(
        {"calendar_list_events": {"windows": {"today": events_[:5], "next_7_days": events_}}},
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (cdir / "granola_responses.json").write_text(json.dumps(
        {"granola_get_transcript": {"doc_ids": transcripts}},
        indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ------------------------------------------------------------------ metadata

FIXTURE_VERSION = "1.1"  # 1.1 (BENCH1, 2026-08-26): client-layer CLAUDE.md + primary user; roster picks up PSCRUB3 (Adan retired)
COMPATIBLE = ["4.8.0"]  # bumped from 3.13.8-3.14.0 per M, 2026-07-15


def metadata(name: str, description: str, characteristics: dict,
             passes: list[str], skips: list[str], **extra) -> dict:
    m = {
        "name": name,
        "description": description,
        "fixture_version": FIXTURE_VERSION,
        "compatible_plugin_versions": COMPATIBLE,
        "status": "POPULATED",
        "characteristics": characteristics,
        "expected_invariants_pass": passes,
        "expected_invariants_skip": skips,
    }
    m.update(extra)
    return m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cr1", default=str(Path.home() / "repos" / "cr1"),
                    help="path to the cr1 clone (for live schema + name allowlist)")
    ap.add_argument("--check", action="store_true",
                    help="validate only; write nothing")
    args = ap.parse_args()

    cr1 = Path(args.cr1).expanduser().resolve()
    enum = load_schema_enum(cr1)
    firsts, lasts = load_approved_names(cr1)
    print(f"cr1                : {cr1}")
    print(f"legal event types  : {len(enum)}")
    print(f"approved names     : {len(firsts)} first x {len(lasts)} surnames "
          f"= {len(firsts) * len(lasts)} unique full names")
    print()

    built = [
        ("clean_workspace", build_clean(firsts, lasts, enum), metadata(
            "clean_workspace",
            "Pristine baseline -- 10 people, 5 orgs, 3 projects, all canonical shapes. "
            "For verifying happy-path doesn't regress.",
            {"people_count": 10, "orgs_count": 5, "projects_count": 3,
             "events_count": 206, "aliases_count": 25,
             "has_malformed_lines": False, "has_dual_shape_seqs": False,
             "has_unsanctioned_events": False, "has_first_name_collisions": False,
             "has_unattributed_people": False, "has_paused_projects": False},
            ["I1", "I2", "I3", "I4", "I5", "I7", "I9", "I10", "I11", "I13",
             "I14", "I15", "I16", "I17"],
            ["I6", "I8", "I12", "I18"])),
        ("mature_workspace", build_mature(firsts, lasts, enum), metadata(
            "mature_workspace",
            "Realistic mature workspace -- 80 people, 20 orgs, 15 projects, 1500 events. "
            "8 malformed events.jsonl lines at 100-107 (Sub-bug #14b shatter: 7 bare-key "
            "JSON strings + 1 truncated event). Mix of nano-epoch + human-counter seqs "
            "(Bug #41). Legacy person_added then canonical person_created (Bug #34). "
            "aliases.json carries BOTH nested and flat shapes. 4 orgs with no domains "
            "(Bug #1). For verifying substrate-hygiene migrations + defensive readers.",
            {"people_count": 80, "orgs_count": 20, "projects_count": 15,
             "events_count": 1500, "aliases_count": 200,
             "has_malformed_lines": True,
             "malformed_line_pattern": "lines 100-107 shattered as 7 bare-key JSON "
                                       "strings + 1 truncated event raising JSONDecodeError",
             "has_dual_shape_seqs": True,
             "dual_shape_split": "1200 human-counter seqs (1..1200) + 300 nano-epoch "
                                 "artifacts (1.77e18+)",
             "has_unsanctioned_events": False,
             "has_first_name_collisions": True,
             "first_name_collision_note": "CHANGED from false, 2026-07-15. The approved "
                                          "placeholder vocabulary is 11 first names x 2 "
                                          "surnames = 22 unique full names; 80 people "
                                          "cannot avoid collisions. It is also the "
                                          "realistic shape -- an 80-person org with zero "
                                          "repeated first names is the 'too clean fixture' "
                                          "failure mode. Collisions exercise entity_resolve, "
                                          "which invariants.md already expects here (I7, "
                                          "'fixture has multi-Daniel collision').",
             "has_unattributed_people": True, "unattributed_count": 12,
             "has_paused_projects": True, "paused_project_count": 3,
             "orgs_without_domains": 4},
            ["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10", "I11",
             "I13", "I14", "I15", "I16", "I17"],
            ["I12", "I18"])),
        ("degraded_workspace", build_degraded(firsts, lasts, enum), None),
        ("fresh_install", build_fresh(firsts, lasts, enum), metadata(
            "fresh_install",
            "Day-1 customer fixture. Empty entities, single seed event, no aliases.json, "
            "no brain_name set (Bug #36 prompt test). For verifying first-fire / "
            "onboarding behavior + M1 widget rendering.",
            {"people_count": 0, "orgs_count": 0, "projects_count": 0,
             "events_count": 1, "aliases_count": 0,
             "has_brain_name_set": False, "has_workspace_settings_stub_only": True},
            ["I1", "I2", "I3", "I4", "I5", "I7", "I9", "I10", "I13", "I14",
             "I15", "I16", "I17"],
            ["I6", "I8", "I11", "I12", "I18"],
            expected_invariants_handle_empty=(
                "I7 (canonical_entity_resolve) handles empty alias graph (returns no "
                "candidates gracefully). I3 (pack_run_written) MUST pass even on first fire."))),
    ]

    # degraded's metadata needs the unsanctioned types the generator actually resolved.
    deg_spec = built[2][1]
    used = deg_spec["unsanctioned_used"]
    built[2] = ("degraded_workspace", deg_spec, metadata(
        "degraded_workspace",
        "Edge-case failure-mode fixture. 2 people sharing a first name with distinct full "
        "names (Bug #19). 2 people with no email (Bug #44 dead-chrome). Decision events "
        "with only title / only summary / only notes (Bug #22 fallback chain). 2 "
        "commitment_resolved events that are actually supersedes (Bug #24). Unsanctioned "
        "event types (Bug #43). show-my-list wrapper + source pair (I12 cascade).",
        {"people_count": 15, "orgs_count": 8, "projects_count": 5,
         "events_count": 100, "aliases_count": 30,
         "has_malformed_lines": False, "has_dual_shape_seqs": False,
         "has_unsanctioned_events": True,
         "unsanctioned_event_types": used,
         "unsanctioned_note": (
             "Resolved against the LIVE events.schema.json enum at generation time and "
             "asserted illegal. The 0.1-skeleton spec named followup_pack_drafted here, "
             "but it was added to the schema by 4.8.0 -- it is legal now and would have "
             "silently stopped testing Bug #43 detection. The generator fails loudly if "
             "fewer than 2 candidates remain illegal."),
         "has_first_name_collisions": True,
         "first_name_collisions": [["Sam Sample", "Sam Stone"]],
         "first_name_collision_note": (
             "The 0.1-skeleton spec used two names that read as real contact data (one "
             "matched a real client surname). Neither was in cr1's approved placeholder "
             "allowlist, so both were replaced with approved placeholders. Flagged to M."),
         "has_unattributed_people": False, "has_paused_projects": False,
         "has_no_email_people": True, "no_email_person_count": 2},
        ["I1", "I2", "I3", "I4", "I7", "I9", "I10_with_warning", "I11", "I12",
         "I13", "I14", "I15", "I16", "I17"],
        ["I5", "I6", "I8", "I18"],
        expected_invariants_fail_intentional=["I10"],
        fail_intentional_note=(
            "I10 (schema_compliance) should FAIL because the fixture deliberately "
            "contains unsanctioned event types -- this verifies the invariant detection "
            "works.")))

    # --- validate before writing -------------------------------------------
    problems = []
    for name, spec, _ in built:
        for e in spec["events"]:
            if e["type"] not in enum:
                if name == "degraded_workspace" and e["type"] in used:
                    continue  # deliberate
                problems.append(f"{name}: illegal event type {e['type']!r} (seq {e['seq']})")
            for req in ("seq", "ts", "type", "source_skill", "data"):
                if req not in e:
                    problems.append(f"{name}: event seq {e.get('seq')} missing {req!r}")
    if problems:
        for p in problems[:20]:
            print("  PROBLEM:", p)
        sys.exit(f"\nFATAL: {len(problems)} schema problem(s); nothing written.")

    if args.check:
        print("--check: validation passed, nothing written.")
        return 0

    print(f"{'fixture':<22}{'people':>7}{'orgs':>6}{'proj':>6}{'events':>8}{'malformed':>11}")
    print("-" * 60)
    for name, spec, meta in built:
        r = write_fixture(name, spec, HERE, meta)
        print(f"{r['name']:<22}{r['people']:>7}{r['orgs']:>6}{r['projects']:>6}"
              f"{r['events']:>8}{r['malformed']:>11}")
    print()
    print(f"degraded unsanctioned types (verified illegal): {used}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
