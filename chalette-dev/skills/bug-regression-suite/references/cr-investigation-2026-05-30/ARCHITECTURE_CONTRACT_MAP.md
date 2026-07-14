# Command Room — Architecture & Contract Map (from source)

Generated 2026-05-30 from the cr-investigation run (wf_a1c48cb6-f37), derived directly from the v3.15.0 staging files. Three sections: (1) Event registry, (2) Substrate shapes, (3) Trigger map + enforcement-gate inventory.

> Note: the exhaustive per-type event registry (all 135 enum types with writer/reader cells) was produced in the run and is large; the analytically important slices — non-enum types, dead types, and substrate mechanics — are reproduced in full below.

---

# 1. EVENT REGISTRY

Canonical type list = `properties.type.enum` in `shared/data-schemas/events.schema.json:21-135` (135 types). WRITE/READ derived from grep across `skills/`, `shared/`, `references/` only.

## Substrate mechanics
- Writers reserve `seq` via `shared/scripts/next_seq.py` and append atomically (`atomic_write.py::atomic_append_jsonl`). Append-only; corrections are NEW events with `supersedes_seq`, never mutations (`events.schema.json:5`).
- Readers load defensively (`event_refs.py::load_events`) and dispatch on `ev.get("type")`. Heavy consumers: `cru_match.py` (commitments), `decision_match.py` + `render_decision_log.py` (decisions), `build_workspace_map_input.py`, `build_dcc_input.py`, `stall_detector.py`, `telemetry.py`.
- `references/DATA_CONTRACT.md:226` documents only the original ~13 core types and is stale vs the 135-type enum — do not treat as authoritative for coverage.

## (a) Types WRITTEN or READ in production but ABSENT from the enum (the real risk surface)

| token | written? | read? | evidence | assessment |
|---|---|---|---|---|
| `cleanup_run` | WRITTEN by cleanup (every run) | READ by cleanup for tail_hash | `cleanup/SKILL.md:19,109,110` | cleanup's primary audit event is not in the enum; evades the contract guard (near-miss dist >2). Add to enum, or emit canonical `audit_run`. |
| `meeting_held` | — | READ by board-pack + dont-forget last-contact | `orchestrator-dont-forget.md:451` | Latent dangling read (prose-level). Likely meant to be `meeting`. |
| `outcome_positive` / `slack_thread_touched` | — | board-pack/dont-forget read lists | `orchestrator-dont-forget.md:451` | Non-enum read targets, no writer. Same latent-dangling-read class. |
| `decision_pending` | — | call-prep risk pull | `call-prep/SKILL.md:151` | Non-enum; no writer. Risk section reads it but nothing emits it. |
| `commitment_logged`, `commitment_pending_review`, `commitment_captured` | — | READ defensively by source_event_seq_backfill | NEAR_MISS_OK in `run_event_contract_test.py:141-143` | Legacy alt-names tolerated defensively; real writer emits plain `commitment`. |
| `cracks_watch_snooze` | — | READ as legacy alias by dont-forget | `orchestrator-dont-forget.md:137` | Legacy; superseded by `dont_forget_snooze`. Read-only back-compat. |
| `dormant_flag` | — | — (historical) | `operator-report/SKILL.md:72` | Already migrated to `pattern_break_detected`. |

Non-event `"type"` values that correctly stay out of the enum (intentional overloads of the `type` key): entity `type` in entities.json (`home`/`side`/`personal`); interaction channel (`email`/`slack`/`call`/`note`/`in-person`); widget/DCC node `type` (`stuck`/`anomaly`). Flagged so they aren't mistaken for missing event types.

## (b) Enum types that are DEAD (never written, or never read)

**Never WRITTEN by any production surface** (contract-guard-sanctioned reader-only / not-yet-wired):
- `commitment_superseded` — reader-only forward-compat (`run_event_contract_test.py:127`).
- `person_added` — reader-only defensive accept (`:128`).
- `project_stalled_flagged` — write side deferred to v3.14.2 (`stalled-projects/SKILL.md:22`); fully dead today.
- `briefing` — superseded by `pack_run`; only DATA_CONTRACT/README prose names it.
- `audit_run` — no current writer (legacy read-only; cleanup writes non-enum `cleanup_run` and only reads old `audit_run`).
- `bug_received` — no writer or reader (report-bug emits `bug_reported`). Unused/aspirational intake type.
- `thread_repaired` — in enum (parallel to person/org_repaired) but `thread_writer.py` has no repair emit and nothing reads it.

