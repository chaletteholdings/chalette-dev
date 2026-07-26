---
name: cr-skill-builder
description: "Build or audit a Command Room plugin skill with the full CR contract layer enforced. ALWAYS use when M says new CR skill, new command room skill, scaffold a CR skill, build a CR skill, add a command room skill, or CR skill for [outcome] — or to audit an existing draft: audit CR skill, gate-check this skill, contract audit for [skill], check contract gates, run skill validator on [path]. Do not scaffold a customer-bound CR skill with generic tooling — use this skill. DOES NOT fire on create a skill with no Command Room scope — that's skill-creator. DOES NOT fire on generate a skill for [project] or a go-[project] skill — that's skill-generator. DOES NOT fire on regenerate [project] skill — that's regenerate-skill. DOES NOT fire on a trivial one-line edit to an existing skill — edit it directly."
metadata:
  version: 3.0.0
  sync_note: "cr-skill-builder v3.0.0 (SB1, 2026-07-23) — synced across chalette030 + chalette-dev; contracts derived live from cr1 (v5.2.0-era), not vendored."
---

## Recommended Model

**Default: Opus.** Designing a skill — triggers, scope, contract gates, substrate I/O design, Voice Calibration tuning — is where Opus pays back the cost many times over. One good skill spec is read by Claude hundreds of times across paying-client workspaces.

**Switch to Sonnet for:** Mode 1 audit runs against an already-detailed draft where the design is settled and the agent's role is mechanical contract verification (running the 27 static + delegated gates + the live guard tier).

---

## Skill Boundary (v3)

- **Use cr-skill-builder for:** scaffolding a NEW Command Room plugin skill (Mode 2) OR auditing an existing CR skill draft / spec doc against the 27-gate contract (Mode 1). The quality gate for any SKILL.md that ships to a paying CR client.
- **Use `chalette-dev:skill-creator` for:** generic skill creation outside Command Room scope, OR for the eval / packaging phases of a CR skill (this skill delegates there for Gates 15-16).
- **Use `chalette-dev:skill-generator` for:** project-scoped client skills ("go [project]") that live in `_hq/skills/<project>/`, not in the Command Room plugin.
- **Use `chalette-dev:regenerate-skill` for:** refreshing an existing project-scoped skill when its template or context changed.
- **Use direct edit** for: trivial changes to an existing skill (typo, small text fix, single-line clarification). The contract gates don't help here and waste time.
- **Use `chalette-dev:voice-test` for:** standalone voice scoring outside a skill-build context.
- **Use `chalette-dev:synthetic-workspace-runtime-test` for:** running runtime exercise against synthetic fixture once the SKILL.md is drafted (Gate 13 invocation).
- **Use `chalette-dev:bug-regression-suite` for:** regression checks against the resolved workspace or synthetic fixture (Gate 18 invocation).
- **Use `chalette:ship-cr-plugin` for:** the actual release flow once the ship-package is reviewed and ready.

## Live derivation — contracts are read, not vendored (v3 / D1)

This skill no longer trusts a vendored snapshot of cr1's contracts. The "sync references every release" rule failed empirically (the old `cr-event-type-registry.md` sat 10+ releases stale before it was deleted). Instead, the event enum, the guard registry, and the canonical verb set are **read live** from the cr1 clone at runtime. Resolve the clone path **once**, parameterized so Eric's fork works too:

```python
# Parameterized cr1 clone path — M defaults to the canonical edit surface; a contractor's fork
# is read from the merged operator profile (config/operator.json, then config/operator.local.json
# overlaid per-key; the overlay is gitignored and only M has one). Never hardcode a machine path.
import json, os, sys
op = {}
for _n in ("operator.json", "operator.local.json"):
    _p = os.path.join(SKILL_PLUGIN_ROOT, "config", _n)
    if os.path.exists(_p): op.update(json.load(open(_p)))
# SKILL_PLUGIN_ROOT must be a NATIVE path — on Windows `C:/Users/…`, never an MSYS
# `/c/Users/…` (convert with `cygpath -m`): python.exe reads `/c/…` as `C:\c\…`, both
# files miss, and an empty profile silently becomes the default. Fail loud instead.
if not op: sys.exit(f"FATAL: operator profile unreadable under {SKILL_PLUGIN_ROOT}")
cr1_clone = op.get("cr1_clone") or "~/repos/cr1-canonical"   # M-only default
CR = os.path.join(os.path.expanduser(cr1_clone), "command-room")
```

