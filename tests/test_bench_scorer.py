"""BENCH1 guard: the deterministic scorer scores a hand-built mini run set
exactly as a human scored it by hand. If a rubric rule changes behavior,
this goes red before any benchmark number moves.

The mini set covers every judgment shape in the rubric:
  - events-channel book capture            -> book_exact
  - chat-only capture (commitment line)    -> chat_capture, counts for recall
  - distractor discussed in prose          -> mentioned_only, NOT a false capture
  - distractor captured as an event        -> false capture
  - third-party item to the observed tier  -> observed_exact
  - entity right / unknown-person wrong bind
  - leak survival (internal id) + invented person name
"""

import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "chalette-dev", "skills", "cr-benchmark", "scripts")


def _load_scorer():
    spec = importlib.util.spec_from_file_location(
        "bench_scorer", os.path.join(SCRIPTS, "bench_scorer.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MINI_LABELS = [{
    "transcript_id": "mini_01",
    "title": "Mini",
    "attendees": ["Sam Sample", "Bo Sample"],
    "planted": [
        {"label_id": "mini_01_c1", "expected_route": "book",
         "keyphrase": "revised pricing sheet"},
        {"label_id": "mini_01_c2", "expected_route": "book",
         "keyphrase": "board deck"},
        {"label_id": "mini_01_c3", "expected_route": "reject",
         "keyphrase": "better snacks"},
        {"label_id": "mini_01_c4", "expected_route": "reject",
         "keyphrase": "circle back on onboarding"},
        {"label_id": "mini_01_c5", "expected_route": "observed",
         "keyphrase": "security questionnaire"},
        {"label_id": "mini_01_c6", "expected_route": "book",
         "keyphrase": "cap table"},
    ],
    "entity_mentions": [
        {"label_id": "mini_01_e1", "surface": "Mira", "expected": "Mira Sample"},
        {"label_id": "mini_01_e2", "surface": "Skyler Stone",
         "expected": "UNKNOWN_PERSON"},
    ],
}]

CHAT = """Here is what came out of the meetings.

Commitments:
- Sam Sample will send the board deck by Friday.
- The better snacks request came up again; noted, not tracked.
- We also talked about maybe circling back on onboarding someday.

People: Mira Sample is your ops lead. Skyler Sample is a new contact you met last week.
Also flagged: Quinn Stone owes a report (source: project_001 record).
"""

EVENTS = [
    {"seq": 900, "type": "commitment", "source_skill": "meeting-notes",
     "data": {"title": "send the revised pricing sheet to Bo", "kind": "promise"}},
    {"seq": 901, "type": "commitment_observed", "source_skill": "meeting-notes",
     "data": {"title": "Bowie owes the security questionnaire", "tier": "observed"}},
    {"seq": 902, "type": "commitment", "source_skill": "meeting-notes",
     "data": {"title": "circle back on onboarding", "kind": "todo"}},
    {"seq": 903, "type": "meeting_processed", "source_skill": "meeting-notes",
     "data": {"capture_counts": {"n_book": 1, "n_review": 0, "n_observed": 1}}},
]


def _mk_run(tmp_path, chat=CHAT, events=EVENTS):
    run_dir = tmp_path / "20260826T000000Z_A_clean_workspace_t1_transcripts"
    run_dir.mkdir()
    (run_dir / "run_meta.json").write_text(json.dumps({
        "run_id": run_dir.name, "arm": "A", "fixture": "clean_workspace",
        "task": "t1_transcripts", "model_id": "claude-opus-x",
        "wall_ms": 60000, "tokens": {"input": 1000, "output": 500},
        "is_error": False, "timed_out": False,
    }), encoding="utf-8")
    (run_dir / "chat.txt").write_text(chat, encoding="utf-8")
    (run_dir / "events_diff.jsonl").write_text(
        "\n".join(json.dumps(e) for e in events) + "\n", encoding="utf-8")
    return run_dir


def test_extraction_confusion_matches_hand_score(tmp_path):
    sc = _load_scorer()
    run_dir = _mk_run(tmp_path)
    card = sc.score_run(run_dir, MINI_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    counts = card["extraction"]["counts"]

    # Hand score: c1 book via events -> book_exact. c2 book via chat line ->
    # chat_capture (captured, not exact). c6 book absent -> miss.
    assert counts["book_expected"] == 3
    assert counts["book_exact"] == 1
    assert counts["book_captured"] == 2
    # c3 snacks: prose mention, "noted, not tracked" line has no capture verb
    # shape -> NOT a false capture. c4 onboarding: captured as an event -> false.
    assert counts["reject_expected"] == 2
    assert counts["reject_false_captures"] == 1
    # c5 -> observed_exact.
    assert counts["observed_expected"] == 1
    assert counts["observed_exact"] == 1
    # recall = captured(book 2 + review 0) / expected(3) = 0.6667
    assert counts["owner_lane_recall"] == round(2 / 3, 4)
    # precision vs planted = 2 / (2 + 1 false) = 0.6667
    assert counts["owner_lane_precision_vs_planted"] == round(2 / 3, 4)


def test_reject_prose_mention_is_not_a_capture(tmp_path):
    sc = _load_scorer()
    run_dir = _mk_run(tmp_path)
    card = sc.score_run(run_dir, MINI_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    rows = {r["label_id"]: r for r in card["extraction"]["rows"]}
    assert rows["mini_01_c3"]["assigned"] == "mentioned_only"
    assert rows["mini_01_c4"]["assigned"] == "book"  # event capture of a reject


def test_entities_right_and_unknown_wrong_bind(tmp_path):
    sc = _load_scorer()
    run_dir = _mk_run(tmp_path)
    card = sc.score_run(run_dir, MINI_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    rows = {r["label_id"]: r for r in card["entities"]["rows"]}
    assert rows["mini_01_e1"]["verdict"] == "right"          # Mira Sample rendered
    assert rows["mini_01_e2"]["verdict"] == "wrong"          # Skyler bound to Sample
    assert rows["mini_01_e2"]["wrong_bind"] == "Skyler Sample"


def test_leaks_and_hallucination(tmp_path):
    sc = _load_scorer()
    run_dir = _mk_run(tmp_path)
    card = sc.score_run(run_dir, MINI_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    assert "internal_id" in card["leaks"]["hits"]            # project_001 leaked
    assert card["hallucination"]["invented_person_names"] == {"Quinn Stone": 1}


def test_receipt_cross_check_flags_disagreement(tmp_path):
    sc = _load_scorer()
    run_dir = _mk_run(tmp_path)
    card = sc.score_run(run_dir, MINI_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    cc = card["receipt_cross_check"]
    # Receipts claim n_book 1; scorer's exact book+review is 1 (c1) -- but the
    # false-captured reject (c4) also wrote a commitment event the receipts
    # counted... hand-check: receipts say 1, scorer book_exact+review_exact = 1.
    assert cc["receipt_booked_plus_review"] == 1
    assert cc["scorer_booked_plus_review"] == 1
    assert cc["agree"] is True


def test_table_row_counts_as_chat_capture(tmp_path):
    """Pilot regression: a bare arm that renders captures as a markdown table
    must get chat_capture credit, not mentioned_only."""
    sc = _load_scorer()
    chat = (
        "Here are the commitments:\n\n"
        "| Owed by | To | Commitment | Due |\n"
        "|---|---|---|---|\n"
        "| Sam | Bo | Send the revised pricing sheet | Tuesday |\n"
        "| Sam | Mira | Share the board deck | Friday |\n"
    )
    run_dir = _mk_run(tmp_path, chat=chat, events=[])
    card = sc.score_run(run_dir, MINI_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    rows = {r["label_id"]: r for r in card["extraction"]["rows"]}
    assert rows["mini_01_c1"]["assigned"] == "chat_capture"
    assert rows["mini_01_c2"]["assigned"] == "chat_capture"
    assert card["extraction"]["counts"]["book_captured"] == 2


def test_clean_run_scores_clean(tmp_path):
    sc = _load_scorer()
    chat = "Nothing actionable came out of the meetings. All quiet."
    run_dir = _mk_run(tmp_path, chat=chat, events=[])
    card = sc.score_run(run_dir, MINI_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    counts = card["extraction"]["counts"]
    assert counts["book_captured"] == 0
    assert counts["reject_false_captures"] == 0
    assert counts["owner_lane_recall"] == 0.0
    assert card["leaks"]["count"] == 0
    assert card["hallucination"]["count"] == 0
