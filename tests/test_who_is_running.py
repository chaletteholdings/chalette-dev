"""The "Who is running this" section must say the same thing in every cr2 skill (v0.7.1)."""
import pathlib, re

SKILLS = pathlib.Path(__file__).resolve().parent.parent / "chalette-dev" / "skills"
NAMES = ["cr2-test", "cr2-report", "cr2-scrub", "cr2-desk"]


def _rule(name):
    text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"These skills are shared by Matthew and Erick.*?go on with the answer\.", text, re.S)
    assert m, f"{name}: 'Who is running this' rule not found"
    return m.group(0)


def test_who_is_running_is_identical_across_skills():
    rules = {n: _rule(n) for n in NAMES}
    assert len(set(rules.values())) == 1, "the 'Who is running this' rule differs between skills"


def test_who_is_running_checks_local_then_github_then_default():
    rule = _rule("cr2-test")
    order = [rule.index("operator.local.json"), rule.index("gh api user"), rule.index("config/operator.json")]
    assert order == sorted(order)
    assert "FATAL: operator profile unreadable" in rule
