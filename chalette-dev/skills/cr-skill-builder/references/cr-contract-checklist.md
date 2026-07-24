---
title: CR Contract Checklist — the 27 Gates
cr_plugin_version_min: 5.2.0
last_updated: 2026-07-23
---

# CR Contract Checklist — 27 Gates

Every new Command Room skill MUST pass these gates before SKILL.md ships to a customer-bound release. The gates are the unique value of `cr-skill-builder` vs `chalette:skill-creator` (which only enforces SKILL_SHAPE_V2 frontmatter).

**Do not audit against this file's frozen contracts alone.** The event enum, the guard registry, and the canonical verb set all live in cr1 and move faster than any vendored snapshot can track (the reason the old `cr-event-type-registry.md` was deleted — it sat 10+ releases stale). The gates that depend on those contracts (1, 2, 7, 13, 17, 21, 22, 26, 27) name the **live source** to read at runtime, not a copy to trust. Phase 0 of the builder compares each reference's `cr_plugin_version_min` against the running cr1 `plugin.json` and raises a WARN banner on drift so you never silently audit against a stale contract.

Gates 21–25 were added for the v4.5.0 architecture (Phase 1 event gate, Phase 2 commitments-v2, Phase 3 reliability/silent-tasks, Phase 6 learning loops, Phase 7 SCL1). Gates 26–27 and the repurposed Gate 17 are the v5.2 sync (G11 description-budget, G14 date-hygiene, G13 instruction-layer — the guards that are directly skill-authoring-relevant). They encode the contracts documented in cr1's `command-room/shared/EVENT_TYPES.md`, `command-room/tests/GUARDS.md`, and the SCL1 spec — read those live before auditing against them.

For each gate: **definition** → **how to verify** → **severity** (BLOCK / WARN) → **fix template**.

**Gate count note (v3.0.0):** the builder now enforces **27 distinct gates**. The former "25" advertised a Gate 17 that was an exact duplicate of Gate 13 (both "runtime exercise") — that duplicate is folded into Gate 13, and the freed slot 17 now carries the new instruction-layer gate. Gates 1–16 and 18–25 keep their historical numbers (so the guard-to-gate map and every cross-reference survive); the three v5.2 additions are Gate 17 (instruction-layer), Gate 26 (description budget), Gate 27 (date-hygiene).

Tier ordering (number ≠ tier — the tier is set here, not by gate order):
- **Tier A** — static gates, run in-builder, fast (Gates 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27)
- **Tier B** — runtime + eval gates, delegated to existing chalette tooling (Gates 13, 14, 15, 16, 18)
- **Tier C** — ship-time gates, deferred to `chalette:ship-cr-plugin` (Gates 11, 12)

---

## Live source resolution (read before any gate that cites a cr1 contract)

Gates 1, 2, 7, 13, 17, 21, 22, 26, 27 read contracts that live in the cr1 tree, not in this reference. Resolve the cr1 clone **once, at Phase 0**, and read from it directly:

```python
# Resolve the cr1 clone path — parameterized, not hardcoded, so Eric's fork works too.
import json, os
op = os.path.join(SKILL_PLUGIN_ROOT, "config", "operator.json")
cr1_clone = "~/repos/cr1-canonical"          # M-only default (canonical edit surface)
if os.path.exists(op):
    cr1_clone = json.load(open(op)).get("cr1_clone", cr1_clone) or cr1_clone
CR = os.path.join(os.path.expanduser(cr1_clone), "command-room")
```

The live contracts each gate reads from `$CR`:

| Contract | Path under `$CR` | Gates |
|---|---|---|
| Event enum (228+ types) | `shared/data-schemas/events.schema.json` | 1, 2 |
| Event registry (writer + named consumer rows) | `shared/EVENT_TYPES.md` | 1, 2 |
| Guard registry | `tests/GUARDS.md` | audit-mode exit, 7, 13, 17, 26, 27 |
| Canonical action verbs | `shared/scripts/verb_taxonomy.py` / `chat_output_renderer.py::CANONICAL_ACTIONS` | 7 |
| Reclassification-aware activity derivation | `shared/scripts/org_activity.py::derive_from_events` | 21 |

Pull the clone first (`git -C "$CR/.." pull --ff-only`, per the canonical-edit-surface rule) so the read is current. If `$CR` does not resolve on this machine, surface a BLOCK — auditing against nothing is worse than auditing against something stale.

---

## Gate 1 — Event types registered in `events.schema.json` enum AND `EVENT_TYPES.md`

**Definition:** Every event type written by the skill MUST be registered in BOTH places, in the same commit, BEFORE any writer emits it:
1. the `type` enum in `shared/data-schemas/events.schema.json` (the machine-read enum home — the only enum copy; see `shared/EVENT_TYPES.md` "Enum home, decided once, final"), and
2. a row in `shared/EVENT_TYPES.md` naming the **writer** and at least one **named consumer** (Gate 2).

