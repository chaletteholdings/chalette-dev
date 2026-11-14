"""The 2026-11-11 build rules live in docs/trains and the skills follow them (v0.9.8).

Owner ruling 2026-11-11 (cr1#1041 merge gates, cr1#1051 three-computer rules): the Mac checks,
the PCs build, one coordinator merges, the full battery runs every 5 merges (every 10 since
2026-11-12), and a red main between those runs no longer stops everything. Since cr1#1258 the
gates live once, in cr1 ISSUES.md section 10: this file pins that the playbook and the battery
skill point there, and that no skill still states the retired per-batch / revert rule.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRAINS = ROOT / "docs" / "trains"
SKILLS = ROOT / "chalette-dev" / "skills"


def _read(path):
    return path.read_text(encoding="utf-8")


def test_playbook_points_at_the_one_home():
    # cr1#1258 (owner ruling 2026-11-14): the gates live once, in cr1 ISSUES.md section 10;
    # the playbook points there instead of restating them, and states the current cadence.
    text = _read(TRAINS / "THREE_COMPUTER_PLAYBOOK.md")
    for needle in ("cr1#1041", "cr1#1051", "cr1#1258", "ISSUES.md` section 10", "every 10 merges"):
        assert needle in text, needle
    gates = text[text.index("## The merge gates"):text.index("## Who does what")]
    assert "1. **CI runs on the Mac.**" not in gates, "the gates are restated again"
    assert "every-5" not in text


def test_prompts_point_at_the_repo_copy():
    text = _read(TRAINS / "CHAT_PROMPTS.md")
    assert "docs/trains/THREE_COMPUTER_PLAYBOOK.md" in text
    assert "Sofia Brain" not in text


def test_old_playbook_is_bannered():
    assert "Superseded 2026-11-11" in _read(TRAINS / "TWO_MACHINE_PLAYBOOK.md")


def test_skills_drop_the_retired_rule():
    for name in ("battery", "cr1-desk"):
        text = _read(SKILLS / name / "SKILL.md")
        assert "fixed or reverted" not in text, name
        assert "per batch" not in text, name
    # cr1#1258 (owner ruling 2026-11-14): the battery skill states the current cadence
    # (every 10 merges since the 2026-11-12 ruling) and points at the rules' one home.
    battery = _read(SKILLS / "battery" / "SKILL.md")
    assert "every 10 merges" in battery and "every 5 merges" not in battery
    assert "ISSUES.md` section 10" in battery
    assert "cr1#1041" in _read(SKILLS / "cr1-desk" / "SKILL.md")


def test_merge_script_lets_unrelated_prs_past_a_red_main():
    assert "MAIN_RED_OK" in _read(TRAINS / "merge_pr.sh")
