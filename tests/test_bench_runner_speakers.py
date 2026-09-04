"""BENCH-METHEM runner guards (review F1 + F2). No real CLI: `subprocess.run`
is monkeypatched so every `fake-claude` invocation answers from a script
while git and everything else run for real. Pins:

  - `--speakers` injects the requested rendering into the granola connector
    doc (me_them / named / unlabelled), with the calendar attendees kept
  - an authentication failure on turn 1 stops the batch (exit 2), is on the
    RUNLOG row (`auth_blocked`, `error`), spends 0 tokens, skips the confirm
  - a non-auth error is recorded and the batch continues
  - a non-JSON reply with "not logged in" on stderr stops the batch too
  - an authentication failure on the `--resume` confirm turn is recorded
    (`follow_up_used: false`, `follow_up_error`) and stops the batch (F2)
  - a missing variant dir is FATAL before any run

Lifted from the reviewer's probe (e), 2026-09-04.
"""

import importlib.util
import json
import os
import types

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(HERE, "..", "chalette-dev", "skills", "cr-benchmark", "scripts")


def _load_runner():
    spec = importlib.util.spec_from_file_location(
        "bench_runner", os.path.join(SCRIPTS, "bench_runner.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


AUTH = json.dumps({"type": "result", "is_error": True, "num_turns": 1, "total_cost_usd": 0,
                   "duration_api_ms": 0, "session_id": "s1",
                   "usage": {"input_tokens": 0, "output_tokens": 0},
                   "result": "Failed to authenticate: OAuth session expired and could not be refreshed"})
OTHER = json.dumps({"type": "result", "is_error": True, "num_turns": 1, "total_cost_usd": 0.01,
                    "session_id": "s2", "usage": {"input_tokens": 5, "output_tokens": 7},
                    "result": "Some unrelated tool error"})
OK = json.dumps({"type": "result", "is_error": False, "num_turns": 3, "total_cost_usd": 0.5,
                 "session_id": "s3", "usage": {"input_tokens": 100, "output_tokens": 50},
                 "result": "Done.", "modelUsage": {"claude-opus-5": {"outputTokens": 50}}})


@pytest.fixture
def rig(tmp_path, monkeypatch):
    br = _load_runner()
    real_run = br.subprocess.run
    calls = []
    fake_cr1 = tmp_path / "cr1"
    (fake_cr1 / "command-room" / ".claude-plugin").mkdir(parents=True)
    tasks = json.loads(open(os.path.join(SCRIPTS, "tasks.json"), encoding="utf-8").read())["tasks"]

    def drive(argv, script):
        """Run bench_runner.main() with `script` = [(rc, stdout, stderr)] per
        fake CLI call. Returns (exit code, RUNLOG rows, runs dir)."""
        calls.clear()
        it = iter(script)

        def fake_run(cmd, cwd=None, env=None, **kw):
            if cmd[0] != "fake-claude":
                return real_run(cmd, cwd=cwd, env=env, **kw)
            rc, out, err = next(it)
            ws = br.Path(cwd)
            g = json.loads((ws / "_hq" / "connectors" / "granola_responses.json")
                           .read_text(encoding="utf-8"))
            calls.append({"cmd": cmd, "granola": g["granola_get_transcript"]["doc_ids"]})
            return types.SimpleNamespace(returncode=rc, stdout=out, stderr=err)

        runs = tmp_path / f"runs_{len(os.listdir(tmp_path))}"
        monkeypatch.setattr(br.subprocess, "run", fake_run)
        monkeypatch.setattr(br.sys, "argv", ["bench_runner.py", "--runs-dir", str(runs),
                                             "--claude", "fake-claude", "--cr1", str(fake_cr1)] + argv)
        rc = br.main()
        log = runs / "RUNLOG.jsonl"
        rows = ([json.loads(ln) for ln in log.read_text(encoding="utf-8").splitlines()]
                if log.exists() else [])
        return rc, rows, runs

    return types.SimpleNamespace(br=br, drive=drive, calls=calls, keys=list(tasks))


def test_auth_failure_on_turn_one_stops_the_batch_and_is_on_the_row(rig):
    rc, rows, runs = rig.drive(["--arm", "A", "--task", "all", "--speakers", "me_them", "--follow-up"],
                               [(1, AUTH, "")] * 10)
    assert rc == 2
    assert len(rows) == 1 and len(rig.calls) == 1          # one run of six attempted, no confirm
    r = rows[0]
    assert r["is_error"] is True and r["auth_blocked"] is True
    assert "OAuth session expired" in r["error"]
    assert all(not v for v in r["tokens"].values()) and r["total_cost_usd"] == 0
    assert r["follow_up_used"] is False
    assert r["speakers"] == "me_them" and r["run_id"].endswith("_me_them")
    assert r["transcript_set"] == {"speakers": "me_them", "set_version": "1.1", "variants_version": "1.0"}
    assert "--plugin-dir" in rig.calls[0]["cmd"]
    meta = json.loads((runs / r["run_id"] / "run_meta.json").read_text(encoding="utf-8"))
    assert meta["auth_blocked"] is True and meta["error"] == r["error"]
    raw = (runs / "RUNLOG.jsonl").read_bytes()
    assert b"\r" not in raw                                  # LF on every platform


def test_speakers_flag_injects_the_variant_and_keeps_calendar_attendees(rig):
    rig.drive(["--arm", "A", "--task", rig.keys[0], "--speakers", "me_them"], [(1, AUTH, "")])
    docs = rig.calls[0]["granola"]
    assert len(docs) == 12
    t = docs["bench_01"]["transcript"]
    assert t.startswith("Me: ") and " Them: " in t and "Sample:" not in t
    assert docs["bench_01"]["attendees"] == ["Sam Sample", "Bo Sample"]

    rig.drive(["--arm", "B", "--task", rig.keys[0], "--speakers", "named"], [(1, AUTH, "")])
    docs = rig.calls[0]["granola"]
    assert docs["bench_01"]["transcript"].startswith("Sam Sample: ")
    assert docs["bench_01"]["attendees"] == ["Sam Sample", "Bo Sample"]

    _, rows, _ = rig.drive(["--arm", "B", "--task", rig.keys[0], "--speakers", "unlabelled"], [(1, AUTH, "")])
    t = rig.calls[0]["granola"]["bench_01"]["transcript"]
    assert not t.startswith("Sam Sample: ") and not t.startswith("Me: ")
    assert rig.calls[0]["granola"]["bench_01"]["attendees"] == ["Sam Sample", "Bo Sample"]
    assert rows[0]["speakers"] == "unlabelled" and rows[0]["run_id"].endswith("_unlabelled")


def test_non_auth_error_is_recorded_and_the_batch_continues(rig):
    rc, rows, _ = rig.drive(["--arm", "B", "--task", ",".join(rig.keys[:2]), "--speakers", "named"],
                            [(1, OTHER, ""), (0, OK, "")])
    assert rc == 0 and len(rows) == 2
    assert rows[0]["is_error"] is True and rows[0]["auth_blocked"] is False
    assert rows[0]["error"] == "Some unrelated tool error"
    assert rows[1]["is_error"] is False and "error" not in rows[1]
    assert rows[0]["speakers"] == "named" and not rows[0]["run_id"].endswith("_named")
    assert "--plugin-dir" not in rig.calls[0]["cmd"]


def test_non_json_reply_with_not_logged_in_on_stderr_stops_the_batch(rig):
    rc, rows, _ = rig.drive(["--arm", "B", "--task", ",".join(rig.keys[:2])],
                            [(1, "", "Error: not logged in\n"), (0, OK, "")])
    assert rc == 2 and len(rows) == 1
    assert rows[0]["auth_blocked"] is True and "not logged in" in rows[0]["error"]
    assert rows[0]["tokens"]["output"] is None


def test_auth_failure_on_the_confirm_turn_is_recorded_and_stops_the_batch(rig):
    """Review F2: turn 1 succeeds, the --resume confirm turn cannot
    authenticate -> the confirm did NOT happen and the batch stops."""
    rc, rows, _ = rig.drive(["--arm", "B", "--task", ",".join(rig.keys[:2]), "--follow-up"],
                            [(0, OK, ""), (1, AUTH, ""), (0, OK, "")])
    assert len(rig.calls) == 2 and "--resume" in rig.calls[1]["cmd"]
    assert rc == 2 and len(rows) == 1
    r = rows[0]
    assert r["is_error"] is False                    # turn 1 was fine
    assert r["follow_up_used"] is False
    assert "OAuth session expired" in r["follow_up_error"]
    assert r["auth_blocked"] is True


def test_confirm_turn_that_succeeds_is_used_and_summed(rig):
    rc, rows, _ = rig.drive(["--arm", "B", "--task", rig.keys[0], "--follow-up"],
                            [(0, OK, ""), (0, OK, "")])
    assert rc == 0 and rows[0]["follow_up_used"] is True and "follow_up_error" not in rows[0]
    assert rows[0]["tokens"]["output"] == 100 and rows[0]["num_turns"] == 6


def test_missing_variant_dir_is_fatal_before_any_run(rig, tmp_path):
    empty = tmp_path / "no_variants"
    empty.mkdir()
    (empty / "manifest.json").write_text("{}", encoding="utf-8")
    rig.br.BENCH_TRANSCRIPTS = empty
    with pytest.raises(SystemExit) as exc:
        rig.drive(["--arm", "B", "--task", rig.keys[0], "--speakers", "me_them"], [(0, OK, "")])
    assert "me_them transcript variant missing" in str(exc.value)
    assert "_generate_bench_transcripts.py --speakers me_them" in str(exc.value)
    assert rig.calls == []