The enum is machine-read by three enforcers (the `append_event()` write-time gate, `run_source_of_truth_test.py` Check 4, and the weekly workspace audit), so an unregistered type is now a hard write-time rejection under the strict cr1 gate — not a warning.

**Severity:** BLOCK (always).

**How to verify:**
1. Parse the SKILL.md for `"type": "<value>"` event-shape examples.
2. Parse the proposed enum diff (if Phase 5 generated one).
3. Read the **live** enum + registry from `$CR` (see "Live source resolution"): `shared/data-schemas/events.schema.json` and `shared/EVENT_TYPES.md`. Never read a vendored copy — there is none anymore.
4. Assert: every event type the skill writes is either already in the enum OR in the proposed diff, AND has (or gains, in the same diff) an `EVENT_TYPES.md` row.
5. Never spell-variant an existing type. The gate normalizes known drift (e.g. `commitment_update` → `commitment_updated`) but new drift is a defect.

**Fix template:** Add a unified diff to `events.schema.json`:

```diff
    "schedule_created",
+   "<new_event_type>",
    "backfill_chunk_scheduled",
```

...AND add the registry row to `shared/EVENT_TYPES.md`:

```
| `<new_event_type>` | <name_of_writer>.py (this skill) | <named consumer skill(s)> |
```

Both land in the same commit as the skill. A payload with a required shape also gets a stanza in `shared/data-schemas/event-payloads.schema.json`.

---

## Gate 2 — Each new event type has at least one NAMED consumer in `EVENT_TYPES.md`

**Definition:** For every new event type the skill writes, AT LEAST ONE existing or new skill in the plugin MUST read it, and that consumer MUST be named in the type's `shared/EVENT_TYPES.md` row. Consumer-less writes are forbidden (EVENT_TYPES.md "Registering a new event type" step 2 — Writes-checklist item 5, enforced at review). Else: shipped a feature nobody reads.

**Severity:** BLOCK (always).

**How to verify:**
1. For each new event type, read its **live** `EVENT_TYPES.md` row (`$CR/shared/EVENT_TYPES.md`) and confirm the **Named consumers** column is non-empty.
2. Grep all skill files for `"type": "<value>"` in read contexts to confirm the named consumer actually reads it (a named-but-not-wired consumer is the same dead feature).
3. Skill author must declare in Phase 2: "Consumer for [event_type]: [skill-name]."
4. If the declared consumer is also new (e.g., morning-briefing being updated to read the new event), generate the consumer-update note as part of Phase 5.

**Consumer-check rules (migrated from the retired `cr-event-type-registry.md`):**
1. Named consumer must EXIST in `$CR/skills/` OR be a new skill created in the same ship.
2. If the consumer is an existing skill being modified to read the new event, generate a consumer-update note in Phase 5 output.
3. Zero consumers → BLOCK.

**Fix template:** Either:
- Drop the event type if no consumer can be identified, OR
- Declare which existing skill will read it, name it in the `EVENT_TYPES.md` row, + include the consumer-update note in the same ship.

---

## Gate 3 — All writes go through atomic helpers; every EVENT write goes through the gated append path

