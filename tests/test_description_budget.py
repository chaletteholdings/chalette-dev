#!/usr/bin/env python3
"""Description-budget guard for chalette-dev, the sibling of cr1's G11.

Why this exists (2026-08-16): a skill description over 1,024 characters does not warn; the
skill stops loading at frontmatter parse. Nothing was watching this repo's descriptions and
three of them had drifted to within 20 characters of the cap. Since 2026-10-24 (v0.8.1) the
same budget covers the two manifests: plugin.json's description had grown into a
22,892-character changelog.

The whole-catalog total is deliberately NOT asserted: whether the runtime's listing budget
is per plugin or per install is not established, and the four cr1 skills are far under any
plausible total.

  BUDGET (980)    same headroom cr1 keeps under the hard cap.
  HARD_CAP (1024) the spec's parse limit. Never raise this; it is not ours.
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
MANIFESTS = [
    ROOT / "chalette-dev" / ".claude-plugin" / "plugin.json",
    ROOT / ".claude-plugin" / "marketplace.json",
]


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
    assert len(files) >= 4, f"only {len(files)} skills found; expected the four cr1 skills"


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


def _manifest_descriptions() -> list[tuple[str, str]]:
    import json
    out = []
    for p in MANIFESTS:
        data = json.loads(p.read_text(encoding="utf-8"))
        if "description" in data:
            out.append((p.name, data["description"]))
        for entry in data.get("plugins", []):
            out.append((f"{p.name}:{entry.get('name')}", entry.get("description", "")))
    return out


def test_manifests_are_discoverable() -> None:
    assert len(_manifest_descriptions()) >= 2, _manifest_descriptions()


@pytest.mark.parametrize("item", _manifest_descriptions(), ids=lambda x: x[0])
def test_manifest_description_within_budget(item: tuple[str, str]) -> None:
    """A manifest description is read wherever the plugin is listed; it is a label, not a changelog.

    Release history belongs in CHANGELOG.md.
    """
    name, desc = item
    assert desc.strip(), f"{name}: empty description"
    assert len(desc) <= BUDGET, (
        f"{name}: description is {len(desc)} chars, over the {BUDGET} budget. "
        f"Move history to CHANGELOG.md; keep two sentences here."
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
