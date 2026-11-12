---
name: battery
description: "INTERNAL — the single entry point for testing Command Room. Orchestrates the full battery in tiers, fail-fast, and emits ONE consolidated GREEN/HOLD/RED verdict. Replaces having to remember synthetic-workspace-runtime-test / bug-regression-suite / cross-skill-interaction-test / ship-readiness-gate individually — it sequences and delegates to them. Fires on 'run the battery', 'test command room', 'full test', 'badass test', 'battery --quick', 'battery --ship', 'battery --attended'. Absorbs two retired entry points. run-command-room-tests: 'internal: run plugin tests', 'run command room tests', 'command room health check', 'verify plugin code' alias 'battery --quick' — the quick check, via tests/run_all.py. verify-cr-release: 'verify cr release', 'run verification suite' alias '--attended'; 'pre-ship check' aliases '--ship'. Tier 5 = the dogfood ritual, walked by hand. Plugin-developer use only; not customer chat. Not 'test #N' (cr1-test, a fixed issue)."
---

# battery — the Command Room test battery

> **Team toolkit (chalette-dev).** Anyone on the team may run this. A contractor runs it against the synthetic fixtures or a copied test brain only, never a real client folder, and never ships or promotes. The owner's own workspace needs the owner's yes in the chat. Who is running is read the way `cr1-test` reads it, from `config/operator.json`.

**One command, the whole battery, one verdict.** This is the badass testing flow:
it sequences every layer of Command Room verification in the order learned from
the deep-testing sessions (May 2026), fails fast at the cheapest tier, and ends
with a single GREEN / HOLD / RED call. You stop having to remember which of the
ten testing skills to run — you run this, it runs them, in the right order.

## Why this exists (the learnings it bakes in)

The deep-testing weeks surfaced a layered truth about what catches what:

1. **Static guards catch a different bug class than unit tests** — and unit tests
   catch a different class than runtime simulation
   (`feedback_static_analysis_vs_runtime_exercise`). Five rounds of static checks
   each found 1–3 bugs; the runtime pass then found 15 the static rounds were
   structurally blind to. So the battery must run ALL layers, not pick one.
2. **Tests-green / prod-dead is real** — a reader filtering for an event type no
   writer emits passes its unit test (the test feeds it the phantom name) while
   doing nothing in every real workspace. The `run_event_contract_test` guard
   exists for exactly this and runs in the guard tier.
3. **A hardcoded test list goes stale silently** — the old `run-command-room-tests`
   skill (retired in v0.3.1, its triggers now alias to `battery --quick`) shipped
   running 5 of 40+ suites for months. This flow calls `tests/run_all.py`, which
   DISCOVERS every suite at call time. New test file = automatically in the battery.
4. **Runtime > static for destructive bugs** — the window=3 quarantine bug that
   would have destroyed real customer events passed every unit test; the runtime
   exercise caught it. Runtime tier is non-optional before a ship verdict.

## Tiers (run order; fail-fast)

| Tier | What | How it runs | Gate |
|---|---|---|---|
| 0 · guard | structural / write-time invariants: privacy, hardcoded-drive, .md-deliverables, retired-skills, jargon, leak scan, entity-resolve, **event-contract**, customer-voice, personification, source-of-truth | `tests/run_all.py --tier guard` | **HARD** — stop on any fail |
| 1 · unit | pure-python suites: renderer, helpers, cru_match, backfill, writers, detectors, schedule-config, widget-transport, … (all auto-discovered) | `tests/run_all.py --tier unit` | **HARD** |
| 2 · runtime | code-path simulation vs synthetic data: `runtime_exercise_*`, spec-example render | `tests/run_all.py --tier runtime` | **HARD** |
| 3 · integration | multi-fire sequences + regression vs a real/synthetic workspace | delegate → `synthetic-workspace-runtime-test`, `cross-skill-interaction-test`, `bug-regression-suite` | **SOFT** (HOLD) |
| 4 · ship verdict | unattended pre-promote battery + bug-catalog cross-ref | delegate → `ship-readiness-gate` | emits PROMOTE/HOLD/BLOCKED |
| 5 · attended | the dogfood ritual: freeform real-workspace dogfood **+** walk `references/VERIFICATION_PLAN.md` against a fresh test workspace | hand off to the operator — **no skill; walked by hand** (NOT auto-run) | the ship operator's call (`may_ship`) |