**Written but never READ by a code-shaped consumer** (mostly intentional audit/telemetry; the contract test's orphan detector "over-reports heavily"):
- Allowlisted-OK: `pack_run`, `schedule_created` (`:133-136`).
- Entity-mutation audit trail, no code reader: `org_created`, `org_updated`, `org_repaired`, `thread_created`, `thread_updated`, `person_updated`, `person_merged`, `person_repaired` (consumed only by view regeneration / prose).
- Deliverable/telemetry, no code reader: `email_sent`, `bug_reported`, `levelup_session`, `operator_report_generated`, `onboarding_setup_widget_emitted`, `weekly_recap_run`, `connector_read`, `scope_change`, `scheduled_task_failure`, `m1_backfill_started`, `m1_backfill_complete`, `skill_first_run_configured`, `skill_reconfigured`, `plugin_update_deferred`, `plugin_update_remediation`, `artifact_install_failed`, `file_filed`, `chat_suppressed`, `choices_applied`, `intro_landed`, `intro_didnt_land`, `contact_email_captured`.

Caveat: the contract test being green asserts zero dangling reads of *canonical* types and zero near-miss typos. The "never read" set is dominated by intentional audit/telemetry and prose-only consumption a code scan cannot see — not necessarily defects.

## Highest-signal cross-checks
- `tests/run_event_contract_test.py` `DANGLING_READ_OK`/`ORPHAN_WRITE_OK`/`NEAR_MISS_OK` allowlists (`:126-148`) = canonical record of every deliberate exception.
- `events.schema.json:21-135` = source of truth (135 types). Add `cleanup_run` or migrate cleanup to `audit_run`.
- `cru_match.py` + `decision_match.py` = densest reader/writer logic (commitment + decision state machines).
- Representative heavy types: `commitment` (written by meeting-notes/scan-for-commitments/inbox-triage/team-intelligence; read by cru_match/build_workspace_map_input/stall_detector/+); `decision` (written by decision-log; read by render_decision_log/decision_match/board-pack/contract-review/+); `pack_run` (every orchestrator; read by telemetry/usage-report); `pattern_break_detected` (the canonical dormancy flag, replaced non-enum `dormant_flag`).

---

# 2. SUBSTRATE SHAPES

Substrate: `_hq/data/entities.json` (source of truth) + `_hq/data/events.jsonl` (append-only). Markdown views are regenerated from entities.json (`entities.schema.json:5`).

## entities.json
**Top-level keys (required):** `version`, `last_updated`, `last_writer`, `entities` (`entities.schema.json:7`). `version` bumps every write (optimistic concurrency). `workspace` is an OPTIONAL top-level sibling of `entities` (NOT nested) holding `user_id` (canonical owner signal, preferred over legacy `is_primary_user`), `user_timezone`, `first_go_months`, `schedule_timezone` (`:46-49, 409-432`).

**The `entities` wrapper (nested) vs flat top-level.** Canonically the collections are nested under an `entities` wrapper requiring `people`, `projects`, `orgs` (+ optional `engagements`) (`:23-45`). Writers reach them via `entities_collection(data, "people"|"orgs")`. The stall detector makes the tolerance explicit: `raw.get("entities") if isinstance(dict) else raw` (`stall_detector.py:148`) — accepts BOTH nested and flat.

**projects vs threads.** `projects` is the canonical JSON key (`:25`; record `$def` named `project`). BUT `threads` is the canonical user-facing/model language, and `stall_detector.py:26-28,151-164` treats `threads` as preferred, `projects` as legacy fallback ("schema drift — records renamed to threads but the helper wasn't updated"). Id prefix stays `project_` regardless (`:160`). Person↔thread links live in a field literally named `project_ids` ("Threads this person is involved in", `:106-110`). **A reader cannot assume one key name.**

**Project record — `status` enum and `status` vs `stage`.** `status` is a 5-value enum: `active|dormant|paused|blocked|archived` (`:174-177`). BUT `stall_detector.py:64,79-86` uses a 6-value vocabulary **including `exploring`** (not in the JSON enum). `stage` is a DIFFERENT field: integer 0-5 (`:179-183`), a numeric progression marker, NOT the lifecycle state. The stall detector conflates them defensively: `thread.get("status") or thread.get("stage") or "active"` (`:248`). Other project fields: `kind` enum (`:213-217`, supersedes DEPRECATED `project_class`), `affiliation_id` (supersedes DEPRECATED `org_id`), `last_activity`, `first_seen`.

**Person record — writer allowlist** (`people_writer.py:118-140`, kept in sync with schema): id/canonical_name/first_seen (required) + aliases, nicknames, role, primary_org_id, affiliation_ids, org_id(dep), email(dep), emails(canonical array v3.13.0+), phones, project_ids, last_interaction, last_touched_at, connections, notes, communication_style, reports_to_id, status(active|archived), needs_enrichment. Read emails via `get_person_emails()`, never `record["email"]`. `needs_enrichment` replaces the FORBIDDEN `pending_review`/`inferred_from`. **FORBIDDEN person keys** (`:151-180`, rejected by `_validate_person`): display_name/name→canonical_name, current_org_id→primary_org_id, org_ids→affiliation_ids, last_seen/last_contact→last_interaction, pending_review/inferred_from/confidence→remove (gate via events), is_primary_user→remove (use workspace.user_id), relationship_type/tier→remove (org-level, not person-level), created_at/created_by→remove (person_created event).

**Org record — writer allowlist** (`org_writer.py:52-73`): id/canonical_name (required) + aliases, scope, scope_label, parent_org_id, relationship_type, relationship_label, tier, is_primary_focus, domains, slack_workspace_ids, inferred_from, first_seen, last_interaction, status, type(dep), domain(dep), notes, needs_enrichment. Enums: `scope` (holding|operating|division|brand|fund|other), `relationship_type` (operating|partner|board|advisory|investment|client|portfolio_company|beneficiary|vendor|prospect|service_provider|other), `tier` (primary|secondary|external|passive, default secondary). `domains[]` canonical; `domain` DEPRECATED. `inferred_from` is canonical for orgs (opposite of persons). **FORBIDDEN org keys** (`:79-89`): name/display_name→canonical_name, nicknames→aliases (opposite of person!), industry/tags→notes, primary_user→remove.

## events.jsonl
**Required envelope:** `seq`, `ts`, `type`, `source_skill`, `data` (`events.schema.json:7`). `seq` ≥1 monotonic (reserved by atomic_append_jsonl, writers do NOT set it). `ts` = ISO 8601 of the EVENT, not write time (v3.13.6 renamed off-schema `timestamp`→`ts`, nested per-event fields under `data`).

**Canonical thread-id field + deprecated aliases.** `primary_thread_id` is canonical (pattern `^project_[0-9]{3,}$`; null for workspace-level events; `:141-145`). `project_id` is DEPRECATED — "Use primary_thread_id. Retained for backward compat; readers should fall back to this if primary_thread_id is missing" (`:165-167`). **`primary_project_id` does not exist in the schema at all** — the only deprecated alias defined is `project_id`. Inside event `data`, writers/stall-scan use `data.project_id` / `data.primary_thread_id`.

**related_thread_ids vs related_project_ids.** `related_thread_ids` is canonical (`:146-153`); `cross_ref_reason` maps each to a reason. **`related_project_ids` does not exist anywhere** — no deprecated plural form. Other envelope fields: `classification_confidence` (≥0.75 auto / 0.40-0.75 provisional / <0.40 low), `person_ids[]`, `org_ids[]`, `source_ref_hash` (passive-capture dedup), `supersedes_seq`.

## Defensive-read contract (the stall detector is the reference implementation)
- **(a) Both collection keys** — read `threads` first, fall back to `projects`, dedupe by id (`stall_detector.py:140-164`).
- **(b) Both nestings** — `raw.get("entities") if dict else raw` (`:148`).
- **(c) status/stage fallback + `exploring`** — `status or stage or "active"` (`:248`); tolerate the 6-wide vocabulary incl. `exploring` even though the JSON enum has 5; `archived` → never flagged.
- **(d) project_id/primary_thread_id fallback inside data** — `data.get("project_id") or data.get("primary_thread_id")` (`:210`); schema-level guidance is the same fallback in opposite default order. A correct reader accepts EITHER key.
- **(e) email/domain merge** — `get_person_emails()` / `get_org_domains()`, never the singular field directly.
- **(f) date robustness** — accept date-only or datetime, skip malformed rows, return `[]` on missing/decode error.

## Cross-file discrepancies worth flagging
1. `projects` (schema) vs `threads` (thread-model code) — reader must accept both.
2. Status enum width — schema 5 (no `exploring`) vs stall_detector 6 (with `exploring`).
3. `primary_project_id`/`related_project_ids` named in some prose do not exist in the schema; only `project_id` (singular) is a defined deprecated alias.
4. `nicknames` ALLOWED on persons, FORBIDDEN on orgs; `inferred_from` FORBIDDEN on persons, canonical on orgs.

---

# 3. TRIGGER MAP + ENFORCEMENT-GATE INVENTORY

## A. Trigger map (highlights + overlap clusters)
Trigger families derived from each skill's frontmatter `description`; cross-checked against `tests/triggers.yaml`. Every "overlaps with" is an explicitly-defended boundary unless noted.

**Quoting-trap finding:** the DOES-NOT-fire convention is single-quoted across the plugin (30+ skills). **`cleanup` is the lone double-quote outlier** (`"weekly recap"`, `"level up command room"`) — the single inconsistency in the negative-trigger quoting convention. `weekly-recap` uses a third style (backticked skill names). Single-quoting a phrase in a DOES-NOT clause risks the router treating it as a live positive trigger.

**Highest-risk overlap clusters (all defended, but worth monitoring):**
1. **"prep me for …"** — call-prep (meetings) vs people-crm ("prep me for dinner") vs out-of-scope speaking prep. `triggers.yaml:465` pins "prep me for my 2pm" → call-prep.
2. **"follow up" + meeting** — follow-up-ritual claims ALL such phrasing; meeting-notes disclaims it (`triggers.yaml:46-57`).
3. **decision triad** — decision-log (capture) / decision-memo-composer (forward) / decision-revisit (backward).
4. **"audit" vocabulary** — automation-scanner owns "automation audit"; cleanup absorbs retired "weekly audit". `triggers.yaml:147`: bare "audit" was DROPPED to resolve the one historical real collision.
5. **list-active vs workspace-manager** — both can see "what … projects"; `triggers.yaml:477-487` pins "what's going on"/"lets work" to workspace-manager.
6. **ingest family** — workspace-ingest (pipeline) vs ingest-context (no copy) vs file-documents (copy) vs intel-intake (single URL).

Mechanically gated by `tests/run_trigger_test.py` (runs every triggers.yaml phrase against all descriptions; exit 1 on zero/multi/mis-match) — BUT it is a literal-overlap heuristic and "will miss semantic-only matches" (`:21-24`), so disambiguation is partly mechanical, partly trust-the-LLM.

## B. Enforcement-gate inventory
MECHANICAL = a script/test returns non-zero on violation and is in `run_all.py`. ADVISORY = MUST/NEVER prose with no failing test.

| # | Gate | Declared at | Enforcement | Evidence |
|---|---|---|---|---|
| 1 | Atomic-write helper usage (no raw write to entities.json/events.jsonl) | WORKSPACE_API.md:108 | **MECHANICAL (static)** | `run_cr_skill_validator_test.py:135` gate_3 returns BLOCK on `.write_text(`/`open(...,"a")` in skill bodies; + atomic_write/append unit tests. |
| 2 | ENTITY_RESOLVE before name writes | ENTITY_RESOLVE_PROTOCOL.md:18-44 | **MECHANICAL (static)** | `run_entity_resolve_enforcement_test.py:53-87` fails if any of 10 covered skills lacks the marker; validator gate_4 BLOCKs name-bearing triggers without resolve ref. **Caveat:** verifies the marker EXISTS, not that the runtime path calls it — a structural floor, not a runtime trace. |
| 3 | Lazy-vs-eager Gmail draft (no draft at fire time) | EMAIL_DRAFT_PROTOCOL.md:31-43 | **ADVISORY** | No test asserts lazy timing. `run_helpers_test.py` tests only tool *discovery*, not lifecycle. **The most exposed of the six** — the eager-draft regression that bit v2.7.x-v2.9.2 has no automated guard today. (This is exactly the RP6 inbox-triage/follow-up-ritual regression the audit found.) |
| 4 | brief_writer vs docx skill | meeting-notes/SKILL.md:444; brief_writer.py:1-12 | **ADVISORY routing; MECHANICAL byte-content** | No test fails if a skill hand-rolls a docx; but the docx leak scanner (`run_docx_leak_scanner_test.py`) gates the resulting bytes. Produce-path advisory, content gated. |
| 5 | Never hand-roll artifact HTML | CONTRACT.md:11 (Rule 1); CHAT_ACTION_WIDGET.md:320 | **MECHANICAL (runtime + static)** | `render_chat_output_widget()` raises CanonicalActionError/ValueError on non-canonical actions; render_artifact.py exits 1 on unsatisfied `{{PLACEHOLDER}}`; validator gate_7 + widget_transport/chat_output/spec_example tests. |
| 6 | Writer-helper-only entity writes | org_writer.py:6-8; people_writer.py:1-32 | **MECHANICAL at helper boundary; ADVISORY for "skills must route through it"** | people_writer rejects unknown keys + dedups (tested). But no test scans SKILL.md to prove skills *call* the writer vs hand-rolling — Gate 3 (raw write detection) is the partial backstop. |

**Adjacent mechanical guards (same BLOCK/exit-1 model):** Rule 27 no-.md-deliverables, Rule 26 no-real-names (the one with the 325-name blind spot — see TEST_BLINDSPOT_MAP.md), Rule 25 no-hardcoded-paths, event-type-in-enum validator gate_1, next_seq reservation, docx leak scanner.

**Bottom line:** Fully MECHANICAL = atomic-write (1), ENTITY_RESOLVE reference (2), never-hand-roll-HTML (5). Helper/byte-boundary only = writer-helper entity writes (6), brief_writer-vs-docx (4). Purely ADVISORY = lazy-vs-eager Gmail draft (3), the most exposed gate and the source of the RP6 regression.
