---
name: cr-skill-builder
description: "Build new Command Room skills with the full CR contract layer enforced from the start — substrate I/O contracts, event types in schema enum, atomic-write helpers, ENTITY_RESOLVE gates for name-bearing triggers, privacy compliance (no real names + no operator-pattern leakage), friendly voice tone, first-run questionnaire, release manifest + changelog entries, runtime test stubs, Voice Calibration scoring for composer skills, eval benchmarks, cross-skill collision detection, and bug-regression checks. The quality gate for every skill that ships to a paying Command Room client. Composes with `chalette:skill-creator` for scaffolding + evals, `chalette:voice-test` for voice scoring, `chalette:synthetic-workspace-runtime-test` for runtime exercise, `chalette:bug-regression-suite` for no-regression checks, and `chalette:ship-cr-plugin` for the release flow. Use when M says 'new CR skill', 'new command room skill', 'scaffold a CR skill', 'add skill to command room', 'create a Command Room skill', 'build a CR skill', 'CR skill for [outcome]', 'add a command room skill for [purpose]'. Also runs in AUDIT mode — point it at a SKILL.md path or spec doc and it runs all 20 contract gates against the draft. Audit-mode triggers: 'audit CR skill', 'audit my skill draft for [name]', 'check contract gates for [skill]', 'gate-check this skill', 'contract audit for [skill]', 'run skill validator on [path]'. DOES NOT fire on generic 'create a skill' without Command Room scope — that's `chalette:skill-creator`. DOES NOT fire on trivial edits to an existing skill (typo, single-line fix) — direct edit is fine; this skill is for new skills or significant rewrites. DOES NOT fire on 'create a project skill' or 'generate a skill for [client]' — that's `chalette:skill-generator` for project-scoped 'go [project]' skills. DOES NOT fire on 'regenerate my skill' — that's `chalette:regenerate-skill`."
---

## Recommended Model

**Default: Opus.** Designing a skill — triggers, scope, contract gates, substrate I/O design, Voice Calibration tuning — is where Opus pays back the cost many times over. One good skill spec is read by Claude hundreds of times across paying-client workspaces.

**Switch to Sonnet for:** Mode 1 audit runs against an already-detailed draft where the design is settled and the agent's role is mechanical contract verification (running the 20 static + delegated gates).

---

## Skill Boundary (v2.1)

- **Use cr-skill-builder for:** scaffolding a NEW Command Room plugin skill (Mode 2) OR auditing an existing CR skill draft / spec doc against the 20-rule contract (Mode 1). The quality gate for any SKILL.md that ships to a paying CR client.
- **Use `chalette:skill-creator` for:** generic skill creation outside Command Room scope, OR for the eval / packaging phases of a CR skill (this skill delegates there for Gates 15-16).
- **Use `chalette:skill-generator` for:** project-scoped client skills ("go [project]") that live in `_hq/skills/<project>/`, not in the Command Room plugin.
- **Use `chalette:regenerate-skill` for:** refreshing an existing project-scoped skill when its template or context changed.
- **Use direct edit** for: trivial changes to an existing skill (typo, small text fix, single-line clarification). The contract gates don't help here and waste time.
- **Use `chalette:voice-test` for:** standalone voice scoring outside a skill-build context.
- **Use `chalette:synthetic-workspace-runtime-test` for:** running runtime exercise against synthetic fixture once the SKILL.md is drafted (Gate 17 invocation).
- **Use `chalette:bug-regression-suite` for:** regression checks against M's workspace or synthetic fixture (Gate 18 invocation).
- **Use `chalette:ship-cr-plugin` for:** the actual release flow once the ship-package is reviewed and ready.

## Writer Contract

This skill is a META-skill: it does NOT write to the CR substrate (`events.jsonl`, `entities.json`). It writes to:

- **Workspace drafts:** `Desktop/Claude/Command Room/Command Room/SKILL_PACKAGE_<name>_<date>.md` (Mode 2 output) or `AUDIT_<name>_<date>.md` (Mode 1 output).
- **Plugin source (only on explicit M-approval at end of Phase 5):**
  - `command-room/skills/<...>/SKILL.md` (CR-internal skills go in CR plugin staging at `~/.claude/plugins/marketplaces/commandroom1/command-room/`)
  - `command-room/tests/runtime_exercise_<name>.py`
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
- Does NOT replace `chalette:skill-creator`. Composes with it.
- Does NOT design the SKILL.md from a vague brief. If Phase 1 intent capture doesn't produce a clear outcome + 5+ trigger phrases + 2+ negative triggers, the skill STOPS and pushes back for clarification. Vague briefs produce vague skills.
- Does NOT run evals itself. Defers to `chalette:skill-creator`'s Executor/Grader for Gate 15.
- Does NOT run voice scoring itself. Defers to `chalette:voice-test` for composer-skill Voice Calibration (Gate 14).
- Does NOT run regression itself. Defers to `chalette:bug-regression-suite` for the no-regression check (Gate 18).
- Does NOT run runtime exercise itself. Defers to `chalette:synthetic-workspace-runtime-test` (Gate 17).
- Does NOT generate fake names / synthetic data outside the canonical placeholder set (`Sam Sample`, `Bo Sample`, `Rio Sample`, `Acme Co`, `Northstar Partners`, `Category Company`, `@example.com`). Privacy Rule 26 hard-gate.
- Does NOT skip Voice Calibration for composer skills. Any skill detected as a composer (drafts emails / writes memos / composes replies) MUST score ≥85 on `chalette:voice-test`. No override below 70; 70-85 requires explicit M-acceptance with reason logged.
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

