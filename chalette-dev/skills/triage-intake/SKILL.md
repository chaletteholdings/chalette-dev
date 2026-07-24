---
name: triage-intake
description: "Process the intake queue (intake_root from config/operator.json, default ~/cr-intake/) — verify each captured bug against the cr1 clone (graduated: read-trace → test slice → synthetic-fixture repro), feasibility-check each idea/skill for trigger collisions and overlap, sweep for same-class sites, then write a build spec (SPEC_*.md) or surface a kill/park recommendation, and move each file to its status folder. Companion to capture-for-code: capture writes items the moment they're spotted; triage-intake verifies and specs them with the repo open. Use when the operator says: 'triage intake', 'triage the intake', 'process intake', 'process the intake queue', 'what's in intake', 'run intake triage', 'work the queue', 'triage the queue'. DOES NOT fire on 'bug intake' / 'process bug report' / customer-inbound reports. DOES NOT build or fix code — output is specs and decisions; builds happen in fresh sessions from the spec. DOES NOT fire on 'triage my inbox' or 'commitment triage' (Command Room product skills)."
---

# triage-intake

The verify half of the intake pair. Sibling of `capture-for-code`. Turns raw captures into either a build-ready `SPEC_*.md` or an honest "don't build this" — never leaves an item in limbo silently.