Tiers 0–2 are pure code and run in this skill directly: together they are cr1's full battery, about 35 to 47 minutes on the dev PC. Tiers 3–5 are
heavier and delegate to the specialist skills, which keep their own logic — this
flow just sequences them and rolls their verdicts into one.

## Modes

| Trigger | Runs | When |
|---|---|---|
| `battery --quick` | cr1's quick check (`run_all.py --quick`: the guard tier plus every suite but the slow ones), about 4 to 8 minutes | before every pull request, on the builder's PC (the only Windows check); the Mac runs the same check as the merge gate |
| `internal: run plugin tests` / `run command room tests` / `command room health check` / `verify plugin code` | the quick check (alias for `battery --quick`) | the retired run-command-room-tests entry point, folded in here (v0.3.1) |
| `test command room` / `run the battery` | tiers 0–2 (the full battery) | on cr1's main once every 5 merges, and before a promote (owner ruling 2026-11-11, cr1#1041); never per pull request |
| `battery --ship` / `badass test` | tiers 0–4 (adds integration + ship verdict) | before a production-promote decision |
| `battery --attended` | tiers 0–5 (adds the Cowork loop) | full pre-release gate with the operator present |

## Behavior

### Step 1 — Locate the plugin + run the code battery (tiers 0–2)

You are looking for the `command-room/` directory — the one with `tests/run_all.py`
inside it. It lives in a cr1 checkout (the canonical edit surface), or in an
installed plugin. **Search; do not assume a path.** This step used to hardcode one
marketplace location and shell out through `sed`/`ls`, which meant it found nothing
on a normal contributor machine and could not run on Windows at all.

Check these in order and take the first hit where `tests/run_all.py` actually exists:

0. **`cr1_clone` from the operator profile** — read `config/operator.json`, then overlay
   `config/operator.local.json` per-key if present (gitignored; not every operator has one). If the merged
   `cr1_clone` is set and `<cr1_clone>/command-room/tests/run_all.py` exists, use it outright.
   This is the operator's canonical-clone preference expressed via config (M defaults it to
   `~/repos/cr1-canonical`), not a hardcoded path in prose.
   ```python
   import json, os, sys
   op = {}
   for _n in ("operator.json", "operator.local.json"):
       _p = os.path.join(SKILL_PLUGIN_ROOT, "config", _n)
       if os.path.exists(_p): op.update(json.load(open(_p)))
   # SKILL_PLUGIN_ROOT must be a NATIVE path — on Windows `C:/Users/…`, never an MSYS
   # `/c/Users/…` (convert with `cygpath -m`): python.exe reads `/c/…` as `C:\c\…`, both
   # files miss, and an empty profile silently becomes the default. Fail loud instead.
   if not op: sys.exit(f"FATAL: operator profile unreadable under {SKILL_PLUGIN_ROOT}")
   ```
1. **`$CR1_ROOT`** — if that env var is set, `$CR1_ROOT/command-room` wins outright.
   This is the escape hatch for a checkout in an unusual place.
2. **A cr1 checkout under the home directory** — glob `~/*/cr1*/command-room` and
   `~/cr1*/command-room`. Covers `~/repos/cr1`, `~/src/cr1`, `~/code/cr1`, and also
   suffixed clones like `~/repos/cr1-canonical`. This is the normal case and the one
   to expect. The trailing `*` is load-bearing: matching only a folder named exactly
   `cr1` misses a canonical clone entirely and drops you into rule 4, which is how
   you end up testing a stale or client copy without noticing.

   **If several match**, prefer one named `cr1-canonical`; otherwise take the first
   with a real `tests/run_all.py`. Either way, when there was more than one candidate,
   **say which you picked and list the others** — a silently-chosen target is the
   failure this whole step exists to prevent.
3. **Walking up from the working directory** — if you are already inside a checkout,
   look at each parent for a `command-room/tests/run_all.py`.