**Definition:** No hand-rolled substrate writes anywhere — no raw `open(path, "a").write(...)`, no `path.write_text(...)`, no bare `>>`. Non-event substrate uses `atomic_write_json` (entities.json / aliases.json / okrs.json / one_on_ones.json / skill_config/*.json) or a canonical wrapper (`people_writer.py`, etc.).

**Events are gated at a single chokepoint (verify against the LIVE code, not this prose).** As of cr1 Phase 4 (2026-07-02), the event gate (`shared/scripts/event_gate.py::gate_events`) runs **INSIDE** `atomic_append_jsonl`'s `events.jsonl` branch on BOTH entries — so **both** `append_event(...)` **and** a direct `atomic_append_jsonl($WS/_hq/data/events.jsonl, [event])` are fully gated (strict enum validation, type-drift normalization, `cmt_<ulid>` minting + `data.kind`, id-less-`commitment_resolved` rejection). `append_event()` is the intent-revealing entry and is preferred for new event writers, but a direct `atomic_append_jsonl` on the events path is **NOT a bypass** — do not flag it as one (that was true pre-Phase-4; the shipped `decision-log`/`decision` writer uses `atomic_append_jsonl` on the events path and is correct). Re-confirm the wiring at audit time by reading `$CR/shared/scripts/atomic_write.py` (the `is_events:` branch) — if that chokepoint ever moves, this gate's verdict moves with it.

The ONLY event-write BLOCK is a **hand-rolled raw write** that skips the chokepoint entirely (`open('a')`, `write_text`, bare `>>`), because that skips the gate.

**Severity:** BLOCK for a hand-rolled raw write (always — Bug #81 architectural fix). A gated helper call (`append_event` or `atomic_append_jsonl` on the events path) PASSES.

**How to verify:**
1. Grep skill content (SKILL.md inline bash blocks, any embedded python) for forbidden RAW patterns on the events path:
   - `open(...events.jsonl...) ... write(`
   - `path.write_text(` / `path.write_bytes(` on the events path
   - a bare shell `>> ...events.jsonl`
2. For anything that writes an event: assert it goes through EITHER `append_event(...)` OR `atomic_append_jsonl(events_path, ...)` (both are gated — see Definition). Confirm the live chokepoint still wires the gate before trusting this.
3. Assert zero hand-rolled raw writes in the skill author's code.

**Fix template:** Replace a hand-rolled write with a gated helper:

```python
# WRONG — hand-rolled, skips the gate entirely
with open(events_path, "a") as f:
    f.write(json.dumps(event) + "\n")

# RIGHT (either — both route through the event gate inside atomic_append_jsonl)
from event_gate import append_event
append_event(workspace_root, event)         # intent-revealing; preferred for new writers
# — or the locked writer directly (also gated on the events.jsonl branch):
from atomic_write import atomic_append_jsonl
atomic_append_jsonl(events_path, [event], holder="<skill>")
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
"Your brief saved to C:\Users\asdas\Desktop\Claude\..."

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

## Gate 7 — Widget format for action surfaces; actions only from the canonical verb set

**Definition:** Any output surface that includes actionable items (send / edit / draft / skip) MUST render as a widget via `mcp__visualize__show_widget`. NEVER markdown numbered actions. **And (v4.5.0):** every action verb emitted in a widget's `"actions": [...]` array MUST come from the renderer-validated canonical verb set `CANONICAL_ACTIONS` — the renderer rejects any verb outside it, and guard **G4** (`run_guard_g4_widget_verbs_test.py`) fails the battery on any prescribed `"actions"` array that doesn't validate. An action the renderer can't dispatch is an unexecutable-widget bug (the P1.1 class).

**Severity:** BLOCK if skill produces actionable output; SKIP if pure-report.

**How to verify:**
1. Detect from skill description: does the skill produce drafts (emails / memos / replies / actions)?
2. If yes, assert SKILL.md references `render_chat_output_widget()` and `shared/CHAT_ACTION_WIDGET.md`.
3. Assert every action verb in any prescribed `"actions": [...]` array is a member of the **live** `CANONICAL_ACTIONS` set (`$CR/shared/scripts/verb_taxonomy.py` → `chat_output_renderer.py::CANONICAL_ACTIONS`). Do NOT vendor a verb list here — it drifts. Do not invent verbs; extend the canonical set deliberately via the renderer if a genuinely new action is needed.
4. Assert no markdown patterns like `▸ send 1 ▸ draft 1`.

**WG1 grammar (v5.x — the current canonical shape a new skill must emit):**
- **Button rows (WG1 D-A3):** action surfaces render as the widget's button rows, driven by the surface driver — do not hand-author action markup.
- **`nudge` is a DELEGATED verb**, not a send-class verb. It lives in `surface_drivers.py::_DELEGATED_VERBS` (`nudge`, `mark received`, `snooze 3d`, `add to my plate`) and degrades (`nudge` → `add email then send`) when no owner email is known. A new skill emitting a delegated action uses the delegated row shape, never a To-bearing send row.
- **`draft` superseded `to drafts` + `edit then draft`** (v2.14.4+). A new skill emits `draft`, never the retired pair.
- **my-list verbs are RETIRED** — new skills never emit them. (`add to my list` survives only for legacy list surfaces; a fresh skill should not introduce it.)
- Because the verb set is live-read, this gate does NOT freeze the current members — it asserts membership at audit time and that no RETIRED verb (`to drafts`, `edit then draft`, my-list verbs) appears in a new skill's prescribed actions.

Per CONTRACT.md Rule 1 + the live `GUARDS.md` G4 row + WG1 (widget-grammar spec).

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
5. **Banned-word lint (v4.5.0 — guard G5):** every customer-verbatim string (blockquotes, "Say X" copy, any string the customer reads) MUST pass the **G5** banned-word list — the PL.1 list + PL.5 nouns enforced by `run_pl_banned_words_test.py`. Do NOT re-derive or inline the list here; run it / cite it. A term on the G5 list in customer-facing copy is a BLOCK.

**Fix template:** Rewrite per the friendly-voice replacement table in CONTRACT.md Rule 4; for G5 hits, replace the banned term with the approved plain-language equivalent (`run_pl_banned_words_test.py` names the substitution).

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

## Gate 13 — Runtime exercise: stub generated AND synthetic-workspace PASS

**Definition:** Every new skill needs a corresponding test in `tests/runtime_exercise_<skill>.py` that exercises the canonical code paths against the synthetic workspace fixture, AND `chalette:synthetic-workspace-runtime-test` MUST return a PASS verdict for the skill against that fixture. (This gate absorbs the former Gate 17, which was a verbatim duplicate — one runtime gate, not two.)

**Severity:** BLOCK at draft-time.

**How to verify:**
1. At Phase 5, generate the test stub.
2. Assert ≥N cases: happy path, empty substrate, name-bearing-trigger-unknown-name, first-run-default, every gate from Phase 4.
3. Drop SKILL.md + stub into a temporary staging clone; invoke `chalette:synthetic-workspace-runtime-test --target=synthetic --skill=<new-skill-name>`.
4. Assert the verdict is PASS (not WARN, not BLOCK) — runtime exercise catches the "static analysis passes but runtime substitutes an inferior path" class (Bug #11 / #45 / #52 / #53).

**Fix template:** Auto-generated stub at Phase 5; M fills in the actual assertions. A runtime BLOCK means the canonical path wasn't actually invoked — trace the freelance substitution and pin the canonical call.

Per V3.13.8 §6 Principle 1 — static checks miss bugs that runtime exercise catches. **Test-date hygiene in the generated stub is Gate 27.**

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

## Gate 16 — Trigger evals (measured, not scored-by-vibe)

**Definition:** The frontmatter `description` field MUST pass a **measured trigger eval** — a labeled query set the skill activates correctly on — with a validation score ≥0.85. This replaces the old "≥0.85 description-improver score" (which was a single opaque number). Skill activation is the bottleneck and it is description-driven (baseline auto-activation ≈ 50–55%; a directive description measurably outperforms a passive one), so the description is engineered against real queries, not eyeballed.

**Severity:** BLOCK.

**How to verify (the procedure):**
1. At Phase 5, the builder generates `tests/eval_triggers_<skill>.json`:
   - **8–10 should-fire** positives, varying phrasing and explicitness (terse, verbose, conceptual, name-bearing).
   - **8–10 near-miss negatives**, sourced from the *actual trigger tables of neighbor CR skills* (the skills this one disambiguates from) — a near-miss is a query that a sloppy description would steal from a neighbor.
2. Split 60/40 train/validation.
3. Iterate the description on the **train set only** — reword, front-load trigger stems, tighten `DOES NOT fire on` clauses.
4. Accept when the **validation** score ≥0.85 (never tune on validation — that launders overfitting into the number).
5. Final honest check: 5 fresh queries never seen during iteration; report the result even if it dips.
6. Delegated runner: `chalette:skill-creator` (its Executor/Grader + description-improver, which already carries the Mar-2026 benchmark mode — verified, no sync owed).

**Fix template:** For each misfire, identify whether it is a false-negative (positive that didn't fire → front-load its stem into the first 250 chars) or a false-positive (near-miss that fired → add/sharpen the `DOES NOT fire on [near-miss] — that's [neighbor]` clause). Re-run on train, re-accept on validation.

**Quoting trap (still load-bearing):** single-quoted phrases inside a `DOES NOT fire on` clause BECOME negative triggers; a clarifying *mention* of a neighbor must be UNQUOTED, or you silently suppress a phrase you meant to keep.

Interlocks with Gate 26 (the description you tune here must still fit the ≤980-char budget and land a stem in the first 250 chars).

---

## Gate 17 — Instruction-layer wiring (G13 mirror, draft-time)

**Definition:** Any new shared-code path the skill introduces MUST be referenced by at least one skill text — otherwise the code is invisible to the agent and the instruction layer never fires it (the F-15 invisible-code class: transport was code-complete but referenced by zero skill texts, so it never ran). Specifically: any skill text that mandates widget rendering MUST reference `widget_transport.render_and_persist` (not just `render_chat_output_widget` + `show_widget`), and byte-relay show_widget language is banned. More generally, code that only *exists* is not wired — a skill must NAME the helper it depends on in prose the router and the agent actually read.

**Severity:** BLOCK if the skill introduces a new shared-code path or mandates widget rendering; SKIP otherwise.

**How to verify:**
1. Identify every new `shared/scripts/<x>.py` entry point the skill's package introduces or newly depends on.
2. Grep the SKILL.md (and any consumer-update notes) for a reference to each such helper by name. Zero references = BLOCK (invisible code).
3. If the skill renders widgets: assert the text references `widget_transport.render_and_persist`; assert no "pass the returned html to show_widget byte-exact"-style relay language stands *without* the transport reference (that's the banned byte-relay pattern the live guard G13 catches).

**Fix template:** Add the wiring sentence to the SKILL.md body — name the helper and state when it fires:

```markdown
Every action surface is produced by `widget_transport.render_and_persist`; pass its
returned transport to `show_widget`. If the helper errors, say so and stop — never
hand-compose the widget.
```

Per the live `GUARDS.md` **G13** row (widget-transport instruction layer) + F-15 (instruction-layer-gap class). This is a STATIC check (Tier A) — it reads the shipped text, not a runtime.

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
3. Check the **live** event enum (`$CR/shared/data-schemas/events.schema.json`) for new-event-type collisions — there is no vendored registry to check against anymore.
4. Check `_hq/data/` and `_hq/views/` for path collisions.
5. Check skills/ folder for name collisions.

**Event-type collision rules (migrated from the retired `cr-event-type-registry.md`):**
1. Exact name match against the live enum → BLOCK (rename required).
2. ≥90% semantic similarity (e.g., a new `customer_scored` against an existing `customer_health_scored`) → WARN with rename suggestion.
3. Same prefix family but different shape (e.g., a new `commitment_X` type that doesn't match the canonical commitment reader shape) → BLOCK (reuse the existing shape OR introduce an explicit reader).

**Fix template:**
- Trigger phrase collision: add explicit negative-trigger clause ("DOES NOT fire on '<phrase>' — that's `<existing-skill>`")
- Event-type collision: rename the new event type
- Path collision: choose a non-shadowing path
- Folder name collision: choose a different kebab-case name

---

## Gate 21 — Commitments carry `data.kind` and close only via `close_commitment()`

**Definition:** Any skill that writes commitment-family events MUST honor the gate-enforced append contract in `shared/EVENT_TYPES.md`:
- A `type: commitment` write MUST carry `data.kind`, one of `promise | task | scheduling | agenda`. (A missing kind is stamped `promise` by the gate as the behavior-preserving default, but new producers emit kind explicitly — do not rely on the default.)
- A commitment is CLOSED only through `commitment_state.close_commitment()` — the single closure path. Never hand-build a `commitment_resolved` event, never write one via `append_event` directly. `close_commitment()` owns legacy-id normalization (seq lookup), idempotency over the full resolved-id set, the `pending_review` floor, and `data.resolution ∈ {done, dropped, superseded}`. An id-less closure is rejected at append time.
- `cru_match.build_commitment_resolved_event` is a construction-only legacy helper — never build-and-append in new code.

**Severity:** BLOCK if the skill touches commitments; SKIP otherwise.

**How to verify:**
1. Detect commitment-family writes in the skill (any `type: commitment` / `commitment_resolved` / `commitment_updated` / `commitment_reclassified` / `commitment_reopened`).
2. Assert every `commitment` write sets `data.kind` to a valid value.
3. Assert every closure routes through `commitment_state.close_commitment()` — grep for hand-built `commitment_resolved` shapes and for `build_commitment_resolved_event` used in a build-and-append pattern; both are BLOCK.

**Fix template:**

```python
# WRONG — hand-built closure
append_event(ws, {"type": "commitment_resolved", "data": {"target_id": cid}})

# RIGHT
from commitment_state import close_commitment
close_commitment(workspace_root, commitment_id=cid, resolution="done")
```

Per `shared/EVENT_TYPES.md` "Commitment-family append contract (gate-enforced)".

**Reader-derivation guidance (RECL1 — applies to any skill that derives thread/entity activity from events, not just commitment writers):** a skill that computes "last active", "quiet since", dormancy, or any recency signal from the event stream MUST derive it through `org_activity.py::derive_from_events(workspace_root, honor_reclassifications=True)` (the same path `entity_resolve`, `build_dcc_input`, `build_workspace_map_input`, and `objective_math` opt into), NOT a hand-rolled scan of `events.jsonl`. A hand scan misses reclassifications (a thread moved/renamed/merged) and reports stale activity — the RECL1 class. Flag any `for ev in events: ...` recency loop in a reader skill as a BLOCK with this fix.

---

## Gate 22 — Commitment counts come from `commitment_counts()`

**Definition:** Any header total, badge, or "N open / you owe / they owe" number the skill surfaces MUST be derived from `commitment_counts()` (over the projector's `load_open_commitments` view), never hand-summed from a filtered list or read off a lagging Tier-2 projection (PERSON.md tables, MASTER_TRACKER). Hand-rolled counts are the Bug #85 canonical-total-parity class — the coach reported 18 while the brief reported 16 for the same workspace because one side summed `you_owe + they_owe` and dropped ownerless items.

**Severity:** BLOCK if the skill surfaces a commitment count; SKIP otherwise.

**How to verify:**
1. Detect any commitment count in the skill's output (numbers labeled open/owed/commitments, header totals, badges).
2. Assert the number is sourced from `commitment_counts()` / `by_kind` — grep for hand-summed `len([...])` over a commitment list feeding a user-facing total.
3. Assert canonical-total parity: the header total equals `counts.total` (the same number every other surface reports).

**Fix template:** Replace the hand-count with the canonical helper:

```python
# WRONG
open_n = len([c for c in commitments if not c["resolved"]])

# RIGHT
from commitment_state import commitment_counts
counts = commitment_counts(workspace_root)   # counts.total, counts.you_owe, counts.by_kind, ...
open_n = counts.total
```

---

## Gate 23 — Scheduled skills register via the `SILENT_TASKS` registry + declare a watchdog receipt

**Definition:** If the skill runs on a schedule (a background/silent task, not user-fired), it MUST NOT hand-roll its own registration block. It registers by adding an entry to the `SILENT_TASKS` registry that `enable-command-room-schedules` loops on EVERY invocation (the Phase 5.9 unconditional assertion), so upgraders actually get it — the Bug #82 silent-task-registration-miss class, where each hand-written per-task block was a place to forget one. The entry MUST declare its watchdog **receipt spec**: the audit event it writes on each fire (so the task watchdog can detect `never_authorized` / chronic-lateness from a real event, not a narration) and its fire cadence. A registered task that never clears Cowork's one-time Run-Now permission never fires, and without a receipt event there's no way to know (the W2 authorization-ghost class).

**Severity:** BLOCK if the skill is scheduled; SKIP if purely user-fired.

**How to verify:**
1. Detect scheduled intent (skill fires on a cron / is a silent background task rather than a chat trigger).
2. Assert the skill adds itself to the `SILENT_TASKS` registry (not a bespoke registration block in its own prose).
3. Assert it writes a receipt/audit event on each fire (e.g. a `*_run` event) that is itself registered per Gates 1–2, so the watchdog reads a real event.
4. Assert the ritual/enable copy renders the task + its reason from what actually registered (no hardcoded task counts — see Gate G7 / Gate 9's count concern).

**Fix template:** Add the registry entry rather than a prose block:

```python
# In the SILENT_TASKS registry (enable-command-room-schedules reads this every run):
{"slug": "<task>", "cadence": "<cron/plain-english>", "receipt_event": "<task>_run",
 "reason": "<one-line why this runs>"}
```

...and emit `append_event(ws, {"type": "<task>_run", "data": {...}})` at the end of each fire. Register `<task>_run` per Gates 1–2 with the watchdog (cleanup / system-health) named as consumer.

Per `references/HISTORY.md` Bug #82 (silent-task registration miss) + the W2 authorization-ghost class.

---

## Gate 24 — Learned / customer state lives workspace-side only

**Definition:** Any state the skill LEARNS or accumulates per-customer (feedback signals, per-sender priority, prep grades, cadence baselines, customization records, tuned thresholds) MUST live in the customer's workspace substrate (`_hq/data/…`, events.jsonl, skill_config) — NEVER baked into plugin source. Plugin source is identical for every client (and fans out to every client repo on promote); a learned value written into the plugin would leak one operator's patterns into every other client's install and be clobbered on the next core update. All Phase 6 learning-loop state is workspace-side by design.

**Severity:** BLOCK.

**How to verify:**
1. Identify any per-operator learned/accumulated value the skill maintains.
2. Assert its store is a workspace path (`$WORKSPACE/_hq/…`, an event type, or `skill_config/<skill>.json`) — not a file under the plugin tree (`skills/…`, `references/…`, `shared/…`).
3. Grep for writes targeting the plugin's own directory for anything that varies by customer.
4. Cross-check Gate 19: a learned value that encodes operator specifics is also a privacy leak if it lands in source.

**Fix template:** Move the store to the workspace:

```
# WRONG — learned state in plugin source
skills/<skill>/references/learned_sender_priority.json

# RIGHT — per-customer, in their workspace
$WORKSPACE/_hq/data/skill_config/<skill>.json     (or an event type consumed by insight-generator)
```

---

## Gate 25 — Composers adopt the SCL1 §6.2 customization paragraph (optional but offered)

**Definition:** Composer skills (anything that drafts customer-facing text — emails, memos, replies, board packs; the Gate 14 composer set) SHOULD adopt the SCL1 §6.2 customization paragraph so a per-client workspace directive can tune the composer's voice/behavior without a code fork. SCL1 (Phase 7) generalizes the voice-block override into a workspace-side customization layer; §6.2 is the standard paragraph a composer includes so it reads and honors that layer. This gate is a WARN (an offered adoption), not a BLOCK — but every new composer should consciously opt in or record why not.

**Severity:** WARN for composer skills (offer + record decision); SKIP for non-composers.

**How to verify:**
1. Detect composer status (same markers as Gate 14).
2. Assert the SKILL.md either includes the SCL1 §6.2 customization paragraph (reads the workspace customization layer before composing) OR carries a one-line note stating it deliberately opts out and why.
3. Confirm the paragraph reads customization from the workspace layer (Gate 24 store), not from plugin source.

**Fix template:** Insert the canonical SCL1 §6.2 paragraph into the composer's SKILL.md (the standard block that loads the workspace customization directive and applies it to the draft), or add the opt-out note. See the SCL1 spec §6.2 for the verbatim paragraph.

---

## Gate 26 — Description budget (G11 mirror, draft-time)

**Definition:** The frontmatter `description` MUST fit the budget that the live remote-marketplace validator and guard **G11** enforce — checked at DRAFT time so a fat description is designed within budget at Phase 1, not discovered at audit:
- **≤980 chars** (the 1,024 spec cap with headroom — strict runtimes DROP an over-cap skill entirely, so it never triggers).
- **No angle brackets, no version tags** (`v5.2.0`, `<name>`) — both fail the remote validator (G15) and the local `quick_validate.py`.
- **At least one tested trigger stem inside the first 250 chars** — Claude Code truncates catalog listings, so a stem past the window is invisible at routing time.
- **Catalog-total headroom:** compute the post-add fleet total against the **53k** cap. A fat new description can blow the whole fleet's budget even if it is individually legal. Current headroom is small (~3,026 chars as of 2026-07-21) — a 980-char description is ~1/3 of it. If the add would exceed 53k, trim this description OR an existing one in the same ship.

**Severity:** BLOCK (always — it is the same failure the live G11 guard raises, just caught earlier).

**How to verify:**
1. `len(description) <= 980`.
2. No `<`, `>`, and no `vN.N.N`-style version token in the description.
3. The first 250 chars contain at least one trigger stem that appears in the eval positives (Gate 16).
4. `sum(len(d) for d in all_shipped_descriptions) + len(new) <= 53000` — read the live descriptions from `$CR/skills/**/SKILL.md` (or the chalette plugin, whichever the skill ships into).

**Fix template:** Move any workflow/composition/gate-inventory prose OUT of the description into the body (Skill Boundary / How It Works). The description carries triggers + boundaries ONLY. See WI-3 doctrine formula in `cr-skill-template.md`.

Per the live `GUARDS.md` **G11** (+ **G15** remote-validity) rows. Mirrors what `quick_validate.py` checks locally so the two never disagree.

---

## Gate 27 — Date-hygiene in generated tests (G14 mirror, draft-time)

**Definition:** Every date literal in a generated test stub (`tests/runtime_exercise_<skill>.py`, `tests/eval_*_<skill>.json`) MUST be a **computed relative date**, never a hardcoded today-or-future ISO literal. A hardcoded "future" due-date fed to a real-clock status stamp goes RED the day real-time crosses it (the MC3 time-bomb that reddened a frozen fleet). Two extra traps this gate pins:
- **Cron-boundary offsets:** an offset that lands a fixture near a cron-grid boundary flips green-in-the-morning / red-in-the-afternoon on the SAME commit (the am-green/pm-red class). Keep offsets FAR from grid boundaries — use `_ago(30)` / `_ahead(30)`, not `_ahead(1)` against a daily grid. G14 cannot catch this; the discriminator is a pristine-main re-run, so design it out.
- **Window-aging (FS-11):** a PAST literal governed by a TTL/expiry key that is still inside its window (`0 <= age <= ttl`) is also a bomb — it ages OUT and flips. Use a computed `_ago(N)` or annotate.

**Severity:** BLOCK for a hardcoded today-or-future literal in a generated test; WARN for a boundary-proximate offset.

**How to verify:**
1. Grep the generated stubs for ISO date literals (`\d{4}-\d{2}-\d{2}`).
2. Assert each is either computed (`_ago(N)` / `_ahead(N)` / `today - timedelta(...)`), a historic DATA past date, a `>= +50y` sentinel, OR carries a same-line `# DATE_GUARD_OK: <reason>`.
3. Assert no now-relative offset lands within ~2 days of the skill's own cron cadence boundary.

**Fix template:** Replace the literal with a computed offset far from any grid boundary:

```python
from datetime import date, timedelta
def _ago(n):   return (date.today() - timedelta(days=n)).isoformat()
def _ahead(n): return (date.today() + timedelta(days=n)).isoformat()
due = _ahead(30)   # NOT "2026-08-01" — and NOT _ahead(1) against a daily fire
```

Per the live `GUARDS.md` **G14** row (date-bomb gate + window-aging extension) + the cron-boundary-fixture gotcha (see "Build-relevant gotchas" below).

---

## Build-relevant gotchas promoted into named checks (D7)

Durable, build-relevant gotchas used to live only in Claude's machine-local memory — invisible to Eric and to any fresh install. They are encoded here as named checks so every builder run and every audit sees them. **Standing rule:** any NEW gotcha that constrains how skills are BUILT gets promoted into this checklist in the same session it is learned.

| Check | Rule | Enforced near |
|---|---|---|
| **Mutation fences** | A trigger/fence test proves itself by being REMOVED and watched to fail, then restored. A fence that has never been seen to fail is not known to work. Verify negatives by mutation, not by assertion alone. | Gate 16, Gate 13 |
| **YAML-quote trap** | Single-quoted phrases inside a `DOES NOT fire on` clause become live negative triggers; a clarifying neighbor *mention* must be UNQUOTED. | Gate 16 |
| **Real-data fixture shape** | Regression/runtime fixtures MUST mirror the real substrate's shape (the malformed-line tolerance, the 5 commitment shape variants, real event nesting) — a too-clean fixture passes while production breaks. | Gate 13, Gate 18 |
| **Cron-boundary fixture** | Now-relative offsets near a cron grid flip by time of day; keep offsets far from boundaries. | Gate 27 |
| **Hardcoded-future-date** | No today-or-future ISO literal in tests; compute relative or annotate `# DATE_GUARD_OK`. | Gate 27 |
| **Description-only routing** | Cowork routes on the frontmatter `description` ONLY — body trigger tables are documentation, not routing. This is the WHY behind Gates 16 + 26: all trigger-engineering budget goes into the description field, because that is the only field the router reads. | Gate 16, Gate 26 |
| **Python-eaten escapes** | JS/CSS embedded in a non-raw triple-quoted Python string eats backslashes → a dead widget script. Use raw strings (`r"""..."""`) or externalize the asset. (Belongs in any widget-producing skill's guidance.) | Gate 7, Gate 17 (instruction-layer) |
| **OOXML zip-timestamp** | NEVER byte-compare two `.docx`/`.pptx`/`.xlsx` files in a generated test (`read_bytes() == read_bytes()`) — the zip carries per-write timestamps, so identical content compares unequal. Compare the extracted payload (`_zip_payload_identical`-style), not the raw bytes. | Gate 13 |

---

## Body-quality heuristics (WI-6 — the Gate-9-adjacent body audit)

After the leak/voice gates, audit the skill BODY for guidance-form fit. Match the guidance form to the failure type it must survive (the single best body-audit heuristic):

| Failure type | Right form | Wrong form (backfires) |
|---|---|---|
| Rule violation under pressure (agent rationalizes past a gate) | Prohibition + a **rationalization table** (the excuse → why it's wrong) | A bare "MUST" — strong language alone is insufficient; Opus skips "BLOCKING" gates with rationalizations |
| Wrong output SHAPE | A positive recipe / template slot | A prohibition — telling it what NOT to produce doesn't produce the right shape |
| Omitted element | A **template slot** the renderer fills, not a prose reminder | Prose "remember to include X" — reliably forgotten |
| Conditional behavior | An observable conditional ("when X is present, do Y") | A general principle the agent must re-derive each time |

**House-style calibration (matches both the research and M's explain-the-why preference):**
- Keep `MUST` for contracts a guard machine-verifies (they are load-bearing and checked).
- Convert an UNexplained `MUST` to reasoning-based form — "do X because Y causes Z". Reasoning-based instructions get better compliance than ALL-CAPS, because the agent understands the purpose. Heavy-handed MUSTs everywhere are a named anti-pattern.

---

## Body/reference budgets (WI-7 — WARN gate)

**Definition:** A generated `SKILL.md` body persists in context for the whole session — every line is recurring token cost. Keep it lean.

**Severity:** WARN (justify or split).

**How to verify:**
1. SKILL.md body > ~500 lines OR > ~5k tokens → WARN: "does each paragraph justify its token cost? split rarely-needed detail into a reference."
2. Reference files get **conditional load triggers** — "Read `references/X.md` when [condition]" — not generic "see references/". Progressive disclosure is one level deep.
3. A reference file > 100 lines gets a table-of-contents at the top.
4. **Gotchas stay in the SKILL.md body**, never buried in a reference — the agent doesn't know to go load a reference for a gotcha it hasn't hit yet.

---

## Gate verdict aggregation

After all 27 gates run, aggregate into a single verdict:

- **SHIP** — All Tier A + Tier B gates PASS. Tier C ship-time gates queued as INFO.
- **FIX-AND-SHIP** — All BLOCK-status gates pass after applied fixes; some WARNs accepted with reason.
- **REWRITE** — One or more BLOCK gates cannot be addressed without redesigning the skill's intent or scope.

The verdict appears at the top of the Phase 4 summary AND in the rendered ship-package.