> **Operator-aware.** Read `config/operator.json`, then overlay `config/operator.local.json` per-key if present (gitignored; the operator's local overlay — only M has one). Keys used: `intake_root` (queue location, default `~/cr-intake`), `cr1_clone` (the repo to verify against), `chalette_clone` (a chalette030 clone, when the item targets the chalette plugin; only M has one), `specs_dir` (where specs land; default `<intake_root>/specs/`), `parking_doc` (PARK target; default `<intake_root>/PARKING.md`), `allowed_targets`, `may_ship`. **Non-M operators verify against synthetic fixtures ONLY** (`skills/synthetic-workspace-runtime-test/fixtures/`) — never a real workspace. `may_ship: false` means specs are handed to M, never built into a release by you.
> ```python
> import json, os
> op = {}
> for _n in ("operator.json", "operator.local.json"):
>     _p = os.path.join(SKILL_PLUGIN_ROOT, "config", _n)
>     if os.path.exists(_p): op.update(json.load(open(_p)))
> ```

## What this is and is not

**Is:** a batch triage that, per item: locates the code, verifies or refutes the capture against the actual repo, sweeps for the same class of problem elsewhere, sizes it, writes a spec sized to the item, and ends with a one-screen decision table. File moves = the record.

**Is not:** a fix session. Even a one-line fix gets recommended, not applied — the fix happens in a normal build session (or lands as its own PR after a ruling). Not the customer-bug triage either.

## Preflight (every run)

1. **Sync the clone**: `git -C <cr1_clone> pull` — never triage against a stale tree. **INTAKE1 F4 (operator-aware):** if an item targets the chalette plugin AND `chalette_clone` is set in the merged profile, also `git -C <chalette_clone> pull` before verifying that item (only M has a chalette clone; contractors skip this).
2. List `<intake_root>/new/`. **Resurrection guard (INTAKE1 F5):** before triaging, cross-check each `new/` filename against `speced/`, `killed/`, and `done/` — an exact match means a multi-machine sync re-added an item triage already moved out of `new/`; delete-or-skip it, never re-triage. If empty: check `needs-input/` for items since answered (a ruling note appended below the questions = answered), report the queue state in two lines, done.
3. **Stale check**: items in `new/` older than 30 days go on the decision table with a kill-or-keep prompt.
4. If >5 items, state the count and confirm batch order (severity first, then oldest) — or take a subset.

## Per-item flow — BUG

1. **Read the capture. Treat `## Hypothesis (UNVERIFIED)` as a lead, never a fact.** Re-derive root cause from the repo even when the hypothesis looks right.
2. **Locate** the code path: grep skill texts AND runtime scripts — prose-only behavior won't show in `.py`; instruction-layer bugs live in SKILL.md text. Re-verify any "X doesn't exist" conclusion with a second search strategy before writing it down.
3. **Verify — graduated, cheapest sufficient level, then STOP:**
   - **L1 read-trace:** read the code path; a defect provable by reading (wrong constant, missing branch, stale string) is confirmed at L1.
   - **L2 test slice:** run the relevant existing test file(s), not the full battery.
   - **L3 fixture repro:** reproduce against the synthetic fixtures (reuse `synthetic-workspace-runtime-test` machinery) — only for behavior L1/L2 can't prove. Synthetic fixtures ONLY unless `allowed_targets` includes `real`.
   - Cosmetic/label-level items never go past L1.
4. **Same-class sweep:** grep the anti-pattern fleet-wide. The sweep count drives fix scope: surgical vs sweep vs structural.
5. **History check:** the bug-regression-suite catalog + last 5 CHANGELOG entries — regression of a known fix, or a known-issue pattern?
6. **Verdict** (always explicit):
   - `CONFIRMED` — root cause at file:line + blast radius → bug-fix spec (or "trivial — fix inline, no spec" for a provable one-liner with an obvious regression test).
   - `COULD-NOT-REPRODUCE` — first-class outcome, never silently dropped: record what was tried at which level, write 1-3 questions into the file, move to `needs-input/`.
   - `NOT-A-BUG` — working as designed: cite the design decision or spec that pins the behavior. M can overrule.

## Per-item flow — IDEA / SKILL

1. **Trigger-collision check:** would the imagined trigger phrases route to an existing skill? Grep skill frontmatter descriptions across the plugin — routing runs on descriptions only.
2. **Overlap check:** ≥80% of an existing skill → recommend "extend X", not a new build; say which sections of X change.
3. **Touch-surface inventory:** files/skills/substrate touched; new event types must register in `events.schema.json` + `EVENT_TYPES.md` with a named consumer.
4. **Score `ease`** (1-5) in the frontmatter; ICE = impact × confidence × ease is a sort key for attention, never a verdict.
5. **Verdict:** `SPEC` / `PARK` (real but not now — append a one-paragraph entry to `parking_doc` from the merged profile, default `<intake_root>/PARKING.md`; M's overlay points it at his `FUTURE_WORK.md`; then file to `killed/` with a pointer) / `KILL` (with the honest reason).

## Writing the spec

Templates in `references/spec-templates.md` — two sizes, pick by item, never inflate: **bug-fix spec** ≤1 page, **feature/skill spec** ≤3 pages with a §0 open-decisions table where every genuine fork gets a **recommended default** (flag ambiguity, never silently guess; blocking decisions marked `AWAIT ruling — DO NOT BUILD`).

Specs land in the merged `specs_dir` (default `<intake_root>/specs/`; M's overlay points it at his `build-specs/` folder), named `SPEC_<TAG>_<snake_name>.md` (fresh TAG — check for collisions). **Delivery is `may_ship`-gated:** when the merged profile has `may_ship: true` (M), the spec lands directly in `specs_dir` (his build-specs queue) ready to build; when `may_ship: false` (contractor), attach the spec to the related cr1 PR or hand it over in your normal channel — contractors never self-approve a spec into a build. Then rewrite the intake file to a pointer ("superseded by SPEC_XXX — <date>") and move it to `speced/`.

Spec hygiene: reference files by path, never inline code the builder can read; a section that restates what any Claude already knows gets cut.

## Closing the batch — the decision table

End with ONE screen:

| Item | Type | Verdict | ICE / Sev | Recommendation | Open decisions |
|---|---|---|---|---|---|

Apply rulings: move files (`new/` → `speced/` / `needs-input/` / `killed/`), append rulings into the files. Unruled items stay in `new/` untouched — never assume.

## Writer contract

- Moves files OUT of `new/` (single-writer rule: capture writes `new/`, triage owns everything downstream). Never writes into `new/`.
- `done/` moves happen when the fix/feature ships, not during triage.
- No substrate events, no version/CHANGELOG bumps, no commits/pushes unless asked. Ship/promote stays with M (`may_ship` in operator.json).
