---
name: cr-benchmark
description: INTERNAL TEST EQUIPMENT — the BENCH1 benchmark lane. Runs Command Room against bare Claude with mocked connectors on synthetic Sample/Stone fixtures, scores both arms with deterministic countable metrics (commitment-extraction P/R by route, entity resolution right/wrong/missed, hallucinated rows, leak survivals, wall-clock + tokens), and submits scorecards to OpenAI Codex adversarial review so the result is official. Fires on 'run the benchmark', 'cr benchmark', 'benchmark command room', 'bench pilot', 'score the benchmark runs'. Plugin-developer use only; never fires in customer chat. Does NOT fire on 'cr test' / 'run the battery' (cr-test) or 'synthetic e2e' (synthetic-workspace-runtime-test).
---

# cr-benchmark — the BENCH1 lane

Measures what the Command Room scaffolding adds over the same model without
it, in countable terms, with a non-Claude grader. Spec ruling 2026-08-26 (M):
two arms only, model pinned to Opus, no other-harness arm ever.

## Ground rules (binding)

1. **Synthetic only.** Fixtures and transcripts use the Sample/Stone roster.
   Client data never enters this lane, in any form.
2. **cr1 is read-only.** The plugin under test loads via `--plugin-dir` from
   the operator profile's `cr1_clone`. `git status` there must stay clean.
3. **Model pinned: `claude-opus-5`, both arms, every run** (M ruling
   2026-08-27 — the model CR clients run in production). The exact model id
   each run reports is logged; runs on different model ids are never
   aggregated. The 2026-08-27 pilot ran at claude-opus-4-8 and is
   calibration-only, never official.
4. **Labels are frozen.** No label edit after a run without re-running every
   affected arm.
5. **Integrity basis (M ruling 2026-08-27): reproducibility, not authority.**
   Methodology, deterministic generators, frozen labels, scoring code, and
   every raw run artifact are committed together — every scorecard cell is
   recomputable from the artifacts, and the v1 external audit is the standing
   verification invitation in the methodology doc §7 (Andrés's engineer or
   any outside reviewer). The codex adversarial-review hooks
   (`/codex:adversarial-review`, `openai/codex-plugin-cc`) stay in the
   harness DORMANT as the designed hardening step — enabling them is M's
   explicit decision, never a default.

## Layout

```
scripts/_generate_bench_transcripts.py   labeled transcript set (deterministic)
scripts/tasks.json                       the 6 frozen task prompts
scripts/bench_mcp_server.py              mock gmail/calendar/granola MCP servers
scripts/bench_runner.py                  one headless run per (arm x fixture x task)
scripts/bench_scorer.py                  deterministic scoring + scoreboard
fixtures/bench_transcripts/              12 transcripts + labels/ + manifest.json
runs/                                    run artifacts + RUNLOG.jsonl (append-only)
references/rubric.md                     metric definitions + judgment rules
references/run-protocol.md               step-by-step run + grading protocol
```

## Running

Read `references/run-protocol.md` and follow it exactly. Short form:

```bash
cd skills/cr-benchmark/scripts
python _generate_bench_transcripts.py --check          # labels still valid
python bench_runner.py --arm A --fixture clean_workspace --task all --model claude-opus-5
python bench_runner.py --arm B --fixture clean_workspace --task all --model claude-opus-5
python bench_scorer.py --runs-dir ../runs --cr1 <cr1_clone>
```

Pilot = 12 runs on clean_workspace (DONE 2026-08-27 at claude-opus-4-8;
calibration-only, never official). **Battery: ruled GO by M for 2026-08-28**
— 2 arms x 6 tasks x {clean, mature} at `claude-opus-5` with `--follow-up`
(t1's confirm turn, ruled in 2026-08-27). Codex grading starts at phase 5,
after M's codex CLI setup.

## Routing

- 'cr test', 'run the battery', 'badass test' → **cr-test** (the ship battery).
- 'synthetic e2e', 'pre-ship runtime gate' → **synthetic-workspace-runtime-test**.
- This skill is the benchmark lane only: arms, scoring, grading, run log.
