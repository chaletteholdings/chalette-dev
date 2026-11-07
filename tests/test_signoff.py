"""A team member's pass never closes; only Matthew's sign-off does (v0.9.3, cr1#448)."""
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SKILLS = ROOT / "chalette-dev" / "skills"


def _test_skill():
    return (SKILLS / "cr1-test" / "SKILL.md").read_text(encoding="utf-8")


def test_a_team_members_pass_ends_at_ready_to_close():
    text = _test_skill()
    team = text[text.index("**A team member's pass:**"):text.index("### Fail or partial")]
    assert "never close" in team
    assert "state=closed" not in team
    assert "add `ready to close`" in team and "remove `needs UAT`" in team
    assert "@chaletteholdings" in team


def test_only_matthews_word_closes_in_the_sign_off():
    text = _test_skill()
    sign_off = text[text.index("## 6. Matthew's sign-off"):text.index("## 7. Backlog review")]  # v0.9.7: section 7 has its own close
    assert "Matthew only, and here a person's word is not enough." in sign_off
    gate, rest = sign_off.split("**The queue**", 1)
    assert "gh api user --jq .login" in gate and "`chaletteholdings`" in gate
    assert "**Close only on Matthew's word in this chat:**" in rest
    assert sign_off.count("state=closed") == 1
    for check in ("Right build", "Three runs", "A log for every run", "Evidence for every pass criterion",
                  "Neighbours checked", "Clean"):
        assert f"**{check}" in sign_off, check


def test_a_team_member_claims_and_releases_the_issue():
    text = _test_skill()
    prepare = text[text.index("## 2. Prepare one test"):text.index("## 3. Give Matthew the script")]
    assert "/assignees" in prepare and "-X DELETE" in prepare


def test_sign_off_phrases_are_trigger_cases():
    cases = json.loads((SKILLS / "cr1-test" / "evals" / "triggers.json").read_text(encoding="utf-8"))
    for phrase in ("what needs my sign-off", "check the pass on #57", "close all that hold"):
        assert phrase in cases["should_trigger"]