4. **A marketplace install** — `~/.claude/plugins/marketplaces/*/command-room`.
   These are installs, not edit surfaces, and a machine can hold several from
   different sources. **If more than one matches, do not guess** — report them all
   and ask for `CR1_ROOT`. Picking one silently risks reporting a verdict for a
   stale or client copy while the contributor believes they tested their own work.
5. **The Cowork sandbox** — `<session>/mnt/.remote-plugins/plugin_*`, where `<session>`
   is `$CLAUDE_CODE_TMPDIR` with the trailing `/tmp` stripped.

Use whatever tooling the session gives you. **On Windows prefer PowerShell**
(`Test-Path`, `Get-ChildItem`): the Bash tool there runs with a stripped PATH, so
`ls`, `sed`, and `head` are frequently missing — the old snippet's core problem.

**If nothing hits: STOP and say so.** Report every location you tried and tell the
contributor to set `CR1_ROOT`. Do **not** clone cr1 to make one of these paths exist
— a missing checkout is a setup problem to surface, and a fresh clone dropped into
the plugins directory can get picked up as a marketplace and shadow the real install.

Then, from that directory:

```
python tests/run_all.py           # run the battery: tiers 0-2, the full battery
python tests/run_all.py --quick   # battery --quick: the quick check CI runs (not a battery)
```

On Windows, a wall of `UnicodeEncodeError: charmap` across ~30 suites is **not** a
real failure — suites crash printing the ✓ glyph *after* their check passed. The
runner pins UTF-8 itself; against an older checkout that predates that, re-run with
`PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` set. Never report those as bugs.

`run_all.py` already fails fast (stops after the guard tier if a structural
invariant breaks) and prints a per-suite PASS/FAIL table + a TOTAL line + a final
`Battery GREEN` / `Battery RED`. Parse the TOTAL line and the final verdict line.

**If the code battery is RED: STOP here.** Do not run tiers 3–5 — a structural or
unit failure means the higher tiers are testing broken code. Surface the failing
suite names + their summary lines and the likely fix.

### Step 2 — Integration tier (only on `--ship` / `--attended`, only if 0–2 GREEN)

Delegate, in order, capturing each verdict:

1. `synthetic-workspace-runtime-test` — fires canonical surfaces against the
   fixtures; checks the invariant catalog.
2. `cross-skill-interaction-test` — multi-fire sequences with substrate snapshots
   (catches order-dependent / cross-skill state bugs).
3. `bug-regression-suite` — re-runs the known-bug catalog against the workspace.

These are SOFT gates: a failure downgrades the final verdict to HOLD, not RED,
because they can have environmental causes (unpopulated fixtures, real-workspace
edge cases). Surface what failed and why.

### Step 3 — Ship verdict (only on `--ship` / `--attended`)

Delegate to `ship-readiness-gate`, which runs its own pre-promote battery +
bug-catalog cross-reference and emits PROMOTE / HOLD / BLOCKED with a verdict doc.
Fold its verdict into the consolidated call below.

### Step 4 — Attended tier (only on `--attended`)

Hand off to the operator for **the dogfood ritual** — the LLM-behavior / voice / tone
layer no code battery can cover. There is no skill for this tier; it is walked by hand.
Do NOT try to automate it, and do NOT report a tier-5 result you did not watch happen.

Hand off cleanly with the version under test and **both halves**, because they cover
different things:

1. **Freeform dogfood** — the operator uses Command Room in their own Cowork against
   their own real workspace, as a customer, and reads the outputs. Catches voice, tone,
   judgment quality, and real-data edge cases. This is `CLAUDE.md` Track A.
2. **The structured plan** — `references/VERIFICATION_PLAN.md`, walked against a
   **fresh, empty** test workspace seeded with the synthetic persona. Catches what
   dogfood structurally cannot: virgin-workspace onboarding, honest empty states, the
   destructive/garbage-input probes (Phase 3 deliberately tries deletions, so it must
   never run against a real workspace), late-fire behavior, and the fresh-loader skill
   canary. The implementer maintains this plan; ~90% is stable release to release.

Dogfood alone is **not** tier 5. If the operator is only doing (1), say so in the verdict
rather than calling the attended tier covered.

### Step 5 — One consolidated verdict

