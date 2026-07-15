---
title: CR Contract Checklist — the 20 Gates
cr_plugin_version_min: 3.13.8.3
last_updated: 2026-05-26
---

# CR Contract Checklist — 20 Gates

Every new Command Room skill MUST pass these gates before SKILL.md ships to a customer-bound release. The gates are the unique value of `cr-skill-builder` vs `chalette:skill-creator` (which only enforces SKILL_SHAPE_V2 frontmatter).

For each gate: **definition** → **how to verify** → **severity** (BLOCK / WARN) → **fix template**.

Tier ordering:
- **Tier A** — static gates, run in-builder, fast (Gates 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 19, 20)
- **Tier B** — runtime + eval gates, delegated to existing chalette tooling (Gates 13, 14, 15, 16, 17, 18)
- **Tier C** — ship-time gates, deferred to `chalette:ship-cr-plugin` (Gates 11, 12)

---

## Gate 1 — Event types in `events.schema.json` enum

**Definition:** Every event type written by the skill MUST exist in the `type` enum in `shared/data-schemas/events.schema.json` BEFORE any writer emits it.

**Severity:** BLOCK (always).

**How to verify:**
1. Parse the SKILL.md for `"type": "<value>"` event-shape examples.
2. Parse the proposed enum diff (if Phase 5 generated one).
3. Read current `events.schema.json` enum.
4. Assert: every event type the skill writes is either already in the enum OR in the proposed diff.

**Fix template:** Add a unified diff to `events.schema.json`:

```diff
    "schedule_created",
+   "<new_event_type>",
    "backfill_chunk_scheduled",
```

The diff lands in the same commit as the skill.

---

## Gate 2 — Each new event type has at least one consumer

**Definition:** For every new event type the skill writes, AT LEAST ONE existing or new skill in the plugin MUST read it. Else: shipped a feature nobody reads.

**Severity:** BLOCK (always).

**How to verify:**
1. For each new event type, grep all skill files for `"type": "<value>"` in read contexts.
2. Skill author must declare in Phase 2: "Consumer for <event_type>: <skill-name>."
3. If the declared consumer is also new (e.g., morning-briefing being updated to read the new event), generate the consumer-update note as part of Phase 5.

**Fix template:** Either:
- Drop the event type if no consumer can be identified, OR
- Declare which existing skill will read it + include the consumer-update note in the same ship.

---

## Gate 3 — All writes go through atomic helpers

