# Command Room — Build-Ready Remediation Plan

**Source:** cr-investigation workflow run `wf_a1c48cb6-f37`, dated 2026-05-30
**Findings corpus:** `skills/bug-regression-suite/references/cr-investigation-2026-05-30/` (`CONFIRMED_SHIP_BLOCKERS.md`, `CONFIRMED_POLISH.md`, `_SUMMARY_STATS.md`)
**Plugin root (all paths below relative to this unless noted):** `C:/Users/asdas/.claude/plugins/marketplaces/commandroom1/command-room/`
**Canonical edit surface:** the staging marketplace clone above *is* the source of truth (Option B model, per `chalette:ship-cr-plugin`). All edits land there.

---

## 1. Executive summary

### Counts by severity
- **Confirmed real findings: 301** (from 394 unique, 395 raw — 93 refuted as false-positive)
- **Ship-blockers: 81**
- **Polish: 211**
- **Notes: 9**

### Counts by root pattern (confirmed, ship-blocker + polish)
Aggregating the `_SUMMARY_STATS.md` "by family" breakdown into the eight named root patterns plus trigger collisions:

| Pattern | Theme | Approx. confirmed count |
|---|---|---|
| **RP1** | Event types absent from `events.schema.json` enum (writes + reads) | ~80 (largest cluster: RP1 variants + "event-contract drift" + "phantom event type" + per-type entries) |
| **RP2** | Deprecated id field (`primary_project_id` / `project_id` vs canonical `primary_thread_id`) | ~35 (RP2 variants + field-drift + deprecated-field entries) |
| **RP3** | Project status values outside the entities enum (`at-risk`, `completed`, `exploring`, `resolved`, `vendor`, `referral`, `placeholder`, Title-Case commitment statuses) | ~20 |
| **RP4** | Real person/org names leaking past the name-scanner | ~75 (the single largest theme by raw family count) |
| **RP5** | Stale references to retired features (weekly-audit, Commitment Cockpit, Pay Attention To, VOICE_SAMPLES.md, stale action-token formats) | ~20 |
| **RP6** | Render-path / draft-model regressions (eager Gmail draft, docx-vs-brief_writer, empty mandatory phases) | ~12 |
| **RP7** | Show-then-tune violations (output gated behind questions) | ~9 |
| **RP8** | Advisory-not-mechanical enforcement gates (no bash pre-flight import check; ENTITY_RESOLVE bypass) | ~10 |
| **Trigger collisions** | Overlapping positive triggers with no DOES-NOT guard | 1 confirmed (`workspace-manager` vs `cleanup`) |

(Counts overlap because many findings are co-tagged, e.g. an RP2 deprecated-field finding is also an "event-contract drift" finding. The pattern groupings in Section 2 are the authoritative work units.)

### The single root leak

**Tests validate code-shaped paths, but skills act via SKILL.md prose, so prose-layer violations escape every test.**

The Command Room test battery (`synthetic-workspace-runtime-test`, `compare-canonical-vs-freelance`, `run-command-room-tests`, the helper scripts under `shared/scripts/`) exercises the **Python writer/reader layer** — `people_writer.py`, `org_writer.py`, `thread_writer.py`, `cru_match.py`, `stall_detector.py`, `entity_resolve.py`. Those scripts are correct or near-correct. But skills do not *call* a typed API for most of their substrate I/O; they **instruct an LLM in SKILL.md prose** to "write a `project_loaded_deep` event," "tag with `primary_project_id`," "read `decision_logged` events," "sign `—Matt`." The model obeys the prose. Because:

1. **No schema gate sits between prose and the JSONL append.** `atomic_append_jsonl` does not validate `type` against the enum, so an invalid event type is written silently and read back successfully by the same prose match — the failure is invisible until a typed consumer or validator runs (RP1).
2. **The open-object entity schema accepts unknown fields.** `primary_project_id` is silently accepted and even partially handled by `event_refs.py`, so RP2 drift produces *thin* output, never an error.
3. **Readers filter by string match, so a typo-class type just returns zero rows** — an empty section, not a crash (RP1 reads: empty §3 Wins, empty "Decisions Already On The Record").
4. **The name-scanner (`docx_leak_scanner.py`) only scans `.docx` render output**, not SKILL.md prose or reference docs — so real names sitting in instruction text (`Drew`, `Matt`, `Tate`, `Colton/Tamer`, `Andrea Wetsel`) ship untouched (RP4).

Every one of the eight root patterns is the same failure mode viewed from a different angle: **the contract is enforced in code, but the actor is prose, and nothing validates the prose.** The fix is therefore two-layered: (a) correct the prose now, and (b) add the *one* missing mechanical gate per pattern (an enum, a pre-flight check, a prose-layer scanner) so the prose can never drift undetected again.

### Top 10 ship-blockers by real customer impact

Ranked by how badly the *paying customer's* output breaks, not by count:

1. **`orchestrator-dont-forget.md:149,171,290` — Pulse computes `last_event_date` via `primary_project_id == project.id`, a field that does not exist (RP2).** Pulse fires 9 AM every weekday. Every active project gets `last_event_date = null`, is flagged stale, and is auto-transitioned **active → dormant → archived**. This silently archives the customer's live work. *Highest-impact finding in the corpus.* (`CONFIRMED_SHIP_BLOCKERS.md:240-242`, `:255-257`)

2. **`inbox-triage/SKILL.md:253-256` — eager Gmail draft creation (`send`/`draft` act on an "eager-created `gmail_draft_id`").** 2-3 unapproved reply drafts land in the customer's real Gmail Drafts folder every morning triage, before any widget choice. Violates `EMAIL_DRAFT_PROTOCOL.md` §1 lazy model. (`CONFIRMED_SHIP_BLOCKERS.md:198-200`)

3. **`follow-up-ritual/SKILL.md:104` — Step 5 "Create Gmail drafts" unconditionally, before the widget.** Same eager-write class as #2; populates Gmail with unsanctioned drafts on every post-meeting run. (`CONFIRMED_SHIP_BLOCKERS.md:168-173`)

4. **`workspace-manager/SKILL.md:313,314,395,413,481,547` — passive-capture writes `primary_project_id` / `related_project_ids[]` across the four highest-frequency flows (morning briefing, `go [project]`, new project, end session).** Every interaction/meeting event the workspace writes is thread-orphaned. The commitment auto-drop reader and stall detector never see them. (`CONFIRMED_SHIP_BLOCKERS.md:354-365`)

5. **`team-intelligence/SKILL.md:16` — writes `commitment_logged` / `commitment_delivered` / `commitment_overdue`, none in the enum; `cru_match.py:684` accepts only `commitment`.** Every direct-report commitment a CEO logs is invisible to morning-briefing, stall-detection, and every list view. The accountability layer silently drops 100% of its data. (`CONFIRMED_SHIP_BLOCKERS.md:318-323`, `:330-332`)

