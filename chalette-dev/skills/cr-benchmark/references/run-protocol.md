# BENCH1 run protocol

Follow in order. Every step is idempotent; a failed run is re-run, never
patched. `<cr1>` = the operator profile's `cr1_clone` (M: `~/repos/cr1-canonical`).

## 0. Preconditions (each session)

```bash
cd <chalette-dev>/chalette-dev/skills/cr-benchmark/scripts
python ../../synthetic-workspace-runtime-test/fixtures/_generate_fixtures.py --cr1 <cr1> --check
python _generate_bench_transcripts.py --check
git -C <cr1> status --short          # MUST be empty; this lane never writes cr1
```

Windows: `set PYTHONUTF8=1` first. The `claude` CLI must be on PATH or at
`~/.local/bin/claude.exe`; runs use the operator's existing subscription auth
(never an API key, never `--bare`).

## 1. Runs

One invocation per arm; each task inside is its own fresh-workspace run:

```bash
python bench_runner.py --arm A --fixture clean_workspace --task all --model claude-opus-5
python bench_runner.py --arm B --fixture clean_workspace --task all --model claude-opus-5
```

**Model pin (M ruling 2026-08-27): official runs are `claude-opus-5`** — the
model CR clients run in production. The 2026-08-27 pilot ran at
claude-opus-4-8 and stands as scorer calibration only; no pilot number is
official, and the delta is noted in RUNLOG.

**t1 confirm turn (`--follow-up`) — RULED IN by M, 2026-08-27.** At
claude-opus-5 the t1 prompt routes to the preview-first scan flow, which by
design writes nothing until the user confirms (draft posture — a trust
feature, documented as a product observation in the methodology doc §6) —
verified in the 2026-08-27 re-check (`runs_recheck/`): a full extraction
preview to `_hq/scans/`, zero events. Battery t1 runs WITH `--follow-up`:
the runner resumes the same session with the verbatim-identical confirmation
("Yes - log all of them.") on BOTH arms, sums both turns' usage into the run
totals, and keeps both raw outputs. The confirmation text is frozen with the
prompts.

**Battery invocation (ruled GO for 2026-08-28, claude-opus-5):**

```bash
python bench_runner.py --arm A --fixture clean_workspace  --task all --follow-up
python bench_runner.py --arm B --fixture clean_workspace  --task all --follow-up
python bench_runner.py --arm A --fixture mature_workspace --task all --follow-up
python bench_runner.py --arm B --fixture mature_workspace --task all --follow-up
python bench_scorer.py --runs-dir ../runs --cr1 <cr1>
```

(`--model` defaults to the pinned `claude-opus-5`; `--follow-up` only fires
on tasks with a defined confirmation, i.e. t1.)

What the runner guarantees per run:

- fresh temp copy of the fixture; nothing persists between runs
- bench transcripts injected into the granola connector fixture (both arms)
- Arm B's CLAUDE.md swapped to the neutral stub (same identity, no CR rules)
- mock connectors attached with `--strict-mcp-config` (nothing else loads)
- Arm A loads the plugin via `--plugin-dir <cr1>/command-room`; Arm B loads
  no plugin (verify `claude plugin list` prints none installed)
- artifacts + `run_meta.json` under `runs/<run_id>/`; a row appended to
  `runs/RUNLOG.jsonl`

Sanity-check the first run of each arm before letting the rest proceed:
open `chat.txt`, confirm the model id in `run_meta.json` is the pinned Opus
id, and for Arm A confirm `events_diff.jsonl` is non-empty on t1.

## 2. Scoring

```bash
python bench_scorer.py --runs-dir ../runs --cr1 <cr1>
```

Writes `scorecard.json` per run and `runs/scoreboard.{json,md}`. Read the
scoreboard; investigate any ERROR/TIMEOUT row and any
`receipt_cross_check.agree: false` before quoting numbers.

## 3. Pilot gate (hard stop)

The pilot is 12 runs (2 arms x 6 tasks, clean_workspace). After scoring:

1. Hand-verify the pilot: for each t1 run, spot-check 10 planted items'
   evidence lines in the scorecard against the raw chat/events.
2. Report to M: scoreboard + measured tokens-per-run at Opus.
3. **Stop.** M schedules the full battery (adds mature_workspace; 24 runs
   total) against the shared weekly usage pool. Do not start the battery,
   ablation arms, or codex grading without that scheduling ruling.

## 4. Integrity + external audit (phase 5, reworked by M ruling 2026-08-27)

**Codex is DORMANT — M holds that spend until results prove out.** The v1
integrity basis is reproducibility (everything committed, every cell
recomputable) plus the standing human-verification invitation in the
methodology doc §7 (Andrés's engineer or any outside reviewer audits the
committed scorecards against the raw artifacts; confirmed findings block the
affected numbers until resolved).

The codex hooks below are the DESIGNED HARDENING STEP — kept documented and
runnable so enabling them later is one decision, not a rebuild. Do NOT run
them without M's explicit go.

Prereqs if ever enabled (M runs these once): `npm i -g @openai/codex`,
`codex login`, `claude plugin marketplace add openai/codex-plugin-cc`
(exactly that repo — look-alike forks exist), install the codex plugin,
`/codex:setup`.

Then, per graded run set:

```bash
git add runs/ && git commit -m "bench: <set> artifacts + scorecards"
/codex:adversarial-review --scope branch verify the BENCH1 scorecards against the raw run artifacts in skills/cr-benchmark/runs/ - recompute the counts, hunt for scoring bias and for evidence lines that do not support their assigned outcome
```

Store the codex verdict JSON at `runs/<set>_codex_verdict.json`, set
`codex_verdict` on the affected RUNLOG rows (append correction rows — the
log is append-only, never rewritten), and only then mark numbers official.
A needs-attention verdict blocks publication of the affected numbers until
resolved and re-reviewed.

## 5. Battery + v2 ablations

Battery = pilot protocol plus `--fixture mature_workspace`, both arms.
v2 ablation arms (CR minus entity-resolve / capture-gate / routing) are
specified in the instructions doc; they reuse this protocol with a modified
`--plugin-dir` payload and are NOT built until M green-lights them with the
measured per-run cost from the battery.