**Definition:** No raw `open(path, "a").write(...)`, no `path.write_text(...)` for substrate files. Must use `atomic_append_jsonl` (events.jsonl), `atomic_write_json` (entities.json / aliases.json / okrs.json / one_on_ones.json / skill_config/*.json), or a canonical wrapper (`people_writer.py`, etc.).

**Severity:** BLOCK (always — Bug #81 architectural fix).

**How to verify:**
1. Grep skill content (SKILL.md inline bash blocks, any embedded python) for forbidden patterns:
   - `open(...) ... write(`
   - `path.write_text(`
   - `path.write_bytes(`
   - `json.dump(... file)` (allowed only inside atomic helpers themselves)
2. Assert zero hits in the skill author's code.

**Fix template:** Replace raw write with the atomic helper:

```python
# WRONG
with open(events_path, "a") as f:
    f.write(json.dumps(event) + "\n")

# RIGHT
from atomic_io import atomic_append_jsonl
atomic_append_jsonl(events_path, event)
```

---

## Gate 4 — ENTITY_RESOLVE_PROTOCOL for name-bearing triggers

**Definition:** Any skill whose trigger phrases include name-bearing variants ("[customer]", "[person]", "[client]", "[project]") MUST invoke `shared/scripts/entity_resolve.py::resolve_all(workspace_root, query)` BEFORE any substrate query that depends on the resolved entity.

**Severity:** BLOCK if name-bearing triggers exist; SKIP otherwise.

**How to verify:**
1. Parse trigger phrases for placeholder patterns: `[name]`, `[customer]`, `[client]`, `[person]`, `[project]`, `[org]`.
2. If found, assert SKILL.md contains an `## Entity-resolve + canonical-helper enforcement` section with `resolve_all` call site referenced.
3. Assert the section references `shared/ENTITY_RESOLVE_PROTOCOL.md`.

**Fix template:** Insert near the top of SKILL.md body:

```markdown
## Entity-resolve + canonical-helper enforcement (mandatory, v3.13.8+)

If the skill is invoked with a name-bearing trigger ("[skill] for [name]"), you MUST call `shared/scripts/entity_resolve.py::resolve_all(workspace_root, query)` first to resolve the named scope. See `shared/ENTITY_RESOLVE_PROTOCOL.md` for the full contract.
```

---

## Gate 5 — `$WORKSPACE` resolved at runtime, no literal paths

**Definition:** Any user-facing path in chat output, links, or "saved to..." narration MUST come from runtime-resolved `$WORKSPACE`. Never a literal path copied from a docstring, CHANGELOG entry, or example.

**Severity:** BLOCK.

**How to verify:**
1. Grep skill content for absolute paths that look like author machine paths: `C:\Users\<name>\`, `/Users/<name>/`, `/home/<name>/`.
2. Allowed: placeholders `<workspace-root>`, `$WORKSPACE`, `/path/to/workspace/`.
3. Allowed: paths inside the plugin itself (`shared/scripts/...`, `references/...`).

**Fix template:** Replace literal with placeholder + reference to runtime resolution:

```
# WRONG
"Your brief saved to C:\Users\<someone>\Desktop\Claude\..."

# RIGHT
"Your brief saved to <workspace>\_hq\meetings\..."
where <workspace> = runtime-resolved $WORKSPACE
```

Per CONTRACT.md Rule 25.

---

## Gate 6 — No real customer or partner names

**Definition:** Plugin source MUST NOT contain real beta-customer names, real email domains, or real org names. Use canonical placeholders from `references/PRIVACY_POLICY.md`.

**Severity:** BLOCK.

**How to verify:**
1. Grep skill content against the known-leak name list (from `tests/run_no_real_customer_names_test.py`).
2. Grep for any email literal `user@host`; assert host is on the allowlist: `example.com`, `*.example.com`, `chaletteholdings.com`, `mail.gmail.com`, `outlook.com`, documented platform domains.
3. Approved placeholders: `Sam Sample`, `Bo Sample`, `Rio Sample`, `Rio Lange`, `Acme Co`, `Northstar Partners`, `Category Company`, plus first-name allowlist (Skyler / Mira / Aria / Bowie / Lyra / Quinn / Dustin / Adan / Sample / Stone).

**Fix template:** Replace any real name with the canonical placeholder pair:
- "operator's main client" → `Category Company` + `Sam Sample`
- "partner org" → `Northstar Partners` + `Bo Sample`
- "prospect org" → `Acme Co`
- Real email domain → `@example.com`

Per CONTRACT.md Rule 26 + `references/PRIVACY_POLICY.md`.

---

## Gate 7 — Widget format for action surfaces

**Definition:** Any output surface that includes actionable items (send / edit / draft / skip) MUST render as a widget via `mcp__visualize__show_widget`. NEVER markdown numbered actions.

**Severity:** BLOCK if skill produces actionable output; SKIP if pure-report.

**How to verify:**
1. Detect from skill description: does the skill produce drafts (emails / memos / replies / actions)?
2. If yes, assert SKILL.md references `render_chat_output_widget()` and `shared/CHAT_ACTION_WIDGET.md`.
3. Assert no markdown patterns like `▸ send 1 ▸ draft 1`.

Per CONTRACT.md Rule 1.

---

## Gate 8 — H2 heading clickable links for deliverables

**Definition:** Any generated `.docx`/`.pdf`/`.xlsx`/`.pptx` deliverable MUST surface as an H2 heading link at the bottom of the chat turn, computed via `shared/scripts/brief_path.py::get_brief_artifact_url()`.

**Severity:** BLOCK if skill produces file deliverables; SKIP if not.

**How to verify:**
1. Detect from Phase 1 / Phase 2: does the skill produce a file?
2. If yes, assert SKILL.md references `brief_path.py::get_brief_artifact_url()` + `chat_output_renderer.doc_headline_link()`.
3. Assert no plain-text path narration like "saved to {path}".

Per CONTRACT.md Rule 3.

---

## Gate 9 — Leak scanner clean

**Definition:** Chat output (any user-facing string from the skill) MUST NOT contain forbidden tokens: `events.jsonl`, `entities.json`, `_hq/data/`, `person_NNN`, `org_NNN`, `Phase N`, `confidence: 0.X`, `commit_NNN`, internal event-type names in narration, etc.

**Severity:** BLOCK.

**How to verify:**
1. Run the leak scanner regex set from `shared/scripts/chat_output_renderer.py` against the skill's user-facing strings.
2. Includes scary error framing: `FAIL`, `CRITICAL`, `ABORT`, `ERROR`.
3. Includes user-shaming numbers: `Workspace health: D+`, percentage scores.
4. Includes internal jargon: `drift`, `overlay`, `Pass 9`, `the substrate`, `the orchestrator`.

**Fix template:** Rewrite per the friendly-voice replacement table in CONTRACT.md Rule 4.

---

## Gate 10 — First-run questionnaire cap

**Definition:** If the skill has a first-run questionnaire, it MUST be ≤5 questions.

**Severity:** BLOCK if questions > 5; SKIP if no questionnaire.

**How to verify:**
1. Parse Phase 3 output (the drafted questionnaire).
2. Count questions.
3. Assert ≤5.

**Fix template:** Drop the lowest-value question(s) OR consolidate two into one multi-select. If can't get to ≤5, the skill is asking for state that should be derived from the substrate instead.

---

## Gate 11 — RELEASE_MANIFEST.md entry (ship-time gate)

**Definition:** Every new skill must be listed in `references/RELEASE_MANIFEST.md` for the release that ships it.

**Severity:** WARN at draft-time; BLOCK at ship-time (handled by `chalette:ship-cr-plugin` Step 6 manifest gate).

**Fix template:** Phase 5 generates the manifest entry stub for M to paste.

---

## Gate 12 — CHANGELOG.md entry (ship-time gate)

**Definition:** Every new skill must have an Added entry in CHANGELOG.md for the release.

**Severity:** WARN at draft-time; BLOCK at ship-time.

**Fix template:** Phase 5 generates the stub:

```markdown
### Added
- `<skill-name>`: <one-line outcome>.
```

---

## Gate 13 — Runtime exercise test stub

**Definition:** Every new skill needs a corresponding test in `tests/runtime_exercise_<skill>.py` that exercises the canonical code paths against the synthetic workspace fixture.

**Severity:** BLOCK at draft-time.

**How to verify:**
1. At Phase 5, generate the test stub.
2. Assert ≥N cases: happy path, empty substrate, name-bearing-trigger-unknown-name, first-run-default, every gate from Phase 4.

**Fix template:** Auto-generated stub at Phase 5; M fills in the actual assertions.

Per V3.13.8 §6 Principle 1 — static checks miss bugs that runtime exercise catches.

---

## Gate 14 — Voice Calibration (composer skills only)

**Definition:** Any skill that drafts user-facing text (emails, memos, board packs, replies — anything in the operator's voice) MUST score ≥85/100 on the Voice Calibration scoring rubric.

**Severity:** BLOCK if skill is a composer; SKIP otherwise.

**How to verify:**
1. Detect composer status: SKILL.md frontmatter description mentions drafting / writing / composing / replying.
2. Invoke `chalette:voice-test` against the drafted skill's sample outputs.
3. Compare against `VOICE_SAMPLES.md` reference samples in the operator's workspace.
4. Score = weighted combo of cadence match + vocabulary match + AI-tell scrubbing + tonal alignment.
5. Threshold: ≥85 minimum.

**Fix template:**
- < 85: surface lowest-scoring sample to M with specific tells flagged
- M either rewrites the skill prompt or explicitly accepts the lower-bar score with reason logged
- < 70: AUTO-BLOCK — no override (gap too wide to ship to paying customer)

Composer-skill markers (any in description triggers composer-classification):
- "draft an email", "draft emails", "drafts email"
- "compose", "composes", "composer"
- "write a memo", "writes a memo"
- "draft a reply", "drafts a reply"
- "write in [name]'s voice"
- "follow-up draft", "outreach draft"
- "decision memo", "one-pager", "board pack"

---

## Gate 15 — Eval benchmark

**Definition:** Each new skill MUST pass quantitative eval. `chalette:skill-creator`'s Executor/Grader runs ≥3 test prompts against the drafted skill; pass rate ≥90%.

**Severity:** BLOCK.

**How to verify:**
1. At Phase 5, render a test prompts file at `tests/eval_prompts_<skill>.json` (3-10 prompts).
2. Invoke `chalette:skill-creator`'s Executor against the drafted SKILL.md.
3. Invoke the Grader with assertions for each prompt.
4. Quantitative result: % prompts that produce expected output structure.
5. Threshold: ≥90% pass rate.

**Fix template:** If pass rate < 90%, identify which prompts failed + refine skill OR revise unrealistic test prompts.

---

## Gate 16 — Description triggering accuracy

**Definition:** The frontmatter `description` field MUST score ≥0.85 on `chalette:skill-creator`'s description-improver. Composite of precision (does it activate when it should?) + recall (does it NOT activate when it shouldn't?) + negative-trigger handling.

**Severity:** BLOCK.

**How to verify:**
1. At Phase 5, run description through description-improver scoring.
2. Threshold: ≥0.85.

**Fix template:** Description-improver outputs specific reword suggestions. Apply, re-score, ship at ≥0.85.

Per the negative-trigger quoting trap (single-quoted phrases inside "DOES NOT fire on" become negative triggers — clarifying mentions must be UNQUOTED).

---

## Gate 17 — Synthetic-workspace runtime exercise PASS

**Definition:** `chalette:synthetic-workspace-runtime-test` MUST produce PASS verdict for the new skill against the synthetic-workspace fixture.

**Severity:** BLOCK.

**How to verify:**
1. After Phase 5 generates SKILL.md + test stub, drop both into temporary staging clone.
2. Invoke `chalette:synthetic-workspace-runtime-test` with `--target=synthetic --skill=<new-skill-name>`.
3. Assert verdict is PASS.

Per V3.13.8 §6 Principle 1 + production-promote-hold protocol.

---

## Gate 18 — No regression in existing skills

**Definition:** After dropping new SKILL.md into staging, `chalette:bug-regression-suite` MUST produce PASS verdict. Adding a skill MUST NOT break existing skills' triggers, substrate reads, or output contracts.

**Severity:** BLOCK.

**How to verify:**
1. Pre-drop: run `chalette:bug-regression-suite` against staging head, capture baseline.
2. Post-drop: run again with new skill installed.
3. Assert: no test that previously PASSED now FAILS.

**Fix template:** If regression detected:
- Identify which existing skill broke + why
- Most common cause: trigger phrase cannibalization
- Either refine the new skill's triggers/negative-triggers, or update the regressing existing skill to coexist
- Re-run until PASS

---

## Gate 19 — Privacy second-pass (no operator-pattern leakage)

**Definition:** Beyond Rule 26 name scan, verify no examples leak operator-specific patterns that could identify a beta operator's situation.

**Severity:** BLOCK.

**How to verify:**
1. Beyond name-scan (Gate 6), scan examples for:
   - Specific revenue figures (`$1.2M`, `$10K MRR`)
   - Specific cadence numbers (`every 14 days` may identify; `bi-weekly` is generic)
   - Specific KR target counts with identifiable names
   - Specific industry markers (`a Charleston-based hospitality client` is leak; `a hospitality client` is fine)
   - Specific dollar thresholds (`flag deals > $50K` may identify)
2. Allowed: generic patterns (weekly, quarterly, range placeholders)
3. Blocked: anything specific enough that a beta operator reading the example could recognize themselves

**Fix template:** Replace specifics with generic placeholders:
- `$1.2M MRR` → `[recurring revenue]`
- `every 14 days` → `weekly or biweekly`
- `5 deals with [real names]` → `5 enterprise contracts with [tier-1 prospects]`

---

## Gate 20 — Cross-skill collision check

**Definition:** New skill MUST NOT collide with existing skills on triggers, event types, substrate paths, folder names, or reference file names.

**Severity:** BLOCK for exact collisions; WARN for near-misses with mitigation path.

**How to verify:**
1. Parse new skill's frontmatter trigger phrases.
2. Grep all existing skills' frontmatter for exact + ≥90% semantic match.
3. Check event-type-registry for new-event-type collisions.
4. Check `_hq/data/` and `_hq/views/` for path collisions.
5. Check skills/ folder for name collisions.

**Fix template:**
- Trigger phrase collision: add explicit negative-trigger clause ("DOES NOT fire on '<phrase>' — that's `<existing-skill>`")
- Event-type collision: rename the new event type
- Path collision: choose a non-shadowing path
- Folder name collision: choose a different kebab-case name

---

## Gate verdict aggregation

After all 20 gates run, aggregate into a single verdict:

- **SHIP** — All Tier A + Tier B gates PASS. Tier C ship-time gates queued as INFO.
- **FIX-AND-SHIP** — All BLOCK-status gates pass after applied fixes; some WARNs accepted with reason.
- **REWRITE** — One or more BLOCK gates cannot be addressed without redesigning the skill's intent or scope.

The verdict appears at the top of the Phase 4 summary AND in the rendered ship-package.
