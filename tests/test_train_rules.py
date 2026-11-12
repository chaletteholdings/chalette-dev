"""The 2026-11-11 build rules live in docs/trains and the skills follow them (v0.9.8).

Owner ruling 2026-11-11 (cr1#1041 merge gates, cr1#1051 three-computer rules): the Mac checks,
the PCs build, one coordinator merges, the full battery runs every 5 merges, and a red main
between those runs no longer stops everything (revert-first retired). This file pins that the
playbook carries the gates and that no skill still states the retired per-batch / revert rule.
"""
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
TRAINS = ROOT / "docs" / "trains"
SKILLS = ROOT / "chalette-dev" / "skills"


def _read(path):
    return path.read_text(encoding="utf-8")


def test_playbook_carries_the_gates():
    text = _read(TRAINS / "THREE_COMPUTER_PLAYBOOK.md")
    for needle in ("cr1#1041", "cr1#1051", "every 5 merges", "Revert-first is retired",
                   "One review round", "--force", "re-run once"):
        assert needle in text, needle


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
    assert "every 5 merges" in _read(SKILLS / "battery" / "SKILL.md")
    assert "cr1#1041" in _read(SKILLS / "cr1-desk" / "SKILL.md")


def test_merge_script_lets_unrelated_prs_past_a_red_main():
    assert "MAIN_RED_OK" in _read(TRAINS / "merge_pr.sh")
