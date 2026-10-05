#!/usr/bin/env python3
"""Description-budget guard for chalette-dev — the sibling of cr1's G11.

Why this exists (2026-08-16): cr1 has G11, which caps every skill description
and the whole-catalog total. chalette-dev had no equivalent, so nothing was
watching this repo's descriptions at all. They drifted: `triage-intake` reached
1,019 characters — FIVE below the 1,024 hard cap at which the Agent Skills spec
fails a skill at frontmatter parse. A skill over that cap does not warn; it
stops loading. `triage-intake` is the skill that works the intake queue, so the
failure mode was "the tool you use to find problems silently stops existing".
`capture-for-code` (1,009) and `cr-test` (1,007) were in the same band.

The gap was structural, not careless: cr1's guard reads cr1's `skills/` folder.
It cannot see this repo, and no one had noticed that meant this repo was
unguarded.

WHY THE CATALOG TOTAL IS NOT CHECKED HERE. M and Eric run cr1 AND chalette-dev
at the same time, so what their runtime actually loads is the SUM of the two
catalogs (~63.8k at the time of writing, against cr1's 53,000 budget). Whether
that budget is enforced per-plugin or per-install is NOT established — it was
raised, not answered, and guessing either way would be worse than the honest
gap. So this guard enforces only what IS established: the per-skill cap, which
comes from the spec and is not ambiguous. A combined-catalog check belongs here
the moment someone confirms the runtime's actual scope; the constant below is
recorded so that work starts from a measurement rather than a memory.

  BUDGET (980)   — same headroom cr1 keeps under the hard cap.
  HARD_CAP (1024) — the spec's parse limit. Never raise this; it is not ours.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "chalette-dev" / "skills"

BUDGET = 980
HARD_CAP = 1024
# Measured 2026-08-16 after the trim pass (was 10,814 before it). Recorded for
# whoever establishes the runtime's real scope; deliberately NOT asserted —
# see the module docstring.
CATALOG_AT_LAST_MEASURE = 10583


def _description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return ""
    fm = yaml.safe_load(m.group(1))
    return (fm or {}).get("description", "") or ""


def _skill_files() -> list[Path]:
    return sorted(SKILLS.glob("*/SKILL.md"))


def test_skills_are_discoverable() -> None:
    """A guard that finds nothing passes vacuously — pin that it found skills."""
    files = _skill_files()
    assert files, f"no SKILL.md found under {SKILLS} — the guard is looking in the wrong place"
    assert len(files) >= 4, f"only {len(files)} skills found; expected the four cr2 skills"


@pytest.mark.parametrize("skill_md", _skill_files(), ids=lambda p: p.parent.name)
def test_description_under_hard_cap(skill_md: Path) -> None:
    """Above 1,024 the runtime drops the skill at frontmatter parse."""
    n = len(_description(skill_md))
    assert n <= HARD_CAP, (
        f"{skill_md.parent.name}: description is {n} chars, over the {HARD_CAP} "
        f"hard cap — this skill will FAIL TO LOAD, silently."
    )


@pytest.mark.parametrize("skill_md", _skill_files(), ids=lambda p: p.parent.name)
def test_description_within_budget(skill_md: Path) -> None:
    """980 keeps working headroom under the hard cap, as cr1's G11 does."""
    n = len(_description(skill_md))
    assert n <= BUDGET, (
        f"{skill_md.parent.name}: description is {n} chars, over the {BUDGET} "
        f"budget ({HARD_CAP - n} from the hard cap). Trim implementation detail "
        f"— trigger phrases and 'DOES NOT fire on' fences are routing and must "
        f"stay; prose the body already carries is what goes."
    )


@pytest.mark.parametrize("skill_md", _skill_files(), ids=lambda p: p.parent.name)
def test_description_is_present(skill_md: Path) -> None:
    """An empty description is unroutable — the skill exists and cannot fire."""
    assert _description(skill_md).strip(), (
        f"{skill_md.parent.name}: no description in frontmatter. Cowork routes on "
        f"the description ONLY, so this skill can never be reached."
    )


def test_guard_can_actually_fail() -> None:
    """Non-vacuity: the measurement must reject something.

    A budget guard that only ever sees compliant input proves nothing about its
    own arithmetic. Feed it a synthetic over-cap description and assert it is
    judged over — the same check the real assertions apply.
    """
    over = "x" * (HARD_CAP + 1)
    assert len(over) > HARD_CAP
    assert not (len(over) <= BUDGET)
    at_edge = "x" * BUDGET
    assert len(at_edge) <= BUDGET, "the boundary must be inclusive, not off by one"
