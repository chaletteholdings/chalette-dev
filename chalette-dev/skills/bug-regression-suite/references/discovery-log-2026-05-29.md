# Command Room — Discovery Log (2026-05-29)

**Purpose:** the shared findings ledger that makes the `/goal` improvement runs *compound* instead of stack.
Every run READS this file first (so it doesn't rediscover known issues) and WRITES its findings here last.
Confirmed bugs graduate from here into [bug-catalog.md](bug-catalog.md) as permanent regression entries.

**Product under test:** `commandroom1` staging copy at v3.15.0 (NOT the live customer copy `commandroom`, which is v3.14.4).

**Run order (most-learning-first):** Discovery → targeted sweeps aimed by findings → lock-in coverage → final ship check → synthesize root patterns into permanent guards.

---

## RUN 1 — Discovery pass (find everything, fix nothing)

### 1a. Existing automated checks — all GREEN (the trap)
- Static battery (`tests/run_all.py`): **46 suites passed, 0 failed.**
- Deep runtime exercise (`tests/runtime_exercise_v3_13_8.py`): **45 passed, 0 failed.**
- Event-contract test: holds — 110 canonical types, no dangling reads, no near-miss types.

> Green means "we ran out of checks," not "we ran out of bugs." The real findings are below.

### 1b. Structural gaps found in the tooling itself
- **G1 — Stale deep-exerciser (HIGH).** `runtime_exercise_v3_13_8.py` only covers v3.13.8 code paths. Product is v3.15.0. Every skill/path added in v3.14.x–v3.15.0 (incl. the `cleanup` skill) has **never been deep-exercised.** The product's best bug-finder has a two-version blind spot.
- **G2 — Runtime exerciser not in the battery (MEDIUM).** It sits beside `run_all.py`, not inside it. A green `run_all.py` does not run the deep pass. Easy to mistake "battery green" for "deeply verified."

### 1c. Orphan-signal leads (broken-promise family — investigate)
75 canonical event types have no code reader. Most are prose-consumed (fine). Flagged leads:
- `weekly_audit_run` written by `operator-report` — but cleanup release retired weekly-audit. Possible dead write / stale reference.
- `org_proposal`, `project_proposal` (insight-generator) — confirm something consumes the proposal or it's a dead write.
- `scheduled_task_failure`, `thread_resurrected`, `person_repaired`, `tier_validated` — confirm readers exist.

### 1d. Generative adversarial sweep across all 47 skills
_(filled in by the discovery fan-out — see below)_

---

## THE ROOT LEAK (most important finding)

**Every automated check is code-shaped. The product runs prose-shaped.** Skills write events, set fields, and use names from their SKILL.md *prose* (LLM-executed), not from `.py` code. The test battery only validates code-shaped writers/readers, so an entire class of contract violations lives in prose and escapes every test. Proven: the event-contract test reported "no dangling reads, no near-miss types" GREEN while ~12 skills write event types that do not exist in the schema enum. Verified by hand against `shared/data-schemas/events.schema.json`.

**The permanent guard (synthesize-phase target):** prose-scanning contract tests that read each SKILL.md and validate every event-write, field name, status value, and person name against the canonical enums/allowlists. That one structural change closes Root Patterns 1–4 below for good.

---

## ROOT PATTERNS (cluster the findings — fix the leak, not each drip)

### RP1 — Prose event writes use types absent from the schema enum (SHIP-BLOCKER class)
Verified absent from `events.schema.json`: `cleanup_run` (cleanup), `schedule_config_changed` (change-schedule), `person_disambiguation_resolved`/`_skipped` (apply-choices), `artifact_refreshed` (enable-quick-commands, enable-workspace-map), 8× `release_*` + `packaging_problem` (command-room-update-bridge), `commitment_logged`/`_delivered`/`_overdue` (team-intelligence), `bug_self_fixed` (report-bug), `project_loaded_deep` (workspace-manager). Dangling reads of non-existent types: `decision_logged`/`decision_pending` (call-prep), `outcome_positive`/`customer_won` (board-pack-assembler). Effect: events written invisibly, sections silently empty.

### RP2 — Deprecated id field `primary_project_id` / `project_id` instead of canonical `primary_thread_id` (SHIP-BLOCKER class)
Verified in 5 surfaces: workspace-manager passive-capture, people-crm enrichment `interaction` events, insight-generator, decision-log (mandates writing deprecated `project_id`), calendar-writer `meeting_scheduled`, stalled-projects doc. Effect: every downstream reader keyed on `primary_thread_id` (stall_detector, list-active, morning-briefing overlay, insight-generator) misses these events.

### RP3 — Project status values absent from the entities status enum (SHIP-BLOCKER class)
Enum is `active|dormant|paused|blocked|archived`. board-pack-assembler uses `at-risk` (SKILL.md:50); list-active filters on `completed` (SKILL.md:38,155). Effect: filters never match, projects mislabeled or never hidden.

### RP4 — Privacy: real names leak in prose despite the green name-scanner (POLISH class, high volume)
The name test passed but skeptics found ~18 unapproved names in active surfaces: Drew, Tate, Colton, Tamer, Charlie, Gary, Matt/Matthew, Pat, Pierce, Jeff, Pioneer, Marcus, Amir, Rae, Joss, Blake, "Wetsel Brothers", "Apex Advisory", "Northstar Inc" (should be Northstar Partners). **The scanner has a coverage hole** — investigate why these passed (surface exclusions? allowlist gap?). This IS the documented "denylist misses ~30%" pattern.

### RP5 — Stale references to retired weekly-audit / Cockpit (POLISH class)
operator-report reads `weekly_audit_run` as live fallback; stall_detector.py:36 docstring says "weekly-audit" (should be cleanup); command-room-update-bridge:826 routes to Commitment Cockpit (retired); report-bug:111 hardcodes "v3.3.0"; inbox-triage reads deprecated `_hq/VOICE_SAMPLES.md` (×3); dormant-customer-scan:178 cites pre-v3.13.0 `.md` deliverable path.

### RP6 — Render-path & draft-model regressions in un-migrated skills (SHIP-BLOCKER class)
inbox-triage:253 + follow-up-ritual:127 still assume EAGER Gmail draft creation — reintroduces the exact Bug #4 trust-bomb that v3.13.7 closed. one-pager-composer has contradictory docx-vs-brief_writer mandates (SKILL.md:92 vs 208/223). memo-writer Phase 5 is an empty truncated section. These skills never got the v3.13.7/v3.13.8 migration the others did.

### RP7 — Show-then-tune violations (composer/setup skills)
decision-memo-composer gates output behind a 2-phase questionnaire (SHIP-BLOCKER); scaffold-automation asks scoping questions before any default output; dormant-customer-scan + command-room-onboarding bounded violations.

### RP8 — Enforcement gates that are advisory, not mechanical (POLISH class)
team-intelligence writes entities.json directly (bypasses people_writer.py) and lacks ENTITY_RESOLVE; command-room-update-bridge Rule 7 ("never hand-roll artifact HTML") has no abort gate; scan-for-commitments commit-gate is instruction-only. Companion to the existing enforcement-gate theme.

---

## FINDINGS LEDGER (full, by skill — graduate confirmed ones into bug-catalog.md)

Ship-blocker count: ~14. Polish: ~22. Notes: ~12. Genuinely clean: intel-intake, level-up-command-room, automation-scanner, change-schedule (minus RP1), decision-revisit, file-documents, log-resolution, show-my-list, usage-report, stress-test, morning-briefing, transcript-search.

(Per-finding detail captured in the 5 sweep agent reports — promote each into a bug-catalog.md entry as the targeted sweeps confirm + fix them. RP1/RP2/RP3 confirmed by hand; RP4 names need per-name verification against the allowlist before treating as leaks.)

---

## NEXT RUNS (aimed by the above)
- **Sweep A — RP1+RP2+RP3 (event/field/status drift):** fix each, THEN build the prose-scanning guard so it can never silently recur. Highest leverage.
- **Sweep B — RP4 (privacy):** first find why the scanner missed these, fix the scanner, then let it find + fix all leaks.
- **Sweep C — RP6+RP7 (render/draft/show-then-tune):** migrate the un-migrated skills to the v3.13.7/8 contracts.
- **Sweep D — RP5+RP8 (stale refs + advisory gates):** mop-up + harden gates.
- **Lock-in:** add the new prose-scanning tests to run_all.py so the deep exercise is no longer stale/sidelined (closes G1+G2).
- **Final check + synthesize** the prose-vs-code guard as the permanent structural win.

---

## RUN 2 — Exhaustive investigation workflow (2026-05-30, run wf_a1c48cb6-f37)

415 read-only agents, ~14.3M tokens, 57 min. **395 raw → 394 unique → 301 confirmed, 93 refuted (24% refute rate).**
After adversarial severity adjustment: **81 ship-blockers, 211 polish, 9 notes.**

Confirmed the RUN-1 root leak with hard evidence: **the test suite validates code-shaped paths, but skills act via SKILL.md prose, so prose-layer violations (event types, field names, status values, names) escape every green test.** The event-contract test's near-miss window is ≤2 edits; invented types are 5-10 edits away → suppressed orphan. The name scanner's "structural" layer is a 325-name dictionary (a denylist in disguise) gated to 3 grammatical positions → misses any name it doesn't already know + every surname/org. Status + field-name drift have NO test owner (no guard loads entities.schema.json).

**Deliverables in `cr-investigation-2026-05-30/`:**
- `REMEDIATION_PLAN.md` — build-ready fix plan grouped by RP1-RP8 + the reusable hardening-workflow design. The handoff for the code session.
- `TEST_BLINDSPOT_MAP.md` — why each pattern escaped + full spec for the new `run_prose_contract_scanner_test.py` guard (the permanent fix).
- `ARCHITECTURE_CONTRACT_MAP.md` — event registry, substrate shapes, defensive-read contract, trigger map, enforcement-gate inventory (mechanical vs advisory).
- `CONFIRMED_SHIP_BLOCKERS.md` (81), `CONFIRMED_POLISH.md` (211), `CONFIRMED_NOTES.md` (9), `_SUMMARY_STATS.md`.

**The one permanent guard to build:** `run_prose_contract_scanner_test.py` (spec in TEST_BLINDSPOT_MAP §3). It reads every SKILL.md and validates prose event-writes/reads, field names, status values, and names against the canonical enums + a PRIVACY_POLICY-parsed allowlist. Closes RP1-RP4 structurally so the class can't silently recur.