Pull the clone first (`git -C "$(dirname "$CR")" pull --ff-only`, per the canonical-edit-surface rule). The live contracts and the gates that read them are tabled in `references/cr-contract-checklist.md` under "Live source resolution".

## Writer Contract

This skill is a META-skill: it does NOT write to the CR substrate (`events.jsonl`, `entities.json`). Resolve the **output dir** once from the merged operator profile: `workspace_root` if set (M writes into his `Command Room/` workspace via his overlay); otherwise a scratch dir adjacent to the resolved `cr1_clone` (e.g. `<cr1_clone>/../cr-skill-drafts/`) so a contractor operator has a real, non-hardcoded home. It writes to:

- **Workspace drafts:** `<output_dir>/SKILL_PACKAGE_<name>_<date>.md` (Mode 2 output) or `<output_dir>/AUDIT_<name>_<date>.md` (Mode 1 output).
- **Plugin source (only on explicit M-approval at end of Phase 5):**
  - `command-room/skills/<...>/SKILL.md` (CR-internal skills go in the canonical edit surface resolved above; the marketplace clone is a read-only install cache)
  - `command-room/tests/runtime_exercise_<name>.py`
  - `command-room/tests/eval_triggers_<name>.json` (the Gate 16 labeled query set)
  - `command-room/shared/data-schemas/events.schema.json` (enum additions only — patch-merge, never rewrite)
  - `command-room/shared/data-schemas/<name>.schema.json` (if new substrate file)
  - `command-room/shared/scripts/<name>_writer.py` (if needed; uses atomic helpers)
  - `command-room/references/RELEASE_MANIFEST.md`
  - `command-room/CHANGELOG.md`

**Atomic-write enforcement:** all file writes use the standard atomic-write helpers. No raw `open(path, "w").write()` anywhere in this skill's own code or in code it generates — eat the dogfood.

**Never auto-commits, never auto-pushes.** Outputs land in workspace OR in plugin staging working tree; M reviews and runs `chalette:ship-cr-plugin` when ready.

## What It Doesn't Do

- Does NOT auto-commit. Output is a draft ship-package; M reviews + commits manually (or via `chalette:ship-cr-plugin`).
- Does NOT auto-ship to production. v3.13.8 architectural review confirmed: production-promote needs human verification gates.
- Does NOT replace `chalette-dev:skill-creator`. Composes with it.
- Does NOT design the SKILL.md from a vague brief. If Phase 1 intent capture doesn't produce a clear outcome + 5+ trigger phrases + 2+ negative triggers, the skill STOPS and pushes back for clarification. Vague briefs produce vague skills.
- Does NOT run evals itself. Defers to `chalette-dev:skill-creator`'s Executor/Grader for Gates 15-16.
- Does NOT run voice scoring itself. Defers to `chalette-dev:voice-test` for composer-skill Voice Calibration (Gate 14).
- Does NOT run regression itself. Defers to `chalette-dev:bug-regression-suite` for the no-regression check (Gate 18).
- Does NOT run runtime exercise itself. Defers to `chalette-dev:synthetic-workspace-runtime-test` (Gate 13).
- Does NOT generate fake names / synthetic data outside the canonical placeholder set (`Sam Sample`, `Bo Sample`, `Rio Sample`, `Acme Co`, `Northstar Partners`, `Category Company`, `@example.com`). Privacy Gate 6 hard-gate.
- Does NOT skip Voice Calibration for composer skills. Any skill detected as a composer (drafts emails / writes memos / composes replies) MUST score ≥85 on `chalette-dev:voice-test`. No override below 70; 70-85 requires explicit M-acceptance with reason logged.
- Does NOT mark a skill ship-ready until ALL Tier A static gates clear AND ALL Tier B runtime/eval gates clear. WARN-status surfaces for explicit accept; BLOCK-status halts.

## How to Use

### Mode 2 — Scaffold a new skill (interactive)

```
"new CR skill for [outcome]"
"new command room skill for [outcome]"
"scaffold a CR skill"
"build a CR skill for [purpose]"
"create a Command Room skill for [thing]"
"add a command room skill for [purpose]"
```

I walk 7 phases:

