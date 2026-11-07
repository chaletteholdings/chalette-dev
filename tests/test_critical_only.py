"""The critical-only rule is a mechanism at report time, not a sentence in ISSUES.md (v0.9.7).

Owner ruling 2026-11-06 (cr1 ISSUES.md sections 7 and 12, cr1 PR #855): the tracker keeps
only critical tickets, and a merged fix is tested by use. A ticket is critical only if it
can (1) write the wrong thing to a book or lose data, (2) send or draft without the owner's
word or to the wrong person, (3) expose client or personal information, or (4) stop the Hub
or Maintenance. This file pins that the skills carry the rule as steps, so a ruling without a
published mechanism cannot drift back into prose.
"""
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "chalette-dev" / "skills"

FOUR_TESTS = ("Wrong write or data loss", "Send without the owner's word", "information exposed",
              "Hub or Maintenance stops")
THE_QUESTION = "This does not meet the four tests. File it anyway, or drop it?"


def _skill(name):
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


def _triggers(name):
    return json.loads((SKILLS / name / "evals" / "triggers.json").read_text(encoding="utf-8"))


# ---- cr1-report: judge at filing, label critical with its reason, ask only outside the rule ----

def test_report_judges_every_report_against_the_four_tests():
    text = _skill("cr1-report")
    judge = text[text.index("## 1a. Critical or backlog"):text.index("## 2. Gather")]
    for name in FOUR_TESTS:
        assert name in judge, name
    assert "label `critical`" in judge
    assert "**Critical:** can close the wrong commitment" in judge
    assert "Ask nothing" in judge


def test_report_asks_one_question_only_outside_the_rule():
    text = _skill("cr1-report")
    judge = text[text.index("## 1a. Critical or backlog"):text.index("## 2. Gather")]
    assert THE_QUESTION in judge
    assert "label `backlog`" in judge and "no milestone" in judge
    assert "Never both labels" in judge


def test_report_files_the_labels_it_decided():
    text = _skill("cr1-report")
    file_step = text[text.index("## 6. Confirm, then file"):text.index("## 7. Reply")]
    assert "`critical`" in file_step and "`backlog`" in file_step
    assert "-f \"labels[]=critical\"" in file_step


# ---- cr1-test: a person's test is owed only on a critical fix; backlog review closes the rest ----

def test_what_needs_me_lists_only_critical_fixes():
    text = _skill("cr1-test")
    queue = text[text.index("## 1. \"What needs me\""):text.index("## 2. Prepare one test")]
    assert "labels=critical,needs%20UAT" in queue
    assert "without `critical`" in queue


def test_backlog_review_lists_old_backlog_tickets_to_close():
    text = _skill("cr1-test")
    review = text[text.index("## 7. Backlog review"):]
    assert "labels=backlog" in review
    assert "30 days" in review
    assert "state_reason=not_planned" in review
    assert "never close" in review  # a team member lists and tags, Matthew closes


def test_backlog_review_is_a_trigger_case():
    cases = _triggers("cr1-test")
    assert "backlog review" in cases["should_trigger"]
    assert "backlog review" not in cases["should_not_trigger"]
    frontmatter = _skill("cr1-test").split("\n---\n", 1)[0]
    assert "'backlog review'" in frontmatter  # the description routes on it


# ---- the train merge script reads the label too, never guesses ----

def test_merge_script_sets_needs_uat_only_on_critical():
    script = (ROOT / "docs" / "trains" / "merge_pr.sh").read_text(encoding="utf-8")
    assert "grep -qx critical" in script
    assert "state_reason=completed" in script
    # the label line sits inside the critical branch, after the merge
    gate = script.index("if gh api repos/$R/issues/$I/labels")
    assert script.index("merge_method") < gate < script.index("labels[]=needs UAT") < script.index("\nelse\n")


def test_pins_can_fail():
    """Non-vacuity: the same checks reject a skill that carries the rule as prose only."""
    prose = "The tracker keeps only critical tickets. Everything else closes."
    assert THE_QUESTION not in prose and "label `critical`" not in prose