I'll walk you through 6 phases:

| Phase | What | Time |
|---|---|---|
| 1 | Intent capture | ≤3 min |
| 2 | Substrate contract design | ≤5 min |
| 3 | First-run questionnaire (if applicable) | ≤3 min |
| 4 | Auto-gates (20-gate suite, Tier A static + Tier B delegated) | ≤2-15 min |
| 5 | Render ship-package | ≤1 min |
| 6 | Defer to existing tooling (eval, runtime, ship) | as needed |

Total: ~45 min per skill including all gates. Plan on a 45-60 min session per skill build.

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

I run all 20 gates and write a findings doc with PASS / WARN / BLOCK per gate + specific fix templates for each BLOCK.

Verdict at the top of the findings doc: **SHIP / FIX-AND-SHIP / REWRITE**.

## How It Works

### Phase 1 — Intent capture (Mode 2)

Four questions, asked in plain language:

1. **What outcome does the CEO get from this skill?** One sentence, lead with the win. "Rank customers GREEN/YELLOW/RED so I can chase the right ones" — NOT "A tool that analyzes customer data."
2. **What does the CEO actually SAY to trigger it?** List 5-10 natural-language phrases. If you give me 3-4, I suggest variants.
3. **What's CLOSE to this but NOT this?** So we can write the negative triggers. Without these, the skill cannibalizes neighbors.
4. **Is this universal for CEOs/owners or specialized?** Per `references/cr-contract-checklist.md` Gate 20 + Command Room positioning — universal goes in CR plugin; specialized goes elsewhere.

If any answer is vague, I push back. Vague briefs = vague skills.

### Phase 2 — Substrate contract design

I read `references/cr-event-type-registry.md` to see what already exists, then ask:

1. **What events does it READ?** (existing event types from the registry, filtered how, sourced from which skills' writes)
2. **What NEW events does it WRITE?** (must add to `events.schema.json` enum — I generate the diff)
3. **What's the shape of each new event?** (data fields)
4. **Which existing or new skills will CONSUME these new events?** (BLOCK gate per Gate 2 — if no consumer, we either don't ship the event type OR we update an existing skill to consume it in the same release)
5. **Does this skill need a new substrate file?** (e.g., `_hq/data/<name>.json`) — if yes, I generate the schema + writer helper stub
6. **Which connectors does it touch?** (Gmail, Calendar, Slack, Granola, QuickBooks, DocuSign, Canva — defines `Writer Contract` references)
7. **Name-bearing triggers?** (if yes, auto-add `ENTITY_RESOLVE_PROTOCOL` MUST-language gate to the SKILL.md)

### Phase 3 — First-run questionnaire (skip if behavior doesn't vary)

I ask: **Does the skill's behavior vary by operator?**

If YES → I help draft 3-5 questions. Cap at 5 per `references/cr-first-run-template.md`. For each question, I propose a substrate-aware default (read from entities.json / events.jsonl).

I sanity-check: questions whose answers are already in the substrate get DROPPED. Don't ask the user what's in the file already.

The config goes to `_hq/data/skill_config/<skill-name>.json`. Pattern is per `references/cr-first-run-template.md`.

If NO first-run config needed → skip this phase. Not every skill needs it.

### Phase 4 — Auto-gates (the 20-gate client-quality suite)

Run all 20 gates from `references/cr-contract-checklist.md` in three tiers:

**Tier A — Static gates (run in-builder, fast):** Gates 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 19, 20.

**Tier B — Runtime + eval gates (delegated to chalette tooling):**
- Gate 13 — runtime stub generated + `chalette:synthetic-workspace-runtime-test` PASS
- Gate 14 — `chalette:voice-test` ≥85 (composer skills only)
- Gate 15 — `chalette:skill-creator` Executor+Grader ≥90% pass rate
- Gate 16 — `chalette:skill-creator` description-improver ≥0.85
- Gate 17 — same as Gate 13 (consolidated runtime check)
- Gate 18 — `chalette:bug-regression-suite` PASS verdict after staging-drop

**Tier C — Ship-time gates (deferred to `chalette:ship-cr-plugin` Step 5.5+6):** Gates 11, 12.

For each gate: PASS / WARN / BLOCK with specific fix template. Tier A runs first; if anything BLOCKs, halt before invoking Tier B (no point burning eval cycles on a SKILL.md that fails name-scan).

Sample summary at end of Phase 4:

```
Phase 4 GATE SUMMARY (20-gate client-quality suite)
===================================================
TIER A — Static (in-builder)
  ✅ PASS  Gate 1  — Event types in enum
  ✅ PASS  Gate 2  — Consumer skills wired
  ✅ PASS  Gate 3  — Atomic helpers used
  ⚠️ WARN  Gate 4  — Name-bearing trigger; auto-added ENTITY_RESOLVE gate
  ✅ PASS  Gate 5  — $WORKSPACE resolved at runtime
  ✅ PASS  Gate 6  — No real customer names (Sample placeholders only)
  ✅ PASS  Gate 7  — Widget format declared
  ✅ PASS  Gate 8  — H2 deliverable links
  ✅ PASS  Gate 9  — Leak scanner clean
  ✅ PASS  Gate 10 — First-run questionnaire ≤5
  ✅ PASS  Gate 19 — Privacy second-pass
  ✅ PASS  Gate 20 — No cross-skill collisions

TIER B — Runtime + Eval (delegated)
  ✅ PASS  Gate 13 — synthetic-workspace-runtime-test PASS
  ✅ PASS  Gate 14 — Voice Calibration 91/100 (composer)
  ✅ PASS  Gate 15 — Eval pass rate 9/10 prompts
  ✅ PASS  Gate 16 — Description triggering 0.91
  ✅ PASS  Gate 17 — (consolidated with Gate 13)
  ✅ PASS  Gate 18 — bug-regression-suite PASS

TIER C — Ship-time (deferred)
  ℹ️ INFO  Gate 11 — RELEASE_MANIFEST entry generated, awaiting ship
  ℹ️ INFO  Gate 12 — CHANGELOG entry generated, awaiting ship

Verdict: PROCEED to Phase 5.
Client-quality readiness: 18/20 clear, 2 deferred to ship-time.
```

### Phase 5 — Render ship-package

I render:

1. **SKILL.md** — full, matching `references/cr-skill-template.md` (which inherits SKILL_SHAPE_V2)
2. **Test stub** at `tests/runtime_exercise_<name>.py` — happy path + edge cases for every Phase 4 gate
3. **Schema diff** — unified diff against `shared/data-schemas/events.schema.json` for new event types
4. **New substrate schema** (if applicable) at `shared/data-schemas/<name>.schema.json`
5. **Writer helper stub** at `shared/scripts/<name>_writer.py` using atomic helpers
6. **RELEASE_MANIFEST.md entry**: skill name + version + dependencies
7. **CHANGELOG.md stub**: `### Added\n- <skill>: <outcome>`
8. **Consumer-update notes**: markdown checklist of existing skills that need touch
9. **Eval prompts file** at `tests/eval_prompts_<name>.json` (3-10 prompts + assertions for Gate 15)
10. **Voice samples** (if composer skill) — 3 sample drafts for Gate 14 scoring
11. **skill_config template** (if first-run questionnaire defined) at `_hq/data/skill_config/<name>.json.template`
12. **Single output file** at `Desktop/Claude/Command Room/Command Room/SKILL_PACKAGE_<name>_<date>.md` containing all the above + a "drop these into the plugin" checklist M can walk

### Phase 6 — Defer to existing tooling

I surface clickable links to:

- `chalette:skill-creator` → run additional evals against test prompts
- `chalette:synthetic-workspace-runtime-test` → runtime exercise against fixture
- `chalette:verify-cr-release` → M-attended Cowork verification (for the release containing this skill)
- `chalette:bug-regression-suite` → regression check against M's workspace post-drop
- `chalette:ship-cr-plugin` → staging push when ready

I do NOT invoke these directly. M decides when each fires.

### Mode 1 audit — single-phase

If triggered with audit phrasing, skip Phases 1-3 and 5. Just run Phase 4 (gates) against the input.

Input formats:
- Path to SKILL.md
- Path to a spec doc (parses each `### N. <skill>` section as a separate audit subject)
- Pasted markdown (last resort)

Output: `Desktop/Claude/Command Room/Command Room/AUDIT_<skill-name>_<date>.md` with verdict (SHIP / FIX-AND-SHIP / REWRITE) at the top + per-gate findings.

## References (what this skill reads at runtime)

- `references/cr-contract-checklist.md` — the 20-gate definitions + verification logic + fix templates
- `references/cr-skill-template.md` — boilerplate SKILL.md to render from (inherits SKILL_SHAPE_V2)
- `references/cr-event-type-registry.md` — every existing event type + writer + consumer + last touched (regenerated at runtime)
- `references/cr-first-run-template.md` — questionnaire convention (≤5 questions, substrate-aware defaults, skill_config storage)
- `references/cr-substrate-helpers.md` — canonical writers + when to use which + quality-gate delegated tooling hooks

## Versioning

This skill's references are SYNCED with the CR plugin version. Each reference doc carries a `cr_plugin_version_min` frontmatter key. If running against a CR plugin newer than the references know about, Phase 4 surfaces a warning: "Contract checklist last synced for v<X.Y.Z>; CR plugin is at v<A.B.C> — review for new contract rules."

Update cadence: every CR plugin release that adds or changes a contract rule MUST update the references in the same ship cycle.