| Phase | What | Time |
|---|---|---|
| 0 | Sync check (reference versions vs live cr1 plugin.json) | ≤1 min |
| 1 | Intent capture | ≤3 min |
| 1.5 | RED baseline — watch Claude do the task WITHOUT the skill | ≤3 min |
| 2 | Substrate contract design (live enum + registry read) | ≤5 min |
| 3 | First-run questionnaire (if applicable) | ≤3 min |
| 4 | Auto-gates (27-gate suite, TodoWrite-tracked) | ≤2-15 min |
| 5 | Render ship-package | ≤1 min |
| 6 | Defer to existing tooling (eval, runtime, ship) | as needed |

Total: ~45-60 min per skill including all gates.

### Mode 1 — Audit existing draft

```
"audit CR skill [path]"
"audit my skill draft for [name]"
"check contract gates for [skill]"
"gate-check [skill]"
"contract audit for [skill]"
"run skill validator on [path]"
```

Point me at:
- A SKILL.md path, OR
- A spec doc (like a NEXT_SKILL_BATCH_SPECS doc) — I parse each `### N. <skill>` section as a separate audit subject, OR
- Pasted markdown (last resort; ask M to save to a file if longer than ~500 lines)

I run all 27 gates and write a findings doc with PASS / WARN / BLOCK per gate + specific fix templates for each BLOCK.

**AUDIT-mode exit — the live guard tier (v3 / D1):** after the 27 gates, before emitting the verdict, run cr1's ship-gate guard tier and fold its result into the findings doc. **No guard IDs are hardcoded here** — the registry moves (it was G1–G10, then G1–G16, and it will move again). Run the tier, then read the live registry and map each RED guard to a finding:

```bash
# Canonical edit surface resolved per "Live derivation" above (marketplace clone is read-only)
cd "$CR" && PYTHONUTF8=1 python tests/run_all.py --tier guard
# then read the live registry to name each guard and map reds to findings:
#   $CR/tests/GUARDS.md
```