6. **`inbox-triage/SKILL.md:65,75` — real customer names `Colton` + `Tamer Designs`, a live `$300K` deal value, and the user email `matthew@chaletteholdings...` in MUST-language gate prose.** Ingested into context on *every* triage run; cross-customer data leak in a shipped file. (`CONFIRMED_SHIP_BLOCKERS.md:183-197`)

7. **`board-pack-assembler/SKILL.md:46,105,119` — §3 Wins reads `outcome_positive` / `customer_won`, neither in the enum.** Every board pack a CEO hands to their board has a permanently empty Wins section. (`CONFIRMED_SHIP_BLOCKERS.md:30-44`, `:51-53`)

8. **`call-prep/SKILL.md:127,148,151,167` (+ `orchestrator-upcoming-meetings.md:114`) — reads `decision_logged` / `decision_pending`; canonical is `decision`.** Every call-prep brief (manual *and* the scheduled 9 AM upcoming-meetings fire) walks the CEO into the meeting with an empty "Decisions Already On The Record" section. (`CONFIRMED_SHIP_BLOCKERS.md:57-74`, `:273-275`)

9. **`email-writer/SKILL.md:363,381,391,405` (+ `follow-up-ritual:252`, `orchestrator-commitments:595`) — default uncalibrated voice signs every draft `—Matt`.** Every customer's email drafts are signed with the maintainer's name until they manually calibrate. Functional defect, not just a leak. (`CONFIRMED_SHIP_BLOCKERS.md:114-116`, `:177-179`, `:228-230`)

10. **`orchestrator-dont-forget.md:660` — the "N resolved" Pulse action writes `status: 'resolved'`, absent from the project status enum.** A customer clicking the surfaced action corrupts the project's status to an invalid value that no list/filter recognizes; the project vanishes from active views. (`CONFIRMED_SHIP_BLOCKERS.md:156-158`)

---

## 2. Remediation plan grouped by root pattern

For each pattern: the canonical corrected value, the confirmed findings as `skill — file:line — one-line fix`, the safe migration order, and the **one** regression test that catches the whole pattern going forward.

The single highest-leverage prerequisite spanning RP1/RP2/RP3: **`shared/data-schemas/events.schema.json` and `entities.schema.json` are the canonical contracts.** Most of this work is editing prose to match them. Where a *type genuinely needs to exist* (cleanup, schedule-change, release-lifecycle, disambiguation, artifact-refresh), the fix is to **add it to the enum**, not to rename the prose.

---

### RP1 — Event types absent from `events.schema.json` enum

**Decision rule (apply per type):**
- If a **canonical equivalent already exists** → fix the prose to use it (rename).
- If the type names a **real lifecycle event with no equivalent** → add it to the enum at `events.schema.json` (and to `DATA_CONTRACT.md`).

**Rename to existing canonical type:**

- `board-pack-assembler — SKILL.md:46,105,119` — replace `outcome_positive` / `customer_won` reads with the canonical win signal (`status_change` to a won state, or `intel_logged`); confirm against what any skill actually writes, then make §3 Wins read that.
- `call-prep — SKILL.md:127,148,151,167` — replace `decision_logged` → `decision`; replace `decision_pending` → `decision_open` (the canonical pending/stuck type per `decision-log`).
- `enable-command-room-schedules/references/orchestrator-upcoming-meetings.md:114` — replace `decision_logged` → `decision`.
- `team-intelligence — SKILL.md:16` — replace `commitment_logged` / `commitment_delivered` / `commitment_overdue` → `commitment` / `commitment_resolved` / `commitment_overdue`(canonical set per `cru_match.py:684`). **Confirm the canonical third type name** against `cru_match.py` before editing.
- `enable-command-room-schedules/references/orchestrator-dont-forget.md:294,313,672,673` — replace `person_record_update` / `person_record_update_rejected` → canonical `person_updated` (+ carry rejection in `data`), OR add the two types (see below) — **decide once**; the rejected-type carries a 60-day cooldown contract, so if renamed, the cooldown reader at `:122` must read the new type.
- `enable-command-room-schedules/references/orchestrator-dont-forget.md:116` — `follow_up_draft` → `followup_pack_drafted` (canonical, already in schema).
- `enable-command-room-schedules/references/orchestrator-historical-backfill.md:74` and `workspace-manager/SKILL.md:413` — `file` → `file_filed` (canonical).
- `operator-report — SKILL.md:94` — fallback counts `weekly_audit_run`; retarget to the canonical cleanup event (see RP1 add-or-rename for `cleanup_run` below) — keep this consistent with whatever `cleanup` ends up writing.

**Add to the enum** (type names a real event with no canonical equivalent):

- `cleanup — SKILL.md:19,67,109,110` — add `cleanup_run` to `events.schema.json` (schema currently has only legacy `audit_run`/`weekly_audit_run`). This is the cleanest fix; renaming to `audit_run` would resurrect retired-skill semantics. Update `DATA_CONTRACT.md:237` payload row to match (`cleanup_run`, not `audit_run`).
- `change-schedule — SKILL.md:180,184,230` — add `schedule_config_changed` (or reuse existing `workspace_setting_changed` — pick one; `schedule_config_changed` is more specific and audit-legible). Also add the required `seq` field the writer omits.
- `command-room-update-bridge — SKILL.md:757-786` — add the 8 `release_*` types + `packaging_problem` (`:340`), OR collapse all release-error paths onto a single `release_action_failed` with a `phase` discriminator in `data` (preferred: 1 enum entry, not 9).
- `apply-choices — SKILL.md:191,193` — add `person_disambiguation_resolved` / `person_disambiguation_skipped` (the skipped type carries a 60-day cooldown contract, so it must be a real, queryable type).
- `enable-quick-commands — SKILL.md:26,27` and `enable-workspace-map — SKILL.md:22,23,78` — add `artifact_refreshed` (schema has `artifact_installed` / `artifact_install_failed` but not the rebuild signal) and `packaging_problem`.
- `report-bug — SKILL.md:72` — add `bug_self_fixed` (schema has `bug_received`/`bug_reported`; the self-fix outcome is a distinct, reportable state).
- `workspace-manager — SKILL.md:403,413` — add `project_loaded_deep` (it gates the expensive ~400K-token first-`go` deep-load; if it silently fails enum validation in a future hardening pass, every `go [project]` re-runs the deep-load — a real cost regression).
- `change-schedule`/`schedule_created` family, `orchestrator-dont-forget.md:101` `pulse_live_check_overrode`, `:369` `noise_filter_review_needed`, `orchestrator-past-meetings.md:124` `brief_save_failed`, `people-crm:386` `person_enriched` (as a typed `note` subtype or its own type) — add or fold into canonical per the same decision rule. `person_enriched` specifically needs a documented `data` shape (`DATA_CONTRACT.md` currently has three incompatible `note` shapes — see RP1 note below).

**`note` payload divergence** (`people-crm:386`, `weekly-recap:121`, `orchestrator-historical-backfill.md:87`): define one canonical `data` contract for `note` in `DATA_CONTRACT.md`; today a typed `data.text` reader would get `undefined`.

