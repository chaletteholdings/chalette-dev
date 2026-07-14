# Bug catalog — canonical regression test corpus

Every bug ever found in Command Room. Each entry is a permanent regression test that runs on every release. Never shrinks — only grows.

**Current size:** 61 entries (Bugs #1-#61 + Sub-bug #14b) — seeded from V3.13.7 verification session + prior month.

**Catalog growth principle:** every new bug surfaced in production gets a permanent entry here. The catalog is the structural defense against re-introducing fixed bugs.

---

## Tier 1 — SHIP-BLOCKER fixes (must pass every regression run)

### Bug #2 — Morning-brief carry-forward trust gap

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.7
**Modifies substrate:** false

**Prerequisite:** M has replied to at least one inbox thread today.

**Trigger:** `morning brief`

**Expected pass signals:**
- Replied threads NOT surfaced as "ball is on you" / "needs reply"
- Each carry-forward item gets `get_thread(messageFormat=FULL_CONTENT)` re-verification
- Latest-sender direction check fires per Step 3c MUST-language gate

**Expected fail (regression):**
- Bob-Chilton-class miss: thread you replied to still flagged as owing you
- Cached carry-forward without latest-sender re-check

---

### Bug #4 — Email-writer widget cascade missing + eager Gmail draft

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.7 (partial — canonical path) + v3.13.8 §2.1 + §2.12 (freelance path)
**Modifies substrate:** true (Gmail draft if user clicks send/draft)
**Cleanup:** delete any Gmail drafts created during test fire

**Trigger:** `draft email to [test recipient — use placeholder Bo Sample at bo@example.com]`

**Expected pass signals:**
- Widget renders BEFORE any Gmail tool call
- 4 canonical actions: `send / edit then send / draft / skip`
- Gmail Drafts folder unchanged until user clicks send/draft
- Approval-gate language: "Gmail draft fires on click" or similar

**Expected fail (regression):**
- Gmail draft appears in Drafts folder before user clicks
- Silent Gmail write
- Widget never renders

---

### Bug #5 — Pulse Calendar half live-check

**Mode:** regression
**Severity:** SHIP-BLOCKER (Bug #28 family)
**Fixed in:** v3.13.7 (Calendar half added to live_contact_check.py)
**Modifies substrate:** false

**Trigger:** fire scheduled task `pulse` (open the Pulse chat in Cowork sidebar + trigger)

**Expected pass signals:**
- Calendar API called via `live_contact_check.py` 
- Contact with recent calendar meeting NOT flagged as going-dark
- max(substrate, gmail, calendar) overlay logic fires

**Expected fail (regression):**
- Calendar-heavy contact (board members, recurring 1:1s) false-flagged as dormant
- Only Gmail check fires (no Calendar half)

---

### Bug #11 — entity_resolve consumer enforcement

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.7 (3 skills) + v3.13.8 §2.6 (10 skills total)
**Modifies substrate:** false

**Trigger:** `who is Eliyahu` (or any misspelled-but-recognizable name not in aliases)

**Expected pass signals:**
- entity_resolve.py::resolve_all() invoked
- Tier 1 / 2 / 3 match returned
- "did you mean Elan?" disambiguation OR direct match
- No 4-clarifying-question storm

**Expected fail (regression):**
- Substring grep used (no resolver trace)
- 4-clarifying-question pattern
- Wrong person returned

---

### Bug #14 — Commitments widget transmission ceiling

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.7 (cap 16→7 + show-more + empty original_thread.body)
**Modifies substrate:** false (read-only fire)

**Trigger:** fire scheduled task `commitments` (open Commitments chat + trigger)

**Expected pass signals:**
- Widget renders cleanly, no error
- ≤7 items per page
- `show more` action for overflow
- Per-fire byte count ≤ 80KB

**Expected fail (regression):**
- "socket connection closed" error
- ≥11 items in one widget (cap not enforced)
- Widget bytes > 80KB

---

### Bug #19 — find_existing_person fuzzy-name match (single-token)

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.7
**Modifies substrate:** false (test_artifact create only on explicit user confirmation — user should cancel form to avoid residue)
**Cleanup:** if user accidentally creates person, archive with test_artifact flag

**Trigger:** `add a new person: Daniel`

**Expected pass signals:**
- Detects existing Daniels (Pourbaba, Spaeth, others)
- Surfaces disambiguation widget (Path B freelance form OR canonical disambiguation)
- REFUSES to silent-create

**Expected fail (regression):**
- Silent person creation
- Existing Daniel record updated with new context

---

### Bug #28 — dormant-customer-scan live-check

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.7 (shared/scripts/live_contact_check.py wired into Step 3)
**Modifies substrate:** false (read-only)

**Trigger:** `who went dark`

**Expected pass signals:**
- "Per the skill's mandatory live-check gate" or similar language
- live_contact_check.py invoked
- Contact with recent calendar meeting suppressed from dormant list (live-check overrides substrate-stale)

**Expected fail (regression):**
- Substrate-only scan (no live-check trace)
- Calendar-recent contact false-flagged as dormant

---

### Bug #32 — Renderer→show_widget byte-relay transport (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.1 (file-URI transport)
**Modifies substrate:** false

**Trigger:** any large widget render (e.g., `commitments` against accumulated workspace)

**Expected pass signals:**
- File-URI transport: `widget_transport.render_and_relay()` invoked
- `mcp__visualize__show_widget` receives `file_uri` parameter, NOT raw HTML
- No bypass-to-freelance even on large (>40KB) widgets

**Expected fail (regression):**
- Freelance HTML emitted (Cowork claims "I built a bespoke editable HTML card")
- Byte-relay through tool parameter
- Canonical render+validation discarded post-validation

---

### Bug #38 — Edit-then-send action handler dead on freelance widgets (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.12 (auto-resolves via §2.1)
**Modifies substrate:** false (just render check)

**Trigger:** `draft email to [Bo Sample]` → click `edit then send`

**Expected pass signals:**
- Inline multi-field editor opens (To/CC/Subject/Body)
- Edit fields populated with draft content
- Submit edits → Gmail draft updated

**Expected fail (regression):**
- "No response requested" empty reply
- No editor opens
- Action handler dead

---

### Bug #39 — chat_dismissal event NOT written from freelance skip (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.13 (auto-resolves via §2.1)
**Modifies substrate:** writes chat_dismissal event (legitimate; not test artifact)

**Trigger:** `draft email to [Bo Sample]` → click `skip`

**Expected pass signals:**
- chat_dismissal event written with 24h TTL
- Event type per EMAIL_DRAFT_PROTOCOL.md §4

**Expected fail (regression):**
- Silent no-op
- No chat_dismissal event in events.jsonl

---

### Bug #44 — Canonical renderer dead chrome (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.11 (6th validator gate + add_email_then_send verb)
**Modifies substrate:** false

**Trigger:** `draft email to [person who has no email on file — use placeholder Sky Sample with no email field]`

**Expected pass signals:**
- 6th validator gate fires → DataShapeError raised at render time
- OR widget renders with `add email then send` canonical recovery action
- NO dead Send button on placeholder string

**Expected fail (regression):**
- Live Send button on `(no email on file)` placeholder
- Renders happily, button clickable, send fails silently

---

### Bug #45 — Cross-skill entity_resolve enforcement (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.6 (10-skill audit)
**Modifies substrate:** false

**Triggers (multiple — one per affected skill):**
- `revive that thread with [misspelled name]` (thread-resurrection)
- `intro [misspelled1] to [misspelled2]` (intro-broker)
- `draft email to [misspelled name]` (email-writer)
- `schedule with [misspelled name]` (calendar-writer)
- `who went dark [near misspelled name]` (dormant-customer-scan)
- `morning brief` (morning-briefing — implicit via "ball is on you" name lookup)

**Expected pass signals (per skill):**
- entity_resolve.py invoked for each skill's name resolution
- ENTITY_RESOLVE_PROTOCOL preamble adherence
- No substring grep fallback unless resolver returns empty

**Expected fail (regression):**
- Substring grep used directly
- 4-clarifying-question storm
- Wrong-person resolution

---

### Bug #51 — show-my-list cascade-close to source commitment (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.9
**Modifies substrate:** true (commitment_resolved events)
**Cleanup:** none — closures are real-state changes M wants

**Sequence:**
1. Fire: `show my list`
2. Click `resolved` on a discuss-wrapper item (NOTE the source commitment seq from data.commitment_id)
3. Fire: `morning brief`
4. Verify underlying source commitment NOT in "you owe" count

**Expected pass signals:**
- TWO commitment_resolved events written: wrapper + source
- Morning brief excludes source from open list

**Expected fail (regression):**
- Only wrapper closed; source remains open in count

---

### Bug #52 — morning-briefing canonical helper enforcement (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER (M-impact)
**Fixed in:** v3.13.8 §2.10
**Modifies substrate:** false (read-only)

**Trigger:** `morning brief`

**Expected pass signals:**
- `cru_match.load_open_commitments()` invoked
- Defensive read skipped-lines surfaces to user if malformed events present
- No freelance manual scan with silent corruption masking

**Expected fail (regression):**
- Freelance scan + try/except silently filters corrupt lines
- skipped_lines warning NOT surfaced
- Count includes corrupted-event-derived data

---

### Bug #53 — brief_writer migration for .docx skills (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.3 (migrates 6 .docx skills to brief_writer)
**Modifies substrate:** true (writes events + creates .docx artifacts)
**Cleanup:** archive test .docx artifacts; mark events test_artifact=true

**Triggers (per skill — pick 1-2 to test):**
- `memo on a test topic — Bug #53 regression test`
- `one-pager on a test topic`
- `decision memo for test decision`
- `board pack` (against test fixture OR M's workspace)

**Expected pass signals (per .docx):**
- File saved at `[Project]/deliverables/[kind]/...`
- Document.xml contains canonical eyebrow (MEMO / ONE-PAGER / DECISION MEMO / BOARD PACK)
- Real Heading 1/2/3 styles (not all Normal)
- Universal post-render leak scan ran + clean

**Expected fail (regression):**
- docx-js hand-rolled output (no canonical eyebrow)
- All Normal-style paragraphs (Bug #7 regression)
- Leak in body (e.g., events.jsonl path leaking back per Bug #59)

---

### Bug #57 — Universal post-render leak scan (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.4
**Modifies substrate:** false

**Trigger:** `decision memo for any topic` → inspect resulting .docx for project_NNN / person_NNN / events.jsonl leaks

**Expected pass signals:**
- Scan invoked: `docx_leak_scanner.scan(output_path)` per brief_writer
- Output document clean of internal IDs / substrate paths / voice-forbidden tokens

**Expected fail (regression):**
- project_020 or similar leak in body
- Substrate paths visible
- Scan didn't run (false-clean per Bug #54 extract-text)

---

### Bug #58 — brief_writer table + matrix primitives (v3.13.8)

**Mode:** regression
**Severity:** SHIP-BLOCKER (blocks #53)
**Fixed in:** v3.13.8 §2.2
**Modifies substrate:** false

**Trigger:** `decision memo for test topic` (uses comparison matrix)

**Expected pass signals:**
- `add_table()` and `add_matrix()` primitives available in brief_writer
- Resulting .docx has actual tables (not flattened bullets)
- Star matrix visual present

**Expected fail (regression):**
- Matrices flattened to bullets
- No table primitive available
- Decision-memo composer falls back to docx-js (Bug #53 regression)

---

### Bug #59 — board-pack v3.13.2 leak fix regression (v3.13.8)

**Mode:** regression  
**Severity:** SHIP-BLOCKER
**Fixed in:** v3.13.8 §2.4 universal scan (auto-detects)
**Modifies substrate:** writes board_pack_assembled event (legitimate)

**Trigger:** `board pack`

**Expected pass signals:**
- Appendix C "Data sources" uses customer-friendly language ("your meeting records, your activity log") NOT substrate paths
- No `events.jsonl` / `entities.json` strings in body

**Expected fail (regression):**
- `(events.jsonl, entities.json)` substrate-path leak in Appendix C

---

### Bug #61 — pack_run telemetry orchestrator audit (v3.13.8)

**Mode:** regression
**Severity:** HIGH (Tier 2, but checkable)
**Fixed in:** v3.13.8 §3.9
**Modifies substrate:** writes pack_run events

**Trigger:** fire all 7 scheduled tasks (sequence)

**Expected pass signals:**
- Each fire writes pack_run event with data.kind populated
- No "unknown" kind values
- duration_ms populated

**Expected fail (regression):**
- 0-2 of 7 orchestrators write pack_run cleanly
- data.kind = "unknown" on multiple fires

---

## Tier 2 — HIGH-VALUE fixes (Bug #7, #30, #34, #40, #42, #43, #24, #49, #46, #48, #16, #60)

[Catalog continues with similar entries for each Tier 2 fix per V3.13.8_MASTER_PLAN §3. ~10 more entries.]

## Tier 3 — NICE-TO-HAVE fixes (Bug #1, #6, #8, #10, #12, #13, #15, #17, #18, #20, #21, #22, #26, #27, #29, #33, #35, #36)

[Similar entries. ~18 more.]

## Cross-skill sequences (multi-fire)

[Specific multi-fire sequences for bugs that require interaction between skills.]

## Adversarial entries (mode: adversarial)

### Adversarial #1 — Email to person with no email on file

(See Bug #44 — same trigger, but tests fix robustness over time)

### Adversarial #2 — Disambiguation with N+ name collisions

(See Bug #19 — but tests with N=3, N=4, N=5 collisions specifically)

### Adversarial #3 — Multi-write update-bridge migration

(See Bug #20 — fires full update-bridge against workspace with 8 malformed lines + missing brain_name + spaeth-not-canonical)

### Adversarial #4 — Commitments at 218+ items

(See Bug #14 — but tests with 250, 300, 500 items)

### Adversarial #5 — Corrupted events.jsonl with new malformed line shapes

(Seeds new malformed-line shapes: triple-comma, missing-quote, partial-unicode, etc. Tests Layer 2 defensive read tolerance breadth.)

### Adversarial #6 — Closure-reversal awareness

(Fire `revive thread with [person who has explicit closure event]` — expects Strength #20 to surface the closure before reviving.)

### Adversarial #7 — Voice-contract under pressure

(Fire stress-prone surfaces — weekly-audit, dormant-scan, operator-report — and run word-boundary leak scan on chat narration.)

[~25 more adversarial entries.]

---

## Catalog versioning

This catalog is versioned alongside chalette plugin. v0.6.0 = 61 entries (the v3.13.7 verification session output). Future versions grow this catalog as new bugs surface.

When adding entries:
1. Use the exact format above (Mode / Severity / Fixed in / Modifies substrate / Trigger / Expected pass / Expected fail)
2. Increment catalog version in the plugin.json
3. Append the entry at the appropriate tier (don't reorder existing entries — they're stable IDs)