```
Command Room test battery — v{version}  ({mode})

Tier 0 · guard        108/108 ✓
Tier 1 · unit          662/662 ✓
Tier 2 · runtime        16/16  ✓
Tier 3 · integration     —    (run with --ship)
Tier 4 · ship verdict    —    (run with --ship)

Code battery: GREEN (786/786, 2,799 s)

VERDICT: GREEN — the batch on main stands; merging may continue.
```

For `battery --quick` the verdict is one line, and it is never called a battery:
`Quick check: GREEN (693/693, 285 s). Not a battery; the full battery runs on main every 5 merges.`

Verdict logic:
- **RED** — any tier 0–2 suite failed (a suite that timed out is re-run once first). On main, a failure that was not already red at the previous every-5 run stops merging, and a fix build starts at once; a known red does not. Log every failure on cr1#1041 (date, range, suite, culprit pull request, files, area, kind). Revert-first is retired. List failures + fixes.
- **HOLD** — code battery GREEN but a tier 3 integration gate failed OR
  ship-readiness-gate returned HOLD/BLOCKED. Safe to commit; NOT safe to promote.
- **GREEN** — everything run was green. For `run the battery` (tiers 0–2) on main: the batch stands.
  For `battery --ship`: ship-readiness-gate said PROMOTE → safe to promote.

Per CONTRACT Rule 4: this is internal dev output — test-suite names and tier
labels are fine here (M is the developer), but never narrate this into customer
chat.

## What this flow does NOT do

- Does not modify plugin files or workspace data (read-only verification).
- Does not commit, push, or promote — it produces the verdict that GATES those.
- Does not replace the specialist skills — it sequences and delegates to them.
  Run a specialist directly when you want just that one layer.

## Relationship to the testing-skill family (consolidation map)

This skill is the **single entry point**. The specialists still exist and keep
their logic; battery is the conductor:

- `run-command-room-tests` → **retired and deleted in v0.3.1** (it never had a
  delegating caller — battery always called `tests/run_all.py` directly, which
  auto-discovers ALL suites instead of its stale list of five). Its trigger phrases
  live on in this skill's description as aliases for `battery --quick`.
- `synthetic-workspace-runtime-test`, `cross-skill-interaction-test`,
  `bug-regression-suite` → tier 3, delegated.
- `ship-readiness-gate` → tier 4, delegated.
- `verify-cr-release` → **retired and deleted** (the paste-back orchestrator for tier 5).
  Its niche — driving the attended loop prompt-by-prompt and auto-classifying pasted-back
  responses — closed: dogfood-before-promote plus BIG-TEST now carry the attended layer,
  per the owner's ruling. Tier 5 is now **the dogfood ritual, walked by hand** (see Step 4); the
  skill's own state tracking, prompt templates, and verdict-doc generation were dropped as
  ceremony. What was worth keeping was kept, not deleted: its verification plan is now
  `battery/references/VERIFICATION_PLAN.md` (tier 5's structured half) and its response
  classifier + findings-log format moved to `bug-regression-suite/references/`, where
  their existing citers still reach them. Its trigger phrases were **re-homed onto this
  skill**, not orphaned: `verify cr release` and `run verification suite` alias
  `battery --attended`, and `pre-ship check` aliases `battery --ship` — all three are
  claimed in this skill's own description above. Only `continue verification` /
  `resume verification` were **deliberately dropped**: they resumed a stateful session
  that no longer exists, so re-homing them would promise resumption nothing provides.
- `ship-cr-plugin` → the release flow. Run battery --ship BEFORE it; it has its
  own in-line structural-guard gate as a backstop.

## Failure modes

- **Plugin not found** → clear error listing every location tried, plus the
  `CR1_ROOT` hint. Never clone to manufacture a path; never guess a verdict.
- **~30 suites red with `UnicodeEncodeError: charmap` (Windows)** → not a failure.
  See Step 1. Report GREEN-pending-rerun, not RED.
- **A tier-3 specialist skill isn't installed** → skip it with a note, don't fail
  the whole battery; downgrade to HOLD only if a gate that DID run failed.
- **run_all.py missing (old plugin install)** → fall back to listing tests/ and
  running each `run_*_test.py`, or tell the owner to update the plugin.