**Safe migration order (RP1):**
1. **First, edit `events.schema.json`** to add every genuinely-new type (single commit). This makes the schema a superset — no existing data breaks.
2. **Then** fix all the *rename* prose (board-pack, call-prep, team-intelligence, orchestrators) — these are pure find-and-replace in SKILL.md / reference docs.
3. **Then** update `DATA_CONTRACT.md` to mirror the new enum and the `note` shape.
4. No data backfill required: invalid events already written are tolerated by the open schema; the fix is forward-looking.

**The ONE regression test for RP1:**
A test that **statically extracts every event `type` string literal from all SKILL.md files and reference `.md` files** (regex for `type: '<x>'`, `type "<x>"`, "writes `<x>` events", "reads `<x>` events") and asserts each is a member of the `events.schema.json` enum. This is a *prose scanner*, not a code test — it closes the exact gap the root leak describes. Wire it into `bug-regression-suite`. (Companion: extend `integrity_check.py` to validate `type` against the enum at append time, so runtime drift is also caught.)

**Effort: L** (≈80 findings, but ~70% mechanical rename; the judgment is the add-vs-rename decision per type, done once.)

---

### RP2 — Deprecated id field (`primary_project_id` / `project_id` → `primary_thread_id`)

**Canonical:** top-level `primary_thread_id` (and `related_thread_ids[]`) on every event. `project_id` is a DEPRECATED alias; `primary_project_id` is **not even a valid alias** — it does not exist anywhere in the schema. `data.project_id` (nested) is wrong location even when the name is tolerated.

**Confirmed findings:**

