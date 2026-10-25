"""The four skills target Command Room 1 (chaletteholdings/cr1) and carry nothing CR2-only (v0.8.0).

CR2 was retired on 2026-10-22. Each skill may name ChaletteHQ/cr2 in exactly one line: the
fallback for when the owner explicitly says a problem is on CR2. Nothing else from CR2 survives:
no CR2 developer, no core/labs routes, no CR2 folders or tools."""
import pathlib
import re

import pytest

SKILLS = pathlib.Path(__file__).resolve().parent.parent / "chalette-dev" / "skills"
NAMES = ["cr1-report", "cr1-scrub", "cr1-test", "cr1-desk"]
GONE = ["Louis", "Lewis", "GiggleSamurai", "cr2-labs", "02_product", "03_tests", "00_docs", "06_labs",
        "04_tools", "refresh_preview", "cr2-preview", "intake drop", "_hq/_system/runs", "CR2_RUNTIME"]


def _text(name):
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def test_the_four_skills_exist_under_cr1_names():
    assert sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md")) == sorted(NAMES)


@pytest.mark.parametrize("name", NAMES)
def test_frontmatter_name_matches_folder(name):
    assert re.search(rf'^name: "?{name}"?$', _text(name), re.M)


@pytest.mark.parametrize("name", NAMES)
def test_cr2_appears_only_in_the_one_fallback_line(name):
    lines = [ln for ln in _text(name).splitlines() if "ChaletteHQ/cr2" in ln or "repos/ChaletteHQ/cr2" in ln]
    assert len(lines) == 1, f"{name}: ChaletteHQ/cr2 on {len(lines)} lines, expected only the fallback line"
    assert "explicitly says" in lines[0]


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
