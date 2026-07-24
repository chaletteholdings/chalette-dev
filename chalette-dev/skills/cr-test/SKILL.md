---
name: cr-test
description: "INTERNAL — the single entry point for testing Command Room. Orchestrates the full battery in tiers (static guards → unit → runtime → integration → ship verdict), fail-fast, and emits ONE consolidated GREEN/HOLD/RED verdict. Replaces having to remember run-command-room-tests / synthetic-workspace-runtime-test / bug-regression-suite / cross-skill-interaction-test / ship-readiness-gate individually — it sequences and delegates to them. Fires on 'cr test', 'test command room', 'run the battery', 'full test', 'badass test', 'cr test --quick', 'cr test --ship'. Plugin-developer use only; not customer chat."
---

# cr-test — the Command Room test battery

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
3. **A hardcoded test list goes stale silently** — `run-command-room-tests`
   shipped running 5 of 40+ suites for months. This flow calls
   `tests/run_all.py`, which DISCOVERS every suite at call time. New test file =
   automatically in the battery.
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
| 5 · attended | Cowork paste-back LLM-behavior verification | delegate → `verify-cr-release` (operator-attended; NOT auto-run) | the ship operator's call (`may_ship`) |

Tiers 0–2 are pure code and run in this skill directly (~10s). Tiers 3–5 are
heavier and delegate to the specialist skills, which keep their own logic — this
flow just sequences them and rolls their verdicts into one.

## Modes

| Trigger | Runs | When |
|---|---|---|
| `cr test --quick` | tiers 0–1 only | mid-edit sanity check, seconds |
| `cr test` / `test command room` / `run the battery` | tiers 0–2 (full code battery) | default — before any commit |
| `cr test --ship` / `badass test` | tiers 0–4 (adds integration + ship verdict) | before a production-promote decision |
| `cr test --attended` | tiers 0–5 (adds the Cowork loop) | full pre-release gate with the operator present |

## Behavior

### Step 1 — Locate the plugin + run the code battery (tiers 0–2)

You are looking for the `command-room/` directory — the one with `tests/run_all.py`
inside it. It lives in a cr1 checkout (the canonical edit surface), or in an
installed plugin. **Search; do not assume a path.** This step used to hardcode one
marketplace location and shell out through `sed`/`ls`, which meant it found nothing
on a normal contributor machine and could not run on Windows at all.

Check these in order and take the first hit where `tests/run_all.py` actually exists:

0. **`cr1_clone` from the operator profile** — read `config/operator.json`, then overlay
   `config/operator.local.json` per-key if present (gitignored; only M has one). If the merged
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
python tests/run_all.py                 # default — tiers 0-2
python tests/run_all.py --tier guard    # --quick
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

Point the operator to `verify-cr-release` for the Cowork paste-back loop (LLM-behavior /
voice / tone — the ~20% no code battery can cover). Do NOT try to automate this;
it needs the operator present. Just hand off cleanly with the version under test.

### Step 5 — One consolidated verdict

```
Command Room test battery — v{version}  ({mode})

Tier 0 · guard          11/11 ✓
Tier 1 · unit           31/31 ✓
Tier 2 · runtime         1/1  ✓
Tier 3 · integration     —    (run with --ship)
Tier 4 · ship verdict    —    (run with --ship)

Code battery: GREEN (43/43, 9.6s)

VERDICT: GREEN — safe to commit.
```

Verdict logic:
- **RED** — any tier 0–2 suite failed. Not safe to commit. List failures + fixes.
- **HOLD** — code battery GREEN but a tier 3 integration gate failed OR
  ship-readiness-gate returned HOLD/BLOCKED. Safe to commit; NOT safe to promote.
- **GREEN** — everything run was green. For `cr test` (tiers 0–2): safe to commit.
  For `cr test --ship`: ship-readiness-gate said PROMOTE → safe to promote.

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
their logic; cr-test is the conductor:

- `run-command-room-tests` → superseded as an entry point. Its job (run the
  python suites) is now `tests/run_all.py`, which cr-test calls and which
  auto-discovers ALL suites instead of a stale list of five. Keep the old trigger
  working as an alias to `cr test --quick` if convenient.
- `synthetic-workspace-runtime-test`, `cross-skill-interaction-test`,
  `bug-regression-suite` → tier 3, delegated.
- `ship-readiness-gate` → tier 4, delegated.
- `verify-cr-release` → tier 5, attended, handed off (not auto-run).
- `ship-cr-plugin` → the release flow. Run cr-test --ship BEFORE it; it has its
  own in-line structural-guard gate as a backstop.

## Failure modes

- **Plugin not found** → clear error listing every location tried, plus the
  `CR1_ROOT` hint. Never clone to manufacture a path; never guess a verdict.
- **~30 suites red with `UnicodeEncodeError: charmap` (Windows)** → not a failure.
  See Step 1. Report GREEN-pending-rerun, not RED.
- **A tier-3 specialist skill isn't installed** → skip it with a note, don't fail
  the whole battery; downgrade to HOLD only if a gate that DID run failed.
- **run_all.py missing (old plugin install)** → fall back to listing tests/ and
  running each `run_*_test.py`, or tell M to update the plugin.