For each RED guard: read its row in `tests/GUARDS.md`, name what it enforces, and map it to the corresponding contract gate (the checklist's gate bodies cite their live-guard mirror — e.g. Gate 7↔G4, Gate 9↔G5, Gate 17↔G13, Gate 26↔G11/G15, Gate 27↔G14). A red guard is a BLOCK in the findings doc regardless of the 27-gate result. G10 (and any other process-only guard) is reviewer discipline, not code — assert it by hand when the audited skill changed a core model.

Verdict at the top of the findings doc: **SHIP / FIX-AND-SHIP / REWRITE**.

## How It Works

### Phase 0 — Sync check (both modes)

Before auditing against any contract, compare each reference doc's `cr_plugin_version_min` frontmatter against the **live** cr1 `plugin.json` version (read from `$CR/.claude-plugin/plugin.json`). If any reference is behind, surface a WARN banner:

```
⚠️  Contract drift: references/<file> synced for v<X.Y.Z>; cr1 is at v<A.B.C>.
    Review the gates that read live contracts (enum, guards, verbs) before trusting a PASS.
```

This is the guardrail that replaces silent auditing against stale snapshots. It does not block — it tells you which gates to double-check. (Deleting this check is a real regression: a stale reference would then be audited against as if current, and a staleness scenario goes undetected — see the build record's mutation-fence note.)

### Phase 1 — Intent capture (Mode 2)

Four questions, asked in plain language:

1. **What outcome does the CEO get from this skill?** One sentence, lead with the win. "Rank customers GREEN/YELLOW/RED so I can chase the right ones" — NOT "A tool that analyzes customer data."
2. **What does the CEO actually SAY to trigger it?** List 5-10 natural-language phrases. If you give me 3-4, I suggest variants.
3. **What's CLOSE to this but NOT this?** So we can write the negative triggers AND source the eval near-misses (Gate 16). Without these, the skill cannibalizes neighbors.
4. **Is this universal for CEOs/owners or specialized?** Per `references/cr-contract-checklist.md` Gate 20 + Command Room positioning — universal goes in CR plugin; specialized goes elsewhere.

If any answer is vague, I push back. Vague briefs = vague skills.

### Phase 1.5 — RED baseline (Mode 2, WI-6 / D-research finding 5)

Before drafting anything, run the top trigger phrase against a fresh context WITHOUT the skill (one subagent) and capture what Claude does today — the exact output shape, the steps it skips, the rationalizations it produces. The draft must then NAME what it changes about that baseline. Cheap (one subagent), and it kills "vague brief → vague skill" earlier than the Phase 1 push-back alone.

Two direct uses of the capture:
- It tells you the **failure type** (wrong shape / omitted element / rule-violation-under-pressure / conditional), which the body-audit heuristic maps to the right guidance form (checklist "Body-quality heuristics").
- For a discipline skill, the rationalizations it produced seed the **rationalization table** slot in the template — you write the skill against the excuses the agent actually made, not imagined ones.

### Phase 2 — Substrate contract design (live read)

Read the **live** enum + registry from `$CR` (see "Live derivation") — never a vendored copy:
- `shared/data-schemas/events.schema.json` — the canonical event enum (228+ types).
- `shared/EVENT_TYPES.md` — writer + named-consumer rows.

Then ask:

1. **What events does it READ?** (existing event types from the live enum, filtered how, sourced from which skills' writes)
2. **What NEW events does it WRITE?** (must be registered in BOTH `events.schema.json` enum AND `shared/EVENT_TYPES.md` — I generate both diffs; Gate 1. Prefer `append_event()` (intent-revealing); a direct `atomic_append_jsonl` on the events path is also gated — Gate 3.)
3. **What's the shape of each new event?** (data fields)
4. **Which existing or new skills will CONSUME these new events?** (BLOCK gate per Gate 2 — the consumer must be NAMED in the `EVENT_TYPES.md` row; if no consumer, we either don't ship the event type OR we update an existing skill to consume it in the same release)
5. **Does it touch COMMITMENTS?** (if yes: every `commitment` write carries `data.kind ∈ {promise, task, scheduling, agenda}`, closures go only through `close_commitment()`, and any surfaced count comes from `commitment_counts()` — Gates 21 + 22)
6. **Does it DERIVE activity/recency from events?** (if yes: derive through `org_activity.py::derive_from_events(..., honor_reclassifications=True)`, never a hand scan — the RECL1 reader-derivation rule, Gate 21-area)
7. **Does it run on a SCHEDULE?** (if yes: it registers via the `SILENT_TASKS` registry, not a bespoke block, and declares a watchdog receipt event it writes each fire — Gate 23)
8. **Does it LEARN anything per-customer?** (feedback, priorities, tuned thresholds → workspace-side only, never plugin source — Gate 24)
9. **Does this skill need a new substrate file?** (e.g., `_hq/data/<name>.json`) — if yes, I generate the schema + writer helper stub
10. **Which connectors does it touch?** (Superhuman, Calendar, Slack, Granola, QuickBooks, DocuSign, Canva — defines `Writer Contract` references)
11. **Name-bearing triggers?** (if yes, auto-add `ENTITY_RESOLVE_PROTOCOL` MUST-language gate to the SKILL.md — Gate 4)
12. **Does it introduce a new shared-code path?** (if yes: at least one skill text MUST name the helper — Gate 17 instruction-layer)
13. **Is it a COMPOSER?** (drafts customer-facing text → offer the SCL1 §6.2 customization paragraph so a workspace directive can tune it without a fork — Gate 25)

### Phase 3 — First-run questionnaire (skip if behavior doesn't vary)

I ask: **Does the skill's behavior vary by operator?**

If YES → I help draft 3-5 questions. Cap at 5 per `references/cr-first-run-template.md`. For each question, I propose a substrate-aware default (read from entities.json / events.jsonl), and I enforce the "show, then tune" UX (produce output immediately with defaults; never block first output behind the questionnaire).

I sanity-check: questions whose answers are already in the substrate get DROPPED. Don't ask the user what's in the file already.

The config goes to `_hq/data/skill_config/<skill-name>.json`. Pattern is per `references/cr-first-run-template.md`.

If NO first-run config needed → skip this phase. Not every skill needs it.

### Phase 4 — Auto-gates (the 27-gate client-quality suite, TodoWrite-tracked)

**Step 0 (do this before running any gate):** create a TodoWrite checklist of all 27 gates. Mark a gate complete ONLY after its verdict exists. This is the same anti-silent-skip discipline the builder scaffolds into generated skills (WI-5 / D4) — a gate that isn't in the list can't be silently skipped, and Phase 4 runs 27 of them, the exact silent-skip risk the fix targets. (Removing this Step-0 checklist is a real regression: with 27 gates and no visible list, a gate gets dropped without notice — see the build record's mutation-fence note.)

Run all 27 gates from `references/cr-contract-checklist.md` in three tiers:

**Tier A — Static gates (run in-builder, fast):** Gates 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27.

**Tier B — Runtime + eval gates (delegated to chalette tooling):**
- Gate 13 — runtime stub generated + `chalette-dev:synthetic-workspace-runtime-test` PASS (absorbs the former Gate 17 runtime duplicate)
- Gate 14 — `chalette-dev:voice-test` ≥85 (composer skills only)
- Gate 15 — `chalette-dev:skill-creator` Executor+Grader ≥90% pass rate
- Gate 16 — measured trigger eval (see below) via `chalette-dev:skill-creator`; validation ≥0.85
- Gate 18 — `chalette-dev:bug-regression-suite` PASS verdict after staging-drop

**Tier C — Ship-time gates (deferred to `chalette:ship-cr-plugin`):** Gates 11, 12.

For each gate: PASS / WARN / BLOCK with specific fix template. Tier A runs first; if anything BLOCKs, halt before invoking Tier B (no point burning eval cycles on a SKILL.md that fails name-scan).

Sample summary at end of Phase 4:

```
Phase 4 GATE SUMMARY (27-gate client-quality suite)
===================================================
TIER A — Static (in-builder)
  ✅ PASS  Gate 1  — Event types in enum + EVENT_TYPES.md (live read)
  ✅ PASS  Gate 2  — Named consumer wired
  ✅ PASS  Gate 3  — append_event() / atomic helpers (no hand-rolled writes)
  ⚠️ WARN  Gate 4  — Name-bearing trigger; auto-added ENTITY_RESOLVE gate
  ✅ PASS  Gate 5  — $WORKSPACE resolved at runtime
  ✅ PASS  Gate 6  — No real customer names (Sample placeholders only)
  ✅ PASS  Gate 7  — Widget format + live canonical verb set (G4)
  ✅ PASS  Gate 8  — H2 deliverable links
  ✅ PASS  Gate 9  — Leak scanner + G5 banned-word list clean
  ✅ PASS  Gate 10 — First-run questionnaire ≤5
  ✅ PASS  Gate 17 — Instruction-layer wiring (helper named in body) (G13)
  ✅ PASS  Gate 19 — Privacy second-pass
  ✅ PASS  Gate 20 — No cross-skill collisions (live enum)
  ✅ PASS  Gate 21 — Commitments carry data.kind; close via close_commitment(); RECL1 derive
  ✅ PASS  Gate 22 — Counts from commitment_counts()
  ➖ SKIP  Gate 23 — Not a scheduled task
  ✅ PASS  Gate 24 — Learned state workspace-side only
  ⚠️ WARN  Gate 25 — Composer; SCL1 §6.2 paragraph offered
  ✅ PASS  Gate 26 — Description budget ≤980, stem in first 250, catalog headroom OK (G11)
  ✅ PASS  Gate 27 — Generated-test dates computed, off cron boundaries (G14)

TIER B — Runtime + Eval (delegated)
  ✅ PASS  Gate 13 — synthetic-workspace-runtime-test PASS
  ✅ PASS  Gate 14 — Voice Calibration 91/100 (composer)
  ✅ PASS  Gate 15 — Eval pass rate 9/10 prompts
  ✅ PASS  Gate 16 — Trigger eval: validation 0.90, fresh-query 0.88
  ✅ PASS  Gate 18 — bug-regression-suite PASS

TIER C — Ship-time (deferred)
  ℹ️ INFO  Gate 11 — RELEASE_MANIFEST entry generated, awaiting ship
  ℹ️ INFO  Gate 12 — CHANGELOG entry generated, awaiting ship

Verdict: PROCEED to Phase 5.
Client-quality readiness: 23/27 clear, 1 skipped (n/a), 2 WARN accepted, 2 deferred to ship-time.
```

### Phase 5 — Render ship-package

I render:

1. **SKILL.md** — full, matching `references/cr-skill-template.md` (which inherits SKILL_SHAPE_V2 and carries the v3 description doctrine + Step-0 / rationalization-table conditional blocks)
2. **Test stub** at `tests/runtime_exercise_<name>.py` — happy path + edge cases for every Phase 4 gate; dates computed relative + off cron boundaries (Gate 27)
3. **Trigger eval set** at `tests/eval_triggers_<name>.json` — 8-10 should-fire + 8-10 near-miss negatives sourced from neighbor trigger tables, 60/40 train/validation split (Gate 16)
4. **Schema diff** — unified diff against `shared/data-schemas/events.schema.json` for new event types
5. **New substrate schema** (if applicable) at `shared/data-schemas/<name>.schema.json`
6. **Writer helper stub** at `shared/scripts/<name>_writer.py` using atomic helpers
7. **RELEASE_MANIFEST.md entry**: skill name + version + dependencies
8. **CHANGELOG.md stub**: `### Added\n- <skill>: <outcome>`
9. **Consumer-update notes**: markdown checklist of existing skills that need touch
10. **Eval prompts file** at `tests/eval_prompts_<name>.json` (3-10 prompts + assertions for Gate 15)
11. **Voice samples** (if composer skill) — 3 sample drafts for Gate 14 scoring
12. **skill_config template** (if first-run questionnaire defined) at `_hq/data/skill_config/<name>.json.template`
13. **Single output file** at `<output_dir>/SKILL_PACKAGE_<name>_<date>.md` (output_dir resolved per the Writer Contract) containing all the above + a "drop these into the plugin" checklist the operator can walk

### Phase 6 — Defer to existing tooling

I surface clickable links to:

- `chalette-dev:skill-creator` → run the trigger eval + additional evals against test prompts
- `chalette-dev:synthetic-workspace-runtime-test` → runtime exercise against fixture
- `chalette-dev:cr-test --attended` → the attended tier for the release containing this skill: dogfood + `cr-test/references/VERIFICATION_PLAN.md`, walked by hand (this replaced the retired `verify-cr-release`)
- `chalette-dev:bug-regression-suite` → regression check against the resolved workspace post-drop
- `chalette:ship-cr-plugin` → staging push when ready

I do NOT invoke these directly. M decides when each fires.

### Mode 1 audit — single-phase

If triggered with audit phrasing, skip Phases 1, 1.5, 3, and 5. Run Phase 0 (sync check), then Phase 4 (the 27 gates, Step-0 TodoWrite-tracked) against the input, THEN the live guard tier from the AUDIT-mode exit above.

Input formats:
- Path to SKILL.md
- Path to a spec doc (parses each `### N. <skill>` section as a separate audit subject)
- Pasted markdown (last resort)

Output: `<output_dir>/AUDIT_<skill-name>_<date>.md` (output_dir resolved per the Writer Contract) with verdict (SHIP / FIX-AND-SHIP / REWRITE) at the top + per-gate findings + the live guard-tier result. A red guard forces at least FIX-AND-SHIP regardless of the 27-gate outcome.

## References (what this skill reads at runtime)

- `references/cr-contract-checklist.md` — the 27-gate definitions + verification logic + fix templates + the promoted build-relevant gotchas + body-quality heuristics
- `references/cr-skill-template.md` — boilerplate SKILL.md to render from (inherits SKILL_SHAPE_V2; carries the v3 description doctrine + Step-0 / rationalization-table blocks)
- `references/cr-first-run-template.md` — questionnaire convention (≤5 questions, substrate-aware defaults, "show then tune", skill_config storage)
- `references/cr-substrate-helpers.md` — canonical writers + when to use which + quality-gate delegated tooling hooks

Read LIVE from the cr1 clone (`$CR`, resolved per "Live derivation") — never vendored:
- `shared/data-schemas/events.schema.json` — the canonical event enum (Gates 1, 2, 20)
- `shared/EVENT_TYPES.md` — event-type registry + commitment-family append contract (Gates 1, 2, 3, 21, 22)
- `shared/scripts/verb_taxonomy.py` / `chat_output_renderer.py` — canonical action verb set (Gate 7)
- `tests/GUARDS.md` — the live ship-gate guard registry (AUDIT-mode exit; the guard↔gate mirror map)

## Versioning

References carry a `cr_plugin_version_min` frontmatter key. Phase 0 compares each against the live cr1 `plugin.json` and surfaces a WARN banner on drift — the replacement for the old "manually sync every release" rule, which failed in practice. The contracts that move fastest (enum, guards, verbs) are read live, so a stale reference degrades to a warning, not a silent wrong audit.

**Standing rule (D7):** any new gotcha that constrains how skills are BUILT gets promoted into `references/cr-contract-checklist.md` as a named check in the same session it's learned — machine-local memory is invisible to Eric and to fresh installs.
