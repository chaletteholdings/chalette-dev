#!/usr/bin/env python3
"""Guard 3 (TI2) — instruction-layer fences on triage-intake's outbound surfaces.

triage-intake's packet + BACKLOG emission is a PROSE contract: the gate lives in
SKILL.md text, because that text is what actually executes when the skill fires.
Prose with no test behind it is deletable in one careless edit and nothing goes
red — the instruction-layer-gap class (code referenced by zero skill texts is
invisible; the inverse is just as true).

These fences assert the four load-bearing clauses are present and, for the two
that could fail dangerously, that the clause and its trigger sit in the SAME
section (an "if null, refuse" rule three sections away from the write it governs
is not a gate). Each is mutation-verified in the BUILD record by deleting the
clause and watching the matching test go red.

What each fence catches if it goes:

  may_ship gate      — the outbound section silently becomes live on a
                       contractor profile, and a contractor routes work to
                       themselves, writing to a repo clone they were never
                       granted.
  fail-closed refusal — a null/unreadable scrub_roster stops meaning "refuse"
                       and starts meaning "skip the check", which is the
                       org-name leak, shipped.
  staged-only         — triage starts committing (or pushing) to the cr1 clone,
                       which is a repo write nobody reviewed.
  no-auto-substitute  — a roster hit gets silently renamed instead of surfaced,
                       so the operator never learns the row was wrong.

Run: pytest tests/  (from the repo root)
"""

import os
import re

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SKILL_MD = os.path.join(
    REPO_ROOT, "chalette-dev", "skills", "triage-intake", "SKILL.md"
)
TEMPLATES_MD = os.path.join(
    REPO_ROOT, "chalette-dev", "skills", "triage-intake",
    "references", "spec-templates.md",
)


def _text(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _outbound_section():
    """The 'Routing work out' section body — heading to the next H2."""
    text = _text(SKILL_MD)
    m = re.search(r"^## Routing work out\b.*?$", text, re.M)
    assert m, (
        "triage-intake/SKILL.md has no '## Routing work out' section — the entire "
        "TI2 outbound contract (packet + BACKLOG, both may_ship-gated) is gone"
    )
    rest = text[m.end():]
    nxt = re.search(r"^## ", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def test_outbound_section_is_may_ship_gated():
    body = _outbound_section()
    assert "may_ship" in body, (
        "the 'Routing work out' section does not mention may_ship — without the "
        "gate a contractor profile emits packets to itself and writes to a cr1 clone"
    )
    # The gate must be stated as a gate, not merely referenced in passing.
    assert re.search(r"gated on .{0,40}`?may_ship", body) or re.search(
        r"may_ship.{0,40}(only|gate)", body, re.I
    ), "may_ship appears in the section but not as the gating condition"


def test_fail_closed_refusal_clause_present_and_in_scope():
    body = _outbound_section()
    assert "scrub roster unavailable" in body, (
        "the verbatim refusal line ('scrub roster unavailable — BACKLOG/packet "
        "emission disabled') is missing: a null/unreadable scrub_roster would "
        "degrade from REFUSE to skip-the-check, which is the org-name leak shipped"
    )
    assert re.search(r"null.{0,120}refuse", body, re.I | re.S), (
        "the section states a refusal line but never ties it to a null/unreadable "
        "roster — fail-closed must be stated as the rule, not implied"
    )
    assert "scrub_roster" in body, (
        "the refusal clause does not name the scrub_roster key it governs"
    )
    # REVIEW_TI2 F-1: a roster that reads fine but yields no names (Drive-sync
    # truncation is a live failure mode on this substrate) must also refuse.
    # Without this the gate degrades to permit-everything on a readable file.
    assert re.search(r"zero names|no names", body, re.I), (
        "the fail-closed rule covers null/missing/unreadable but not an "
        "empty-but-readable roster — a truncated roster would silently degrade "
        "the gate to permit-everything (REVIEW_TI2 F-1)"
    )


def test_no_auto_substitute_clause_present():
    body = _outbound_section()
    assert re.search(r"[Nn]ever auto-substitute", body), (
        "the 'never auto-substitute a name' clause is gone — a roster hit could be "
        "silently renamed instead of surfaced for rewrite"
    )


@pytest.mark.parametrize(
    "needle",
    [
        "never committed",
        "never pushed",
    ],
)
def test_staged_only_clause_in_writer_contract(needle):
    """The staged-only posture must live in the Writer contract, not only in prose.

    The Writer contract is the section a future editor reads to learn what this
    skill may write. AC-4: this clause carries verbatim.
    """
    text = _text(SKILL_MD)
    m = re.search(r"^## Writer contract\s*$", text, re.M)
    assert m, "triage-intake/SKILL.md has no '## Writer contract' section"
    contract = text[m.end():]
    assert needle in contract, (
        f"the Writer contract no longer says '{needle}' — the BACKLOG write is a "
        f"repo write, and stage-and-show is the only thing keeping a triage session "
        f"from committing to the cr1 clone unreviewed"
    )
    assert "git add" in contract, (
        "the Writer contract does not name `git add` as the stopping point"
    )


def test_writer_contract_bounds_outbound_surfaces_to_two():
    text = _text(SKILL_MD)
    m = re.search(r"^## Writer contract\s*$", text, re.M)
    contract = text[m.end():]
    assert "BACKLOG.md" in contract and "PACKET_" in contract, (
        "the Writer contract must name BOTH outbound surfaces explicitly — an "
        "unenumerated contract is what a silent widening hides behind"
    )
    assert re.search(r"[Nn]o other file in any repo is ever written", contract), (
        "the Writer contract's closed-set clause ('no other file in any repo is "
        "ever written by triage') is gone"
    )


def test_packet_body_defers_to_cr1_template_by_reference():
    """D5: one spec grammar on the contributor's side of the fence.

    The packet body must POINT AT cr1's checked-in templates/TEMPLATE_SPEC.md, not
    carry a copy — a second copy drifts, and the contributor's fork already has the
    real one.
    """
    body = _text(TEMPLATES_MD)
    assert "templates/TEMPLATE_SPEC.md" in body, (
        "the packet template no longer references cr1's templates/TEMPLATE_SPEC.md"
    )
    assert re.search(r"do not copy it here|not by copy|by reference", body, re.I), (
        "the packet template must say the body defers BY REFERENCE — without that, "
        "the next editor inlines a copy of TEMPLATE_SPEC.md and it drifts"
    )


def test_packet_requires_pr_description_slots():
    body = _text(TEMPLATES_MD)
    for needle in ("Deviations", "mutation check", "Files touched"):
        assert needle.lower() in body.lower(), (
            f"the packet's PR-description requirements block is missing "
            f"'{needle}' — a fork contributor's PR description IS the build "
            f"record (filled records are never committed), so a dropped slot is a "
            f"permanently missing record"
        )


def test_packet_self_containment_rule_present():
    body = _outbound_section()
    assert re.search(r"[Ss]elf-containment rule", body), (
        "the packet self-containment rule is gone — packets could carry workspace "
        "paths or operator-overlay values to a fork contributor"
    )