- `enable-command-room-schedules/references/orchestrator-dont-forget.md:149,171,290` — `primary_project_id == project.id` → `primary_thread_id`. **(Ship-blocker #1 — see §1.)** Fix all three filter expressions.
- `enable-command-room-schedules/references/orchestrator-dont-forget.md:158,658,660` — `status_change` event uses `data.project_id` → move thread ref to top-level `primary_thread_id`.
- `enable-command-room-schedules/references/orchestrator-commitments.md:878` — context-builder reads `primary_project_id == this project` → `primary_thread_id`.
- `enable-command-room-schedules/references/orchestrator-inbox.md:74` + `orchestrator-dont-forget.md:452` — person records read deprecated `org_id` → canonical `primary_org_id` (the +25 relationship bonus silently scores zero otherwise).
- `workspace-manager — SKILL.md:313,314,395,413,481,547` — `primary_project_id` / `related_project_ids[]` → `primary_thread_id` / `related_thread_ids[]`. **(Ship-blocker #4.)**
- `insight-generator — SKILL.md:168` — Pass 7 passive-capture writes `primary_project_id` → `primary_thread_id`.
- `people-crm — SKILL.md:359` — enrichment-pipeline interaction events write `primary_project_id` → `primary_thread_id`.
- `calendar-writer — SKILL.md:22,158` — `meeting_scheduled` payload `data.project_id` → top-level `primary_thread_id`.
- `decision-log — SKILL.md:14` — "stamp `data.project_id`" → stamp top-level `primary_thread_id` (keep `data.project_id` only if a documented dual-write is intended; otherwise drop).
- `memo-writer — SKILL.md:28`, `one-pager-composer — SKILL.md:36`, `decision-memo-composer — SKILL.md:36` — `*_drafted` event payloads put `project_id` in `data` → top-level `primary_thread_id`.
- `stalled-projects — SKILL.md:21,193` — Writer Contract filter description + `StallFlag` example use `project_id` → `primary_thread_id` / `thread_id` (match `stall_detector.py` TypedDict).
- `shared/scripts/stall_detector.py:210` — **code, not prose:** `_scan_last_activity` reads `data.get('project_id') or data.get('primary_thread_id')` — both nested under `data`. Canonical `primary_thread_id` is **top-level**. Fix to read top-level. **(Ship-blocker — the one RP2 code-layer fix; every stall run currently ignores the event log.)** (`CONFIRMED_SHIP_BLOCKERS.md:312-314`)
- `shared/scripts/build_workspace_map_input.py:107` — `_project_org_id()` reads `org_id` before canonical `affiliation_id` → flip precedence to `affiliation_id` first.

**Safe migration order (RP2):**
1. Fix `stall_detector.py:210` and `build_workspace_map_input.py:107` first (code layer, directly observable via existing script tests).
2. Fix the **scheduled orchestrators** next (`orchestrator-dont-forget.md` especially) — these auto-fire daily and cause the worst silent damage (auto-archival).
3. Fix the high-frequency skill prose (`workspace-manager`, `people-crm`, `insight-generator`).
4. Fix the composer event payloads (memo/one-pager/decision-memo/calendar) and `decision-log` — lowest urgency (readers use the dual-layer `event_refs.threads_of()` helper, so impact is "thin," not broken).
5. No backfill: the open schema tolerated the old writes; canonical readers already dual-scan. Forward-looking only.

**The ONE regression test for RP2:**
A static scanner asserting **the string `primary_project_id` appears in zero SKILL.md / reference `.md` files**, and that `project_id` appears only inside an explicitly whitelisted deprecated-compat context. Pair with a code assertion that every `event_refs` / writer helper reads `primary_thread_id` at top level. This single grep-class invariant catches the entire family.

**Effort: M** (≈35 findings, fully mechanical once the canonical field is fixed in mind; the only code fixes are two scripts.)

---

### RP3 — Project status values outside the entities enum

**Canonical project status enum** (`entities.schema.json:172`): `active | dormant | paused | blocked | archived`. Nothing else. (`stage` is a **separate integer 0–5 field** — see the stage cross-cutting note.)

**Confirmed findings — phantom status values:**

- `board-pack-assembler — SKILL.md:50` — reads `active/at-risk/paused`; `at-risk` is not in the enum → replace with the real values; **`blocked` and `dormant` projects are currently silently omitted** from the board pack roll-up. (Ship-blocker, `CONFIRMED_SHIP_BLOCKERS.md:48-50`.)
- `enable-command-room-schedules/references/orchestrator-dont-forget.md:660` — "N resolved" action writes `status: 'resolved'` → write `archived` (the intended terminal state). **(Ship-blocker #10.)**
- `list-active — SKILL.md:38,155` — filters out `status: completed` → remove the dead `completed` filter (no project can hold it); align suffix rendering.
- `list-active — SKILL.md:57` — groups by `scope: advisory` / `relationship_type: advisor` → use canonical org enum values (`advisor` is valid relationship_type; confirm `scope` value against schema).
- `stalled-projects — SKILL.md:30,45` + `stall_detector.py:81,337` + `stalled_projects_config.schema.json:5,20` — `exploring` used as a status → **decide once**: either (a) add `exploring` to the `entities.schema.json` status enum (it is already a live entry state per `ORG_AND_THREAD_MODEL` lifecycle and `thread_writer.py` accepts it via its superset), or (b) strip it everywhere. **Recommended: add `exploring` to the schema enum** — it is real lifecycle state, and 6+ code/doc sites already assume it; stripping is more churn than adding. This also resolves the `stall_detector.py:81` and `workspace-ingest/openai-export-parser.md:200,212` mismatches.
- `workspace-ingest — SKILL.md:432` + `custom-markdown-parser.md:100,139` — org `scope: 'vendor'` not in org.scope enum (`holding|operating|division|...`) → map to canonical scope; **the relationship is "vendor", which belongs in `relationship_type`, not `scope`.**
- `workspace-ingest — SKILL.md:432` + `custom-markdown-parser.md:102` — org `relationship_type: 'referral'` not in enum → map to canonical (`referral` → likely `prospect` or a new approved value; confirm against `DATA_CONTRACT.md:188` which is *also* stale and missing `vendor`/`prospect`/`service_provider`).
- `workspace-ingest/references/custom-markdown-parser.md:82` — person `status: 'placeholder'` not in person.status enum → use canonical (`active`/a documented placeholder convention).
- `workspace-ingest/references/v1x-parser.md:137` — Title-Case commitment `data.status` `'Open'`/`'Partial'` → lowercase canonical (`open`/`partial`) that `cru_match.load_open_commitments` recognizes. **(Ship-blocker — migrated v1.7/v1.8 workspaces silently lose all Open/Partial commitments.)** (`CONFIRMED_SHIP_BLOCKERS.md:342-344`)

**Cross-cutting (RP3-adjacent) — the `stage` field type contradiction:**
- `ORG_AND_THREAD_MODEL.md:92` documents `stage` as a **string** enum (`"stage": "active"` // `active|dormant|...|exploring`), but `entities.schema.json` defines `stage` as an **integer 0–5**. **(Ship-blocker, `CONFIRMED_SHIP_BLOCKERS.md:9-11`.)** Every `workspace-ingest` run writes string values into the integer `stage` field (coerced to `null`). **Fix the reference doc** to show `stage` as the integer it is, and confirm `workspace-ingest`/`openai-export-parser.md:200,212` writes integers. (`stage` has no downstream readers today, so the runtime blast radius is low, but the doc is actively misleading the parser.)

**Safe migration order (RP3):**
1. Decide the **`exploring` add-vs-strip** question first (recommend add) — it gates ~6 sites.
2. Fix `entities.schema.json` (add `exploring` if chosen) and `DATA_CONTRACT.md` enums (add the missing `vendor`/`prospect`/`service_provider` relationship_types) — schema/doc first.
3. Fix the **write paths** that emit invalid values (`orchestrator-dont-forget.md:660` `resolved`, `v1x-parser.md:137` Title-Case, `workspace-ingest` scope/relationship/status) — these actively corrupt data.
4. Fix the **read/filter** paths (`board-pack-assembler:50`, `list-active:38`) — these silently omit, less corrupting.
5. Fix `ORG_AND_THREAD_MODEL.md:92` stage doc.
6. **Backfill consideration:** workspaces already migrated via `workspace-ingest`/`v1x-parser` may hold invalid `vendor`/`resolved`/Title-Case values. A one-time `cleanup`-driven normalization pass is advisable (out of scope for the prose fix, but flag for a follow-up session).

**The ONE regression test for RP3:**
A scanner that **extracts every project-status / org-scope / org-relationship_type / person-status / commitment-status string literal from SKILL.md, reference `.md`, and the config schemas, and asserts membership in the corresponding `entities.schema.json` enum** (post-`exploring` decision). One invariant covers every phantom-status finding.

**Effort: M** (≈20 findings; the `exploring` and `stage`-type decisions need judgment, the rest is mechanical.)

---

### RP4 — Real person/org names leaking past the name-scanner

**Approved placeholder list** (from findings): `Sam, Bo, Rio, Skyler, Mira, Aria, Bowie, Lyra, Quinn, Dustin, Adan` (people); `Northstar Partners`, `Acme Co` (orgs). Anything else that is a real person/org is a leak.

**Confirmed real names to purge** (from CHANGELOG cross-reference, these are confirmed real customers/contacts, not placeholders): **People —** `Matt`/`Matthew`, `Drew`, `Tate`, `Colton`, `Jeff`, `Pierce`, `Andrea (Wetsel)`, `Amir`, `Marcus`, `Rae`, `Rakesh`, `Sloan`, `Wendy`, `Blake`, `Gary`, `Pioneer`, `Joss`, `Charlie`. **Orgs —** `Tamer Designs`, `Wetsel Brothers`, `Apex Advisory`, `Design Trends Income`, `Duke Real Estate Group`, `The Link`, `The Crescent`, `Imperial Valley Mall`, `Finger Lakes Mall`, `Aspen Hardware`, `CHS Limelight`, `Chaletteholdings`, `Northstar Inc` (→ `Northstar Partners`), `Pioneer`.

**Ship-blocker leaks (hot-path / customer-visible — fix first):**

- `email-writer — SKILL.md:131,222,227,363,381,391,405` — `Matt` / `—Matt` / `Gary` sign-offs and labels → approved placeholder (`—Sam`). **Functional defect: default voice signs customer drafts as Matt.**
- `follow-up-ritual — SKILL.md:252,274,288` — `—Matt` sign-off rule + 2 examples → `—Sam`.
- `enable-command-room-schedules/references/orchestrator-commitments.md:595,712,661,662,467,354,468` — `Matt`, `Wendy`, `Sloan`, `Rakesh` in the verbatim-executed prompt body → placeholders. **(Loaded into context every commitments fire.)**
- `inbox-triage — SKILL.md:65,75` — `Colton`, `Tamer Designs`, `$300K`, `matthew@chaletteholdings...` in MUST-language gate → placeholders + fictional values. **(Top-10 #6.)**
- `dormant-customer-scan — SKILL.md:24,59` — `Drew`, `Pioneer`, `Jeff`, `Design Trends Income` in hot-path "For:" preamble → placeholders.
- `insight-generator — SKILL.md:335,480,481` — `Blake`, `Wetsel Brothers`, `Apex Advisory` in proposed-projects/orgs example tables (model can echo into live output) → placeholders.
- `report-bug/references/known-issue-patterns.md:3,110,163` — `Matthew` ×3 in loaded reference → "the maintainer".
- `enable-quick-commands/references/quick-commands-artifact.html:262` — **"drafts a Gmail to Matthew"** rendered in the Cowork sidebar for every customer → generic copy. **(Only RP4 leak that renders to a live customer surface.)**
- `enable-command-room-schedules/references/SHARED_CHAT_OUTPUT_PROTOCOL.md:398` — verbatim transcript naming `Tate`, `Duke Real Estate Group`, `The Link`, `The Crescent`, `Imperial Valley Mall`, `Finger Lakes Mall` → replace the entire example with a fictional one. **(Largest single-location PII cluster.)**
- `enable-command-room-schedules/references/orchestrator-dont-forget.md:512,531` — `Andrea` / `Andrea Wetsel` as REVIEW-table and code-block `name` value (renderer-shaped) → `Mira Sample`.
- `shared/CHAT_ACTION_WIDGET.md:207`, `shared/CONTRACT.md:245,254`, `shared/FUZZY_ROUTER.md:151` — `Drew` in shared protocol prose → placeholder.
- `workspace-manager/references/maintenance-rules.md:75` — `Pierce` → placeholder.

**Polish leaks (prose-only, not rendered — fix in bulk):** the remaining ~50 occurrences across `board-pack-assembler:166`, `command-room-coach:146` (`Amir`), `email-writer:131,222,363`, `intro-broker:183` (`Matthew`), `meeting-notes:291,333` (`Drew`,`Pierce`), `weekly-recap:42,188` (`Marcus`), `workspace-manager:542` (`Rae`), `scan-for-commitments:184` (`Joss`), `inbox-triage:265` (`Charlie`), `follow-up-ritual:67,192` (`Drew`,`Charlie`), `enable-quick-commands:77` (`Drew`,`Tate`), all the `orchestrator-*` privacy-names entries (`Tate`,`Pierce`,`Rakesh`,`Sloan`,`Adan`,`Aspen Hardware`,`CHS Limelight`), `ORG_AND_THREAD_MODEL.md:192`, `PLUGIN_BOUNDARY.md:84`, `live_contact_check.py:16` docstring, and the test fixtures `tests/run_v2_14_38_actions_test.py:107,250` (`Andrea Wetsel`). One-line fix each: replace with an approved placeholder.

**Safe migration order (RP4):**
1. **Customer-rendered first:** `quick-commands-artifact.html:262`, then all composer sign-offs (`email-writer`, `follow-up-ritual`, `orchestrator-commitments`) — these reach end users.
2. **Hot-path prose** loaded every fire (`inbox-triage` gate, `dormant-customer-scan` preamble, the orchestrator verbatim prompts).
3. **Renderer-shaped examples** the model can echo (`insight-generator` tables, `orchestrator-dont-forget` REVIEW table/code block).
4. **Shared protocol + reference prose** (CONTRACT, CHAT_ACTION_WIDGET, FUZZY_ROUTER, ORG_AND_THREAD_MODEL).
5. **Pure docstrings + test fixtures** last.
6. No ordering hazard — every fix is an independent text substitution.

**The ONE regression test for RP4:**
**Extend the name-scanner to run over SKILL.md prose and all reference `.md`/`.html` files, not just `.docx` render output.** Concretely: a scanner that greps every shipped `skills/**` and `shared/**` text file for any name **not** on the approved placeholder allowlist (seed the denylist from the confirmed-real list above + CHANGELOG full-name extraction). This is the literal closure of the root leak for RP4 ("real names sitting in instruction text ship untouched because the scanner only scans `.docx`"). Also **fix `docx_leak_scanner.py:75`** while here — it forbids the legitimate word `stakeholder`, which is a false-positive that breaks board-pack/operator-report `.docx` output (`CONFIRMED_POLISH.md:231-233`).

**Effort: L** (≈75 occurrences, all trivially mechanical, but high volume and must be exhaustive — a single missed name re-opens the leak. The scanner is the real deliverable.)

---

### RP5 — Stale references to retired features

**Retired and their replacements:** `weekly-audit` → `cleanup`; `VOICE_SAMPLES.md` (retired v2.7.1/v3.0) → per-skill `## Voice Block`; `Commitment Cockpit`, `Pay Attention To`, `Meeting Processor` → never shipped / not installable; old action-token formats → v2.14.38+ handler tokens.

**Confirmed findings:**

- `README.md:43,69` — lists "Weekly Audit" as a live skill with score/dashboard/quick-audit semantics → replace with `cleanup`. **(Ship-blocker — primary onboarding doc; sets false expectations for every new customer.)** (`CONFIRMED_SHIP_BLOCKERS.md:15-17`)
- `inbox-triage — SKILL.md:17,95,303,327` — reads retired `_hq/VOICE_SAMPLES.md` at 4 sites → read the skill's `## Voice Block` instead. **(Ship-blocker — every drafted reply uses stale/no voice calibration; `inbox-triage` is the only composer never migrated off VOICE_SAMPLES.)** (`CONFIRMED_SHIP_BLOCKERS.md:201-203`)
- `cleanup — SKILL.md:18,130` — instructs `brief_writer.py` for its `.docx`, but `brief_writer.py:465-482` `eyebrow_by_kind` has no `cleanup` key (only stale `weekly_audit`) → **add a `cleanup` entry to `brief_writer.py`** (code fix) so the report renders. **(Ship-blocker — cleanup `.docx` either ValueErrors or mislabels as "WEEKLY AUDIT".)** (`CONFIRMED_SHIP_BLOCKERS.md:84-86`)
- `command-room-update-bridge — SKILL.md:826` — Phase 6 completion message offers retired `Commitment Cockpit` / `Pay Attention To` / `Meeting Processor` via "level up" → remove the dead add-on references. (`CONFIRMED_POLISH.md:183-185`)
- `operator-report — SKILL.md:94` — counts retired `weekly_audit_run` → count the canonical cleanup event (coordinate with RP1 `cleanup_run` decision).
- `command-room-onboarding — SKILL.md:61` — past-meetings listed "9 AM weekdays"; canonical default is 5 PM (`schedule_config.py`) → fix the table. (`CONFIRMED_POLISH.md:162-164`)
- Stale action-token formats in `orchestrator-dont-forget.md:605,607,608` — `[a/b/c] confirm/edit/skip` and `[d1] snooze/skip` tokens have no handler post-v2.14.38 → update to the live token set (`:664` handler). **Customer-facing: clicking these tokens hits the unrecognized-input fallback.** (`CONFIRMED_POLISH.md:588-593`)
- Stale `present_files` single-surface design refs in `orchestrator-past-meetings.md:506,603` and `orchestrator-upcoming-meetings.md:307` → align to v3.13.0 default=skip (else file cards appear that don't open on click). (`CONFIRMED_POLISH.md:645-647`, `:657-659`)
- Dev/contributor docs (lower priority, no end-user impact): `README_V2_BUILD.md:71`, `shared/data-schemas/README.md:91`, `references/DATA_CONTRACT.md:237`, `shared/PLUGIN_BOUNDARY.md:37` — all reference retired `weekly-audit`/`VOICE_SAMPLES.md` → update to `cleanup` / Voice Block.

**Safe migration order (RP5):**
1. `README.md` and `cleanup` `brief_writer.py` entry first (customer onboarding + a hard ValueError).
2. `inbox-triage` VOICE_SAMPLES migration (every reply draft affected).
3. Customer-facing stale tokens (`orchestrator-dont-forget` action tokens, `present_files` surfaces, onboarding schedule).
4. Contributor docs last.

**The ONE regression test for RP5:**
A scanner asserting **the strings `weekly-audit`, `weekly_audit_run`, `VOICE_SAMPLES.md`, `Commitment Cockpit`, `Pay Attention To` appear in zero shipped skill/shared files** (allowlist any deliberate "retired:" historical note). A retired-feature denylist is the cheapest durable guard.

**Effort: S–M** (≈20 findings; 3 are code/onboarding judgment, rest are mechanical denylist hits.)

---

### RP6 — Render-path / draft-model regressions

**Two sub-families:** (a) **eager Gmail draft** — drafts must be created lazily (at widget-apply time), per `EMAIL_DRAFT_PROTOCOL.md` §1; (b) **render-path contradictions** — composers must render `.docx` via `brief_writer.py make_brief(...)`, never the raw `docx` skill, and mandatory phases must not be empty.

**Confirmed findings:**

- `follow-up-ritual — SKILL.md:104` — Step 5 "Create Gmail drafts" unconditionally before the widget → move draft creation to apply-time (lazy). **(Top-10 #3.)**
- `inbox-triage — SKILL.md:253-256` — `send`/`draft` act on an "eager-created `gmail_draft_id`" → lazy-create on apply. **(Top-10 #2.)**
- `follow-up-ritual — SKILL.md:192,193,207-219` — Output Structure template embeds a `## Drafted Emails` section with full email bodies inside the `.docx`, contradicting v3.13.0 ("`.docx` is recap-only; emails live in the chat-action widget") → remove the embedded-email section from the template. (`CONFIRMED_POLISH.md:399-404`)
- `one-pager-composer — SKILL.md:92 vs 208,211,213,223,229` — Step 5 says render via `brief_writer.py make_brief(brief_kind="one_pager")`; Gotchas says "Always invoke `docx` skill explicitly" → delete the contradicting Gotchas instruction; `brief_writer` is canonical (loses Calibri/navy hierarchy otherwise). **(Ship-blocker, `CONFIRMED_SHIP_BLOCKERS.md:222-224`.)**
- `memo-writer — SKILL.md:126-128` — **Phase 5 ("Log event + correction detection") is an empty heading + `---`.** The `memo_drafted` event write and the decision-log auto-fire chain were never implemented → write the Phase 5 body. **(Memo activity is invisible to operator-report / morning-briefing / weekly-recap; decision_doc memos never chain to decision-log.)** (`CONFIRMED_POLISH.md:519-527`)
- `dormant-customer-scan — SKILL.md:30,178` — `.md` fallback deliverable path (`_hq/insights/DORMANT_CUSTOMERS_[date].md`) violates the post-v3.13.0 `.docx`-deliverable policy → route fallback through `brief_writer`. **(Ship-blocker, `CONFIRMED_SHIP_BLOCKERS.md:108-110`.)**
- Body-size render risks (`orchestrator-dont-forget.md:437`, `orchestrator-inbox.md:401`) — `original_thread.body` first ~800 chars with no empty-by-default override → apply the v3.13.7 body-empty default to avoid transmission-ceiling failures on "show more" fires. (`CONFIRMED_POLISH.md:582-584`, `:630-632`)

**Safe migration order (RP6):**
1. **Eager-draft fixes first** (`inbox-triage`, `follow-up-ritual`) — these write to the customer's real Gmail; highest trust-damage.
2. `memo-writer` Phase 5 (write the missing implementation) — restores event-graph visibility for an entire skill.
3. Render-path contradictions (`one-pager-composer`, `follow-up-ritual` template, `dormant-customer-scan` fallback).
4. Body-size overrides last.

**The ONE regression test for RP6:**
A behavioral assertion via `synthetic-workspace-runtime-test`: **run each composer/email skill against a fixture with a Gmail connector present, and assert that no `create_draft` MCP call occurs before the chat-action widget is surfaced** (catches the whole eager-draft family), **and** a static check that every composer's render step references `brief_writer.make_brief` with no competing "invoke `docx`" instruction and no empty `Phase N` heading (catches the render-path family). Two assertions, one test harness, the whole pattern.

**Effort: M** (≈12 findings, but `memo-writer` Phase 5 is net-new content and the eager-draft fixes require careful re-sequencing of the apply flow — not pure find-and-replace.)

---

### RP7 — Show-then-tune violations (output gated behind questions)

**Canonical pattern:** produce a first draft/output immediately from available substrate, *then* offer to tune. Never block the first output behind a questionnaire. Skip any question whose answer is inferable.

**Confirmed findings:**

- `decision-memo-composer — SKILL.md:59-93` — Phase 1 asks up to 4 framing questions + Phase 2 criteria-weighting, all before any draft → **invert: draft from substrate first** (even when the trigger already names options like "hire now vs Q4 vs defer"), then offer to refine weights. **(Ship-blocker ×3 — the densest RP7 offender; `CONFIRMED_SHIP_BLOCKERS.md:90-98`.)**
- `board-pack-assembler — SKILL.md:202` — first-use bootstrap blocks on a 5-question KPI wizard before any output → produce a best-effort pack from substrate, surface the KPI gap as a tunable afterward. (`CONFIRMED_POLISH.md:51-53`)
- `contract-review — SKILL.md:68-73` — Phase 0 binary "set up standard terms (6-question wizard) or skip?" before any review → review the contract first, offer the terms-setup after. (`CONFIRMED_POLISH.md:195-197`)
- `scaffold-automation — SKILL.md:86-94` — Phase 3 asks 2-3 scoping questions ("Which Gmail account? Which Sheet? Every match or daily batch?") before generating artifacts → infer from connectors/BUSINESS_CONTEXT where possible, generate a draft scaffold first, then confirm the genuinely-ambiguous ones. (`CONFIRMED_POLISH.md:759-764`)

**Safe migration order (RP7):**
1. `decision-memo-composer` first (highest blocking severity, 3 ship-blocker confirmations).
2. `board-pack-assembler`, `contract-review`, `scaffold-automation` — independent, any order.
3. No data implications — these are control-flow prose rewrites within each SKILL.md.

**The ONE regression test for RP7:**
A behavioral assertion (via `synthetic-workspace-runtime-test`, per skill in a denylist): on first invocation against a cold/minimal workspace, **assert the skill's first surfaced turn contains rendered output (a draft, a brief, a review), not solely a question block.** This is judgment-adjacent (an LLM-graded "did it show before it asked?" check fits the `compare-canonical-vs-freelance` ladder), so it needs a workflow harness rather than a pure grep.

**Effort: S–M** (only 4 skills, but each needs a careful prose re-flow and a judgment call on which questions are truly inferable.)

---

### RP8 — Advisory-not-mechanical enforcement gates

**Canonical pattern:** an enforcement step that says "do X" in prose only is *advisory* and will silently no-op when its dependency is missing. Two required mechanical gates: (a) a **bash pre-flight import check** (`python3 -c "from <writer> import ...; print('OK')"`) before any auto-write path, that aborts on failure; (b) name-bearing triggers must call `entity_resolve.py::resolve_all()`, never read `aliases.json`/`entities.json` directly (per `ENTITY_RESOLVE_PROTOCOL.md`).

**Confirmed findings:**

- `enable-command-room-schedules/references/orchestrator-dont-forget.md:292-294` — Pulse Phase 5 HIGH-confidence auto-apply says "Write directly to entities.json via people-crm" in prose with **no pre-flight `people_writer.py` import check** → add a bash abort gate. **(Ship-blocker — Pulse auto-writes entity updates 9 AM daily with no mechanical guard if `people_writer.py` is unavailable; `CONFIRMED_SHIP_BLOCKERS.md:249-251`.)**
- `team-intelligence — SKILL.md:123,209` (+ `:1-20` no protocol reference) — `1:1 prep` / `what's [name] working on` / `log commitment for [name]` resolve names by reading `aliases.json`/`entities.json` directly, **bypassing the mandatory `entity_resolve.py` gate** → add the `ENTITY_RESOLVE_PROTOCOL` preamble + `resolve_all()` call. **(Ship-blocker — two reports sharing a first name silently misroute; `CONFIRMED_SHIP_BLOCKERS.md:324-326`.)**
- `call-prep — SKILL.md` (no `entity_resolve` reference) — resolves attendees/projects from loose trigger text with no `ENTITY_RESOLVE` preamble → add it (it is in the protocol's "Skills covered" list but doesn't comply). (`CONFIRMED_POLISH.md:90-92`)
- `orchestrator-historical-backfill.md:55` — Phase 3 appends provisional person records as raw JSON with schema-forbidden fields (`inferred_from`, `pending_review`, `first_seen`) instead of going through `people_writer.py` → route through the writer (mechanical), which also fixes the forbidden-field problem. **(Ship-blocker — a 12-month backfill bulk-writes 500–2000 malformed records; `CONFIRMED_SHIP_BLOCKERS.md:261-263`.)**
- `transcript-search — SKILL.md:243-245` — Step 5.5 reconcile pass "swallow errors silently and continue" → at minimum log a surfaced event so dropped persons/orgs are recoverable (advisory error-swallow is the same anti-pattern). (`CONFIRMED_POLISH.md:897-899`)
- Auto-apply-without-surface variants (`orchestrator-dont-forget.md:274` org-layer drift auto-apply) — same class: silent reclassification with only a one-liner surface → require the pre-flight check + a visible audit event.

**Safe migration order (RP8):**
1. `orchestrator-dont-forget.md:292-294` pre-flight gate first (daily auto-write, no guard).
2. `orchestrator-historical-backfill.md:55` writer-routing (bulk corruption risk on the backfill path).
3. `team-intelligence` + `call-prep` ENTITY_RESOLVE compliance.
4. `transcript-search` error-swallow + org-drift auto-apply.

**The ONE regression test for RP8:**
A static assertion that **every SKILL.md / orchestrator with an auto-write or auto-apply path contains a bash pre-flight import-check block before that path, and every skill listed in `ENTITY_RESOLVE_PROTOCOL.md` "Skills covered" contains a `resolve_all(` call and contains no direct `aliases.json` / `entities.json` read for name resolution.** Two greppable invariants, sourced from the protocol's own coverage list.

**Effort: M** (≈10 findings; adding mechanical gates is more than text substitution — each needs the correct import path and abort semantics — and the backfill writer-routing is a structural change.)

---

### Trigger collisions

**Canonical pattern:** two skills sharing a positive trigger must have an explicit DOES-NOT guard in the lower-priority skill (per `FUZZY_ROUTER.md` conventions).

**Confirmed findings:**

- `workspace-manager/SKILL.md:3` vs `cleanup/SKILL.md:3` — both claim positive triggers `'deep clean'` and `'maintenance'`; no DOES-NOT guard → add an explicit DOES-NOT-FIRE-ON `'deep clean'`/`'maintenance'` clause to `workspace-manager` routing it to `cleanup` (the actual tidy sweep). Without it, "deep clean" lands in `workspace-manager`'s generic status response and the customer gets no cleanup. **(Only confirmed collision; `CONFIRMED_POLISH.md:948-950`.)**

**The ONE regression test for trigger collisions:**
A `cross-skill-interaction-test` (the harness already exists) assertion that **builds the union of all positive trigger phrases across all SKILL.md files and flags any phrase claimed by ≥2 skills that lacks a reciprocal DOES-NOT guard.** This generalizes the single finding into a standing invariant.

**Effort: S** (one fix; the value is the standing collision-detector test.)

---

## 3. Sequencing

### Pure-mechanical bulk fixes — suited to an autonomous `/goal` grind

These are find-and-replace against a known canonical value, low judgment, high volume. Hand them to an autonomous grind with the relevant regression test as the acceptance gate:

- **RP2** (deprecated field → `primary_thread_id`) — almost entirely mechanical once the two script fixes are made. *Grind candidate #1: well-bounded, single canonical target, ~35 sites.*
- **RP4** (name purge) — mechanical substitution against the approved-placeholder allowlist, ~75 sites. *Grind candidate #2, but ONLY after the prose-layer scanner exists* — the scanner is both the acceptance gate and the guard against a missed name re-opening the leak.
- **RP1 renames** (the ~70% of RP1 that maps to an existing canonical type) — mechanical, *but* must run **after** the enum-additions commit lands (so the schema is a superset first).
- **RP3 read/filter fixes** and **RP5 denylist hits** — mechanical substitution.

### Need human judgment or a workflow fan-out

These carry a decision or net-new content and should be operator-driven (or a `verify-cr-release`-style fan-out with paste-back), not a blind grind:

- **RP1 add-vs-rename decisions** — per genuinely-new type (cleanup_run, schedule_config_changed, the 8 release_* types, disambiguation pair, artifact_refreshed, bug_self_fixed, project_loaded_deep). One human pass to decide add-vs-collapse-vs-rename, then the rest is mechanical. **This decision blocks RP1 renames and the operator-report fallback — do it first.**
- **RP3 `exploring` add-vs-strip** and the **`stage` integer-vs-string** correction — schema-shape judgment; blocks ~8 sites.
- **RP6** — `memo-writer` Phase 5 is net-new implementation; the eager-draft fixes re-sequence the apply flow. Needs care + behavioral verification.
- **RP7** — control-flow re-flow per skill; "is this question truly inferable?" is a judgment call. Fan out across the 4 skills.
- **RP8** — adding correct pre-flight import-check blocks + writer-routing is structural, not textual.
- **Trigger collision** — trivial fix, but worth a human eye on routing intent.

### Recommended order of attack

**Wave 0 — Schema + decisions (blocks everything; one focused session).**
1. Make the **`events.schema.json` enum additions** (RP1 add-set) and the **`entities.schema.json` `exploring` decision** + **`stage` doc correction** (RP3). Update `DATA_CONTRACT.md` enums + the `note` shape. This makes the schemas supersets so no downstream rename breaks data.

**Wave 1 — Stop the active bleeding (ship-blockers that corrupt data or leak to live surfaces; operator-driven).**
2. **RP2 scheduled-orchestrator fixes** — `orchestrator-dont-forget.md:149,171,290` (auto-archival) first, then `:158,658,660` + the `org_id` reads, then `stall_detector.py:210` + `build_workspace_map_input.py:107`. *This is the single most damaging finding in the corpus.*
3. **RP6 eager-draft fixes** — `inbox-triage`, `follow-up-ritual` (real Gmail writes).
4. **RP3 invalid-write fixes** — `orchestrator-dont-forget.md:660` `resolved`, `v1x-parser.md:137` Title-Case, `workspace-ingest` scope/relationship/status.
5. **RP4 customer-rendered leaks** — `quick-commands-artifact.html:262`, composer sign-offs, `inbox-triage`/`dormant-customer-scan` hot-path prose, `SHARED_CHAT_OUTPUT_PROTOCOL.md:398`.
6. **RP8 daily auto-write gate** — `orchestrator-dont-forget.md:292-294` pre-flight check; **RP8 backfill** writer-routing.

**Wave 2 — Restore silently-broken output (ship-blockers that empty sections; mixed.)**
7. **RP1 renames** — board-pack Wins, call-prep/upcoming-meetings decisions, team-intelligence commitments, the `person_record_update` family. (`cleanup` `brief_writer.py` entry — RP5 — fits here too.)
8. **RP2 remaining prose** — `workspace-manager`, `people-crm`, `insight-generator`, composer payloads.
9. **RP6 render-path** — `one-pager-composer` contradiction, `memo-writer` Phase 5, `dormant-customer-scan` `.md` fallback.
10. **RP8 ENTITY_RESOLVE** — `team-intelligence`, `call-prep`.

**Wave 3 — Autonomous `/goal` grind (mechanical, gated by the new scanners).**
11. **RP4 polish leaks** (the ~50 prose-only names) — *grind, gated by the prose-layer name-scanner.*
12. **RP3 read/filter** + **RP5 denylist** + remaining **RP2 composer payloads** — grind, gated by the static enum/field scanners.

**Wave 4 — Judgment fan-out (parallel, operator/verify-loop).**
13. **RP7** across the 4 skills; **trigger collision** fix; contributor-doc RP5 cleanup.

**Wave 5 — Lock it in (the whole point).**
14. Land the **8 regression tests** (one per pattern + collisions) into `bug-regression-suite` and wire the two runtime guards (`integrity_check.py` enum validation at append; name-scanner over prose). Without these, the prose re-drifts and the same 301 findings regrow.

---

## 4. Effort estimate

Per-pattern sizing (S = <½ day / single focused pass; M = ~1 session; L = multi-session or grind-plus-review):

| Pattern | Size | Driver of the estimate |
|---|---|---|
| **Wave 0: schema + decisions** | **M** | Few edits, but every add-vs-rename and the `exploring`/`stage` calls gate downstream work — must be deliberate. |
| **RP1** | **L** | ~80 findings. ~70% mechanical rename (grind), but the add-vs-rename decision set + the `note` shape + `seq` field need a human pass. |
| **RP2** | **M** | ~35 findings, single canonical target, mostly grind. Two code fixes (`stall_detector.py`, `build_workspace_map_input.py`) are the only non-trivial bits. |
| **RP3** | **M** | ~20 findings. The `exploring` add and `stage` integer correction carry schema-shape judgment; rest mechanical. Possible one-time data-normalization follow-up (separate). |
| **RP4** | **L** | ~75 occurrences, all trivial individually but must be exhaustive — and the real deliverable is the prose-layer scanner. Plus the `docx_leak_scanner.py:75` `stakeholder` false-positive fix. |
| **RP5** | **S–M** | ~20 findings; 3 carry judgment/code (`README`, `cleanup`→`brief_writer` entry, onboarding schedule), rest are denylist substitutions. |
| **RP6** | **M** | ~12 findings, but `memo-writer` Phase 5 is net-new content and eager-draft fixes re-sequence the apply flow — needs behavioral verification, not just edits. |
| **RP7** | **S–M** | 4 skills; each a careful control-flow re-flow + an "is this inferable?" judgment. Low count, non-trivial per-skill. |
| **RP8** | **M** | ~10 findings; adding correct pre-flight import-checks + writer-routing is structural, with the backfill path the heaviest. |
| **Trigger collisions** | **S** | One fix; value is the standing collision-detector test. |
| **Wave 5: 8 tests + 2 runtime guards** | **M–L** | The durable payoff. The prose-layer scanner (RP1/RP2/RP3/RP4/RP5) and the behavioral harness assertions (RP6/RP7/RP8) are net-new test infrastructure — budget accordingly. |

**Rough total:** 2 L-sized blocks (RP1, RP4) + ~5 M-sized blocks + the test-infrastructure block dominate. Plan for **Wave 0–1 as one operator-driven session each**, **Wave 2 as one session**, **Wave 3 as a single gated `/goal` grind**, **Wave 4 as a parallel fan-out**, and **Wave 5 as a dedicated hardening session** — call it **~6–8 working sessions** end to end, with the autonomous grind compressing the bulk of RP2/RP3/RP4/RP5 volume.

**Critical dependency to honor throughout:** schema/enum/doc changes (Wave 0) land **before** any rename or grind, and the two scanners (Wave 5) are what prevent regrowth — they should be built early enough to serve as the **acceptance gate** for the Wave 3 grind, even if the full test suite lands last.

---

### Critical files for implementation
- `C:/Users/asdas/.claude/plugins/marketplaces/commandroom1/command-room/shared/data-schemas/events.schema.json` — canonical event-type enum; the add-set lands here first (gates all of RP1).
- `C:/Users/asdas/.claude/plugins/marketplaces/commandroom1/command-room/shared/data-schemas/entities.schema.json` — canonical status/scope/relationship_type/stage enums (gates RP3); the `exploring` and `stage` decisions land here.
- `C:/Users/asdas/.claude/plugins/marketplaces/commandroom1/command-room/skills/enable-command-room-schedules/references/orchestrator-dont-forget.md` — single most damaging file: RP2 auto-archival (`:149,171,290`), RP3 `resolved` write (`:660`), RP8 missing pre-flight gate (`:292-294`), plus multiple RP4 leaks and stale tokens.
- `C:/Users/asdas/.claude/plugins/marketplaces/commandroom1/command-room/shared/scripts/brief_writer.py` — render-path canonical (RP6); needs the missing `cleanup` `eyebrow_by_kind` entry (RP5 ship-blocker) and is the target every composer must route to.
- `C:/Users/asdas/repos/chalette030/chalette/skills/bug-regression-suite/` — where the 8 new pattern-regression tests and the two prose-layer scanners (the actual root-leak fix) must be added.