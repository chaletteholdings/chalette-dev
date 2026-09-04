"""BENCH-METHEM guards (ATTRIB1 D10): the speaker variants of the benchmark
transcript set and the counterparty-resolved metric.

  - the generator renders me_them as the real Granola shape: Me:/Them: only,
    one line, every non-user voice collapsed, consecutive same-voice turns
    merged; unlabelled carries no marker at all
  - every planted keyphrase survives every variant, in its own transcript
    only (the one frozen label set scores all three renderings)
  - the committed variant fixtures match the generator byte-for-byte (LF)
  - the named set is untouched by the variant machinery
  - the scorer's counterparty verdicts match a hand score on both channels
"""

import importlib.util
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.join(HERE, "..", "chalette-dev", "skills", "cr-benchmark")
SCRIPTS = os.path.join(SKILL, "scripts")
FIXTURES = os.path.join(SKILL, "fixtures", "bench_transcripts")


def _load(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(SCRIPTS, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _gen():
    return _load("_generate_bench_transcripts")


def _roster(gen):
    return gen.load_roster(gen.DEFAULT_FIXTURES)


# ----------------------------------------------------------------- generator

def test_generator_check_passes_for_every_variant():
    env = dict(os.environ, PYTHONUTF8="1")
    r = subprocess.run([sys.executable, os.path.join(SCRIPTS, "_generate_bench_transcripts.py"),
                        "--check"], capture_output=True, text=True, env=env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert "speakers    : ['named', 'me_them', 'unlabelled']" in r.stdout


def test_me_them_is_the_real_granola_shape():
    gen = _gen()
    roster = _roster(gen)
    marker = re.compile(r"(?:(?<=\s)|^)(Me|Them): ")
    for t in gen.TRANSCRIPTS:
        txt = gen.render_transcript(t, roster, "me_them")
        assert txt.count("\n") == 1 and txt.endswith("\n"), t["id"]      # one line
        labels = [m.group(1) for m in marker.finditer(txt)]
        assert "Me" in labels and "Them" in labels, t["id"]
        # consecutive same-voice turns merge: no two identical markers adjoin
        assert all(a != b for a, b in zip(labels, labels[1:])), (t["id"], labels)
        # no named speaker label survives the collapse
        assert "Sample:" not in txt and "Stone:" not in txt, t["id"]
        # the user's turns are exactly the Me: turns, everyone else is Them:
        expected_first = "Me" if t["turns"][0][0] == "Sam" else "Them"
        assert labels[0] == expected_first, t["id"]


def test_three_party_calls_collapse_every_other_voice():
    gen = _gen()
    roster = _roster(gen)
    three = [t for t in gen.TRANSCRIPTS if len(t["attendees"]) >= 3]
    assert three, "the set needs at least one 3+-party call"
    for t in three:
        txt = gen.render_transcript(t, roster, "me_them")
        others = {spk for spk, _ in t["turns"] if spk != "Sam"}
        assert len(others) >= 2, t["id"]
        for first in others:
            assert not re.search(rf"(?:(?<=\s)|^){first} Sample: ", txt), (t["id"], first)


def test_unlabelled_has_no_markers_and_named_is_unchanged():
    gen = _gen()
    roster = _roster(gen)
    label = re.compile(r"(?:(?<=\s)|^)[A-Z][a-z]+(?: [A-Z][a-z]+)?: ")
    for t in gen.TRANSCRIPTS:
        un = gen.render_transcript(t, roster, "unlabelled")
        assert not label.search(un), t["id"]
        assert un.count("\n") == len(t["turns"])
        named = gen.render_transcript(t, roster)               # default = named
        assert named == gen.render_transcript(t, roster, "named")
        assert named.count("\n") == len(t["turns"])
        assert all(ln.split(": ")[0].endswith(" Sample") for ln in named.splitlines())


def test_keyphrases_survive_every_variant_in_their_own_transcript():
    gen = _gen()
    roster = _roster(gen)
    for v in gen.SPEAKER_VARIANTS:
        rendered = {t["id"]: gen.render_transcript(t, roster, v).lower() for t in gen.TRANSCRIPTS}
        for t in gen.TRANSCRIPTS:
            for item in t["planted"]:
                kp = item["keyphrase"].lower()
                hits = [tid for tid, txt in rendered.items() if kp in txt]
                assert hits == [t["id"]], (v, item["keyphrase"], hits)


def test_variant_validator_rejects_a_leaked_name_label():
    gen = _gen()
    roster = _roster(gen)
    rendered = {t["id"]: gen.render_transcript(t, roster, "me_them") for t in gen.TRANSCRIPTS}
    labels = {t["id"]: gen.build_labels(t, roster, rendered[t["id"]]) for t in gen.TRANSCRIPTS}
    assert gen.validate(roster, rendered, labels, speakers="me_them") == []
    # a named label sneaking into a collapsed transcript must fail validation
    leaked = dict(rendered)
    leaked["bench_01"] = leaked["bench_01"].replace("Them: they asked", "Bo Sample: they asked", 1)
    errs = gen.validate(roster, leaked, labels, speakers="me_them")
    assert any("non-Me/Them speaker marker" in e and "bench_01" in e for e in errs), errs


def test_committed_variant_fixtures_match_the_generator_lf():
    gen = _gen()
    roster = _roster(gen)
    for v in ("me_them", "unlabelled"):
        vdir = os.path.join(FIXTURES, v)
        manifest = json.load(open(os.path.join(vdir, "manifest.json"), encoding="utf-8"))
        assert manifest["speakers"] == v
        assert manifest["variants_version"] == gen.VARIANTS_VERSION
        assert manifest["transcript_count"] == len(gen.TRANSCRIPTS)
        assert not os.path.exists(os.path.join(vdir, "labels")), "variants share the one label set"
        for t in gen.TRANSCRIPTS:
            raw = open(os.path.join(vdir, f"{t['id']}.txt"), "rb").read()
            assert b"\r" not in raw, (v, t["id"], "CRLF")
            assert raw.decode("utf-8") == gen.render_transcript(t, roster, v), (v, t["id"], "drift")
    # the base manifest carries no variant key: the named set is the base set
    base = json.load(open(os.path.join(FIXTURES, "manifest.json"), encoding="utf-8"))
    assert "speakers" not in base and "variants_version" not in base


# -------------------------------------------------------------------- scorer

CP_LABELS = [{
    "transcript_id": "mini_2p", "title": "Two-party", "attendees": ["Sam Sample", "Bo Sample"],
    "planted": [
        {"label_id": "mini_2p_c1", "expected_route": "book", "keyphrase": "revised pricing sheet",
         "owner_name": "Sam Sample", "counterparty_name": "Bo Sample"},
        {"label_id": "mini_2p_c2", "expected_route": "book", "keyphrase": "acme usage report",
         "owner_name": "Bo Sample", "counterparty_name": "Sam Sample"},
        {"label_id": "mini_2p_c3", "expected_route": "review", "keyphrase": "customer case study",
         "owner_name": "Sam Sample", "counterparty_name": "Bo Sample"},
        {"label_id": "mini_2p_c4", "expected_route": "book", "keyphrase": "cap table",
         "owner_name": "Sam Sample", "counterparty_name": "Bo Sample"},
        {"label_id": "mini_2p_c5", "expected_route": "book", "keyphrase": "wire instructions",
         "owner_name": "Sam Sample", "counterparty_name": "Bo Sample"},
        {"label_id": "mini_2p_c6", "expected_route": "observed", "keyphrase": "equity grants file",
         "owner_name": "Quinn Sample", "counterparty_name": None},
        {"label_id": "mini_2p_c7", "expected_route": "reject", "keyphrase": "better snacks"},
    ],
    "entity_mentions": [],
}, {
    "transcript_id": "mini_3p", "title": "Three-party",
    "attendees": ["Sam Sample", "Quinn Sample", "Aria Sample"],
    "planted": [
        {"label_id": "mini_3p_c1", "expected_route": "book", "keyphrase": "offer template",
         "owner_name": "Sam Sample", "counterparty_name": "Quinn Sample"},
        {"label_id": "mini_3p_c2", "expected_route": "book", "keyphrase": "panel interviews",
         "owner_name": "Quinn Sample", "counterparty_name": "Sam Sample"},
    ],
    "entity_mentions": [],
}]

CP_EVENTS = [
    # c1: right counterparty by id (person_002 = Bo Sample in clean_workspace)
    {"seq": 1, "type": "commitment", "data": {"title": "send Bo the revised pricing sheet",
     "owner_id": "person_009", "counterparty_id": "person_002",
     "attribution": {"counterparty_basis": "calendar"}}},
    # c3: no id, nobody named -> unresolved, with the basis recorded
    {"seq": 2, "type": "commitment", "data": {"title": "draft the customer case study",
     "owner_id": "person_009", "counterparty_id": None, "pending_review": True,
     "attribution": {"counterparty_basis": "unknown"}}},
    # c4: wrong person by id (person_006 = Mira Sample)
    {"seq": 3, "type": "commitment", "data": {"title": "send the updated cap table",
     "owner_id": "person_009", "counterparty_id": "person_006"}},
    # c5: a hand-written row with a non-roster string -> unresolved, not wrong
    {"seq": 4, "type": "commitment", "data": {"title": "send the wire instructions",
     "counterparty": "counsel"}},
    # 3p c1: a string field naming the right person beside another -> correct
    {"seq": 5, "type": "commitment", "data": {"title": "send the offer template",
     "counterparty": "Quinn Sample / Aria Sample"}},
]

CP_CHAT = """Commitments from the calls:

| Owner | Commitment | To | Due |
|---|---|---|---|
| Bo | Send you the Acme usage report | Sam | Friday |
| Quinn | Schedule the panel interviews for both candidates | Aria | this week |

Also on the list: the equity grants file goes to the auditors (Quinn, Tuesday).
Better snacks came up again; noted, not tracked.
"""


def _mk_run(tmp_path, speakers="me_them"):
    sc = _load("bench_scorer")
    run_dir = tmp_path / "20260903T000000Z_A_clean_workspace_t1_transcripts_me_them"
    run_dir.mkdir()
    (run_dir / "run_meta.json").write_text(json.dumps({
        "run_id": run_dir.name, "arm": "A", "fixture": "clean_workspace",
        "task": "t1_transcripts", "speakers": speakers, "model_id": "claude-opus-x",
        "wall_ms": 1000, "tokens": {"input": 1, "output": 1},
        "is_error": False, "timed_out": False}), encoding="utf-8")
    (run_dir / "chat.txt").write_text(CP_CHAT, encoding="utf-8")
    (run_dir / "events_diff.jsonl").write_text(
        "\n".join(json.dumps(e) for e in CP_EVENTS) + "\n", encoding="utf-8")
    return sc, run_dir


def test_counterparty_verdicts_match_hand_score(tmp_path):
    sc, run_dir = _mk_run(tmp_path)
    card = sc.score_run(run_dir, CP_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    assert card["speakers"] == "me_them"
    rows = {r["label_id"]: r for r in card["counterparty"]["rows"]}
    # events channel
    assert rows["mini_2p_c1"]["verdict"] == "correct" and rows["mini_2p_c1"]["basis"] == "calendar"
    assert rows["mini_2p_c3"]["verdict"] == "unresolved" and rows["mini_2p_c3"]["basis"] == "unknown"
    assert rows["mini_2p_c4"]["verdict"] == "wrong" and rows["mini_2p_c4"]["asserted"] == "Mira Sample"
    assert rows["mini_2p_c5"]["verdict"] == "unresolved" and rows["mini_2p_c5"]["asserted"] == "counsel"
    assert rows["mini_3p_c1"]["verdict"] == "correct"
    # chat channel: table row names Sam (and "you") -> correct; the 3p row
    # names Aria where Sam was expected -> wrong
    assert rows["mini_2p_c2"]["channel"] == "chat" and rows["mini_2p_c2"]["verdict"] == "correct"
    assert rows["mini_3p_c2"]["verdict"] == "wrong" and rows["mini_3p_c2"]["asserted"] == "Aria"
    # observed / reject rows never enter the counterparty metric
    assert "mini_2p_c6" not in rows and "mini_2p_c7" not in rows
    counts = card["counterparty"]["counts"]
    assert counts["2p"] == {"expected": 5, "captured": 5, "correct": 2, "wrong": 1, "unresolved": 2,
                            "unknown_id": 0,
                            "rate_correct_of_captured": 0.4, "rate_wrong_of_captured": 0.2,
                            "rate_correct_of_expected": 0.4}
    assert counts["3p+"]["captured"] == 2 and counts["3p+"]["correct"] == 1 and counts["3p+"]["wrong"] == 1
    assert counts["all"]["expected"] == 7 and counts["all"]["correct"] == 3
    assert card["counterparty"]["counterparty_basis_counts"] == {"calendar": 1, "unknown": 1}


def test_uncaptured_items_sit_outside_the_denominator(tmp_path):
    sc, run_dir = _mk_run(tmp_path)
    (run_dir / "events_diff.jsonl").write_text("", encoding="utf-8")
    (run_dir / "chat.txt").write_text("Nothing actionable.", encoding="utf-8")
    card = sc.score_run(run_dir, CP_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    counts = card["counterparty"]["counts"]["all"]
    assert counts["expected"] == 7 and counts["captured"] == 0
    assert counts["rate_correct_of_captured"] is None
    assert counts["rate_correct_of_expected"] == 0.0
    assert all(r["verdict"] == "not_captured" for r in card["counterparty"]["rows"])


def test_second_person_counts_only_when_the_user_is_the_counterparty(tmp_path):
    sc, run_dir = _mk_run(tmp_path)
    (run_dir / "events_diff.jsonl").write_text("", encoding="utf-8")
    (run_dir / "chat.txt").write_text(
        "- Bo will send you the Acme usage report by Friday.\n"          # cp Sam: "you" -> correct
        "- You will send the revised pricing sheet by Tuesday.\n",        # cp Bo: "you" is the owner -> unresolved
        encoding="utf-8")
    card = sc.score_run(run_dir, CP_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    rows = {r["label_id"]: r for r in card["counterparty"]["rows"]}
    assert rows["mini_2p_c2"]["verdict"] == "correct" and rows["mini_2p_c2"]["asserted"] == "you"
    assert rows["mini_2p_c1"]["verdict"] == "unresolved"


def test_scoreboard_carries_the_speaker_variant_table(tmp_path):
    sc, run_dir = _mk_run(tmp_path)
    card = sc.score_run(run_dir, CP_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    md = sc.scoreboard_md([card])
    assert "## Speaker variants (t1) -- ATTRIB1 D10" in md
    assert "| me_them |" in md
    assert "2/5 (wrong 1, of 5)" in md          # the 2p cell, counts only
    assert "cp2p=2/5 (wrong 1, of 5)" in md     # per-run notes carry it too


def test_run_minted_counterparty_id_is_its_own_class(tmp_path):
    """Review F3: an id the fixture roster does not hold is `unknown_id`,
    visible on the row and in the counts -- never a silent `unresolved`."""
    sc, run_dir = _mk_run(tmp_path)
    events = [{"seq": 1, "type": "commitment", "data": {
        "title": "send Bo the revised pricing sheet", "owner_id": "person_009",
        "counterparty_id": "person_777", "counterparty": "Bo Sample"}}]
    (run_dir / "events_diff.jsonl").write_text(json.dumps(events[0]) + "\n", encoding="utf-8")
    (run_dir / "chat.txt").write_text("Logged.", encoding="utf-8")
    card = sc.score_run(run_dir, CP_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    row = {r["label_id"]: r for r in card["counterparty"]["rows"]}["mini_2p_c1"]
    assert row["verdict"] == "unknown_id" and row["asserted"] == "person_777"
    assert row["basis"] == "id_not_in_fixture_roster"
    c = card["counterparty"]["counts"]["2p"]
    assert c["unknown_id"] == 1 and c["unresolved"] == 0 and c["correct"] == 0
    assert "unknown_id 1" in sc.scoreboard_md([card])


def test_error_rows_carry_no_numbers_in_the_notes(tmp_path):
    """Review F4: a run that produced no output shows its status, not zeros."""
    sc, run_dir = _mk_run(tmp_path)
    meta = json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8"))
    meta["is_error"] = True
    (run_dir / "run_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (run_dir / "events_diff.jsonl").write_text("", encoding="utf-8")
    (run_dir / "chat.txt").write_text("Failed to authenticate", encoding="utf-8")
    md = sc.scoreboard_md([sc.score_run(run_dir, CP_LABELS, sc.EMBEDDED_LEAK_PATTERNS)])
    main_row = next(ln for ln in md.splitlines() if ln.startswith("| 2026") and "| A | me_them | t1" in ln)
    assert main_row.rstrip().endswith("| ERROR |"), main_row
    assert "recall=" not in main_row and "cp2p=" not in main_row and "ent=" not in main_row
    variant_row = next(ln for ln in md.splitlines() if ln.startswith("| 2026") and "| clean_workspace |" in ln)
    assert "| ERROR | ERROR |" in variant_row


def test_legacy_run_meta_without_speakers_scores_as_named(tmp_path):
    sc, run_dir = _mk_run(tmp_path)
    meta = json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8"))
    del meta["speakers"]
    (run_dir / "run_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    card = sc.score_run(run_dir, CP_LABELS, sc.EMBEDDED_LEAK_PATTERNS)
    assert card["speakers"] == "named"
