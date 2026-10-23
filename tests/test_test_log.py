"""Every cr1-test script ends with the test-log prompt, and a right answer by a workaround is never a pass (v0.7.2)."""
import pathlib

SKILL = pathlib.Path(__file__).resolve().parent.parent / "chalette-dev" / "skills" / "cr1-test" / "SKILL.md"
PROMPT = ("For a test log, list exactly what you just did, in order: each skill you loaded, each script or command you ran "
          "(name and whether it ran in this chat or on my computer), each connector you called, every file you read or "
          "wrote or filed as a proposal (path only), any error or warning word for word, and whether anything was saved, "
          "queued for Maintenance, or not saved. Facts only, no summary of the findings, no client names.")


def _text():
    return SKILL.read_text(encoding="utf-8")


def test_the_log_prompt_ships_verbatim_in_a_code_block():
    assert f"```\n{PROMPT}\n```" in _text()


def test_the_script_template_asks_for_the_log_after_every_run():
    text = _text()
    template = text[text.index("## 3. Give Matthew the script"):text.index("Rules for a good script")]
    assert "After every run: the test log" in template
    assert "Every script ends with the test-log prompt, verbatim" in text


def test_a_workaround_answer_is_partial_and_a_missing_log_is_named():
    text = _text()
    assert "is **partial**, never a pass" in text
    assert '"no test log"' in text
