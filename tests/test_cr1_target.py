"""The four skills target Command Room 1 (chaletteholdings/cr1) and carry nothing CR2-only.

CR2 was retired on 2026-10-22. As of v0.8.2 no skill names the CR2 repository at all (the
explicit-fallback line of v0.8.0 is gone). Nothing else from CR2 survives: no CR2 developer,
no core/labs routes, no CR2 folders or tools."""
import pathlib
import re

import pytest

SKILLS = pathlib.Path(__file__).resolve().parent.parent / "chalette-dev" / "skills"
NAMES = ["cr1-report", "cr1-scrub", "cr1-test", "cr1-desk"]
GONE = ["Louis", "Lewis", "GiggleSamurai", "cr2-labs", "02_product", "03_tests", "00_docs", "06_labs",
        "04_tools", "refresh_preview", "cr2-preview", "intake drop", "_hq/_system/runs", "CR2_RUNTIME"]


def _text(name):
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


# The team toolkit that moved in from the owner's plugin on 2026-10-25 (v0.9.0).
TOOLKIT = ["battery", "bug-regression-suite", "synthetic-workspace-runtime-test",
           "cross-skill-interaction-test", "scale-stress-test", "ship-readiness-gate",
           "cr-skill-builder", "skill-creator", "skill-generator", "regenerate-skill",
           "preview-command-room-widget"]


def test_the_four_skills_exist_under_cr1_names():
    assert sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md")) == sorted(NAMES + TOOLKIT)


def test_no_skill_answers_to_the_old_cr_test_name():
    """`cr-test` became `battery` so it cannot collide with `cr1-test` (owner ruling 2026-10-25)."""
    hits = [f"{p.parent.name}:{n}" for p in SKILLS.glob("*/SKILL.md")
            for n, ln in enumerate(p.read_text(encoding="utf-8").splitlines(), 1)
            if re.search(r"\bcr-test\b|\bcr test\b", ln)]
    assert not hits, hits


def test_toolkit_skills_name_the_moved_repo():
    hits = [str(f) for s in TOOLKIT for f in (SKILLS / s).rglob("*")
            if f.is_file() and f.suffix in {".md", ".py", ".json"} and "ChaletteHQ/cr1" in f.read_text(encoding="utf-8")]
    assert not hits, hits


def test_toolkit_skills_carry_the_team_fence():
    missing = [s for s in TOOLKIT if "Team toolkit (chalette-dev)" not in (SKILLS / s / "SKILL.md").read_text(encoding="utf-8")]
    assert not missing, missing


@pytest.mark.parametrize("name", NAMES)
def test_frontmatter_name_matches_folder(name):
    assert re.search(rf'^name: "?{name}"?$', _text(name), re.M)


@pytest.mark.parametrize("name", NAMES)
def test_no_cr2_repository_reference_remains(name):
    hits = [ln for ln in _text(name).splitlines() if re.search(r"ChaletteHQ/cr2|\bcr2\b", ln, re.I)]
    assert not hits, f"{name}: CR2 still named: {hits}"


@pytest.mark.parametrize("name", NAMES)
def test_no_cr2_only_mechanics_remain(name):
    text = _text(name)
    found = [g for g in GONE if g in text]
    assert not found, f"{name}: CR2-only text still present: {found}"
    assert not re.search(r"`core`|`labs`|\bcore or labs\b|route label", text), f"{name}: a route remains"


@pytest.mark.parametrize("name", NAMES)
def test_house_style(name):
    text = _text(name)
    assert "—" not in text, f"{name}: em dash"
    body = text.split("---", 2)[2]
    assert "!" not in re.sub(r"`[^`]*`|```.*?```", "", body, flags=re.S), f"{name}: exclamation mark"
