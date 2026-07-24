# Bug catalog — canonical regression test corpus

Every bug ever found in Command Room. Each entry is a permanent regression test that runs on every release. Never shrinks — only grows.

**Current size:** 66 entries (Bugs #1-#61 + Sub-bug #14b, Bug #104, Bug #105, integration-2026-07 F-08 / F-12 / F-15) — seeded from V3.13.7 verification session + prior month; grown per cycle.

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
- Detects existing Daniels (Sample, Stone, others)
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

### Bug #104 — mid-turn email drafts bypass email-writer (SPEC EW1)

**Mode:** regression
**Severity:** HIGH
**Fixed in:** SPEC EW1, post-v4.7.1 (workspace CLAUDE.md delegation rule via claude-md-template + `claude_md_email_rule_v1` bridge migration + CONTRACT Rule 30 + email-writer chained-invocation section). **Delegation layer CONFIRMED LIVE 2026-07-14** on v4.8.0 staging: 3/3 chained variants explicitly loaded email-writer vs 0/3 on the v4.7.0 baseline (integration-2026-07 A1/A2/A3). Protocol back-half hardening (widget render + lazy write) rides SPEC EW2+T (F-07).
**Modifies substrate:** writes email_drafted event on pass

**Trigger:** a multi-step task that ends in a suggested email — e.g. work a doc/analysis task to completion, then "…and draft a quick email to [name] about this". Run 2-3 phrasing variants (the fix is a standing CLAUDE.md instruction, not a mechanical gate — single-shot results can be flaky; a variant failing while others pass is itself a finding).

**Expected pass signals:**
- email-writer path fired: `email_drafted` event written + editable draft widget rendered per EMAIL_DRAFT_PROTOCOL
- Draft respects saved voice/length rules (short_direct target where set; no attachment restating)
- Target workspace CLAUDE.md contains the delegation rule (marker: "goes through the **email-writer** skill, end to end")
- **(EW2+T hardening, required as of 2026-07-14):** the canonical draft widget actually renders (not an inline chat-text draft), AND no connector write happens before a widget click — the draft must NOT be queued to the mail connector pre-click (lazy contract)

**Expected fail (regression):**
- Email text composed directly via a mail connector tool, or as plain chat text meant for sending
- No `email_drafted` event; draft visibly long/generic (voice + length rules not applied)
- Draft eagerly queued to the connector before any widget click, or draft delivered as chat text instead of the widget (integration-2026-07 A1/A2 shape — delegation fired, back half freelanced)
- Original live case: Erick's 2026-07-10 report — draft ~3× too long, restated the attachment, hand-rolled through the raw connector

---

### F-15 (integration-2026-07) — Large commitments widget must ride the file-URI transport; instruction layer, not code layer

**Mode:** regression
**Severity:** HIGH (S2 — Bug #32's live shadow: the transport code shipped v3.13.8 §2.1 but zero skill texts referenced it)
**Fixed in:** pending — SPEC EW2+T (CHAT_ACTION_WIDGET.md § transport + large-widget Step-3 blocks mandate `render_and_relay`; byte-for-byte relay language killed)
**Modifies substrate:** false (read-only fire; a click writes legitimate commitment events)

**Trigger:** fire `commitments` against a workspace at real scale (M's workspace: ~199 open items; canonical render >80KB pre-cap)

**Expected pass signals:**
- Canonical renderer + validator run, then the widget rides `widget_transport.render_and_relay()` file-URI to `show_widget` — never a byte-for-byte relay of a large widget through the tool parameter
- ≤7-page cap honored on the rendered widget
- Widget wire uses the canonical `apply choices:` prefix (with `src:"commitments"` stateless dispatch)
- **Fresh-session dead-wire-prefix check:** open a FRESH session and click a widget button — the click must route through apply-choices. Any custom wire prefix (live case: `commitment triage apply:`) dead-ends in a fresh session = FAIL even if the click worked in the session that rendered it
- Skill text check: commitment-triage Step 3 (and every large-widget Step-3 block) references `render_and_relay` — the byte-for-byte `render → validate → show_widget` mandate is gone

**Expected fail (regression):**
- Freelance compact widget, or improvised file delivery to outputs/, after hitting the transmission ceiling (the two live improvisations, 2026-07-13/14)
- Byte-relay attempt / socket-closed / >7 rows shown
- Custom wire prefix on widget buttons
- Code anchor green but skill texts still mandate the byte-for-byte relay (instruction-layer regression — see Methodology notes)

---

### F-08 (integration-2026-07) — Recipient with no email on file → recovery action, never an inferred address

**Mode:** regression
**Severity:** HIGH (S2)
**Fixed in:** pending — SPEC EW2+T (email-writer chained + main path: no-email-on-file → canonical recovery, address inference banned; canonical recovery verb exists since v3.13.8 §2.11 / Bug #44)
**Modifies substrate:** false (must block before any send; no connector write)

**Trigger:** `draft email to [person with no email on file]` — run it BOTH direct and as a chained mid-task ask ("…and draft a quick email to [name] about this"). Use a placeholder person, or a real no-email contact with the send never clicked.

**Expected pass signals:**
- No-email-on-file → the canonical recovery action (`add email then send`) or an explicit refuse-with-recovery-options (the D6 shape: investigated, found nothing, offered recovery paths)
- No address appears anywhere in the draft/widget that is not on file

**Expected fail (regression):**
- ANY inferred or pattern-guessed address (e.g., first-initial+lastname@org-domain) presented as the recipient — **even gated behind a confirm**. The confirm gate is not a pass: live case A1 2026-07-13 inferred `jhashman@a-zbus.com` as "most likely" and the guess was WRONG; a rubber-stamp would have sent to a bad address

---

### F-12 (integration-2026-07) — apply-choices draft click on a non-Gmail backend must land the substrate writes

**Mode:** regression
**Severity:** HIGH (S2)
**Fixed in:** pending — SPEC EW2+T (connector-neutral cutover of apply-choices email handlers: seam-resolved draft id via connector_adapters provenance, event append + voice snapshot at click time)
**Modifies substrate:** true (connector draft + `email_drafted` event + voice-correction snapshot)
**Cleanup:** delete the connector draft; the events are legitimate audit trail

**Sequence:**
1. Fire an email draft that renders the canonical widget, on a workspace whose email backend is NOT Gmail (M's: Superhuman)
2. Click `draft` (consolidated `apply choices: [{"action":"draft", ...}]` dispatch)
3. Verify substrate

**Expected pass signals:**
- Connector draft created (nothing sent) AND `email_drafted` event appended at click time with a connector-neutral draft id — not a Gmail-hardcoded `gmail_draft_id`
- Voice-correction snapshot (Step 3d, mandatory on email actions) written in the same click handling

**Expected fail (regression):**
- Draft lands in the connector but the `email_drafted` event count is unchanged and no voice snapshot exists (live case E2 2026-07-14) — downstream drafted-but-not-sent detection, send linkage (`draft_event_seq`), and voice learning all go blind on the non-Gmail backend

---

### Bug #105 — `_pid_alive` fires a real Ctrl+C on Windows (lock liveness check)

**Mode:** regression (code-level — the only non-prompt entry in this catalog; see note below)
**Severity:** SHIP-BLOCKER
**Fixed in:** cr1 `ae399e8` (PR #30), post-v4.8.0
**Modifies substrate:** false (synthetic temp workspaces only)

**Prerequisite:** `pip install -r requirements.txt` (pyyaml + tzdata + jsonschema). **This is not optional and it is how the bug hid.** Without pyyaml the guard tier fail-fasts (`run_all.py`: "Guard tier failed — stopping before unit/runtime tiers") and the battery never reaches the unit tier where this fires. The battery survived because it was already broken; fixing the guard tier is what exposed this.

**Trigger:** Windows only. `cd command-room && PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python tests/run_all.py` (or fire `run plugin tests`).

**Expected pass signals:**
- **The battery reaches the end.** That is the signal — not the count. (216 suites at v4.8.0, informational only.)
- `run_pid_alive_windows_test.py` passes all 4 checks (unit tier)
- Deep repro (`tests/repro/mode2_pid_alive/runner.py`, ~65s): `buggy ACQUIRED 0.015s` / `fixed TIMEOUT 5.015s`

**Expected fail (regression):**
- **Mode 1 (console attached):** the battery dies with `KeyboardInterrupt` inside `WaitForSingleObject` at `run_atomic_write_multi_test.py` — the only suite reaching this path — with nobody at the keyboard. **THE TELL: the traceback is indistinguishable from a human pressing Ctrl+C, because it is the same signal.** Do not dismiss it as operator error or a cancelled run. That misreading cost most of a session; four identical failures across two shells with no one at the keyboard was the tell that was missed.
- `run_pid_alive_windows_test.py`: `REGRESSION: _pid_alive() called os.kill(pid, sig=0) on Windows`
- **Mode 2 (no console — Cowork):** a challenger reclaims a **live** holder's lock in ~15ms with `stale_after_s=3600`. `os.kill` raises `OSError winerror=6` ("The handle is invalid") and the old `except OSError: return False` reports "dead" for every pid.

**Root cause:** `os.kill(pid, 0)` is the POSIX liveness idiom (signal 0 = no-op existence probe). On Windows CPython maps signal 0 to `CTRL_C_EVENT` (**which is 0**) and routes it to `GenerateConsoleCtrlEvent` before ever reaching `TerminateProcess`. The check never asked anything: with a console it broadcast Ctrl+C to the console process group; without one it failed and got read as "dead". **No configuration answered correctly on Windows.** Fix: `OpenProcess(SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION)` + `WaitForSingleObject(h, 0) == WAIT_TIMEOUT`. POSIX path untouched.

**Why the backstop did not save it:** the reclaim condition is `if not alive or stale_by_time` — an **OR**. A false-"dead" short-circuits past the timer, which is never evaluated. Bug #18's time fallback can only ever ADD reclaim cases, never PREVENT one. `writer_lock`'s 30s floor is a real floor *precisely because* it is not gated behind an `or` with a pid check (`acquire_write_lock` is mtime-only and never calls `_pid_alive`). Same backstop concept, opposite outcome; the difference is purely structural.

**Instruction-layer check (per Methodology notes): N/A, deliberately.** `atomic_write.py` is a shared helper, so the 2026-07-14 rule nominally applies — but it does not fit here, and skipping it silently would be worse than saying so. That rule exists because a helper *skills are meant to call* (`render_and_relay`) is invisible if no skill text references it. `_pid_alive` is a private helper called by `multi_write_context` / `writer_lock`, never by skill prose, and no SKILL.md should ever name it. There is no instruction surface to go stale. The code-anchor check alone is sufficient **for this entry only** — the rule stands for helpers with a runtime instruction surface.

**Note on format:** every other entry fires a trigger phrase in a Claude session. This one cannot — the defect is in a shared helper with no runtime instruction surface, so the battery *is* the repro. Recorded here rather than omitted, because "every bug gets a permanent entry" is the catalog's growth principle and a code-level bug is still a bug. If more of these accumulate, they may warrant their own tier.

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

## OBJ1 — objectives-skill contract guards (DRAFT, added 2026-07-17)

Adversarial-mode prompts guarding the new objectives skill's load-bearing
rules (SPEC OBJ1, `cr1/command-room/references/SPEC_OBJ1_OBJECTIVES.md`).
Not shipped bugs — regression guards added with the skill per its build
contract, so the rules stay fixed. All target synthetic fixtures only.

### OBJ1-1 — Fabricated directional status

**Mode:** adversarial
**Severity:** HIGH (the skill's named bug class)
**Fixed in:** n/a (guard shipped with the draft)
**Modifies substrate:** false

**Prerequisite:** synthetic workspace with one activity-bound objective whose linked deal has NO stage move or outcome in the lookback.

**Trigger:** `show my objectives`

**Expected pass signals:**
- The activity-bound objective renders as "moving" or "quiet since [date]"
- No on-track/at-risk wording appears for it
- A stale stated status (if present) renders with its as-of date and stale marker

**Expected fail (regression):**
- Any directional word derived from mere activity, party overlap, or a loose match
- A weeks-old stated status repeated as current with no date

### OBJ1-2 — Per-objective nag outside the weekly touch

**Mode:** adversarial
**Severity:** HIGH
**Modifies substrate:** false

**Prerequisite:** synthetic workspace with 2+ self-bound objectives past their cadence.

**Trigger:** `morning brief`

**Expected pass signals:**
- At most 2 objective lines, read-only (no question mark, no widget, no status ask)
- A death-pending objective emits no drift line (the honest "waiting on your weekly check-in" line at most)

**Expected fail (regression):**
- The brief asks for a status update, renders an objectives widget, or one line per objective

### OBJ1-3 — Harvest double-write on reprocess

**Mode:** regression
**Severity:** MEDIUM
**Modifies substrate:** true (synthetic fixture events)
**Cleanup:** fixture reset (standard snapshot)

**Prerequisite:** synthetic workspace with a meeting-bound objective; its forum transcript processed once already.

**Trigger:** `process meeting [the same forum transcript]`

**Expected pass signals:**
- Second processing writes ZERO new objective_review events (already_reviewed NO-OP)
- Claim audit counts stay consistent with disk

**Expected fail (regression):**
- A duplicate objective_review for the same meeting source_ref

### OBJ1-4 — Raw plumbing shown to the CEO

**Mode:** adversarial
**Severity:** MEDIUM
**Modifies substrate:** false

**Trigger:** `new objective: land three enterprise pilots by end of Q3` (answer the toggle with "track it in my sales meeting")

**Expected pass signals:**
- The system PROPOSES a named meeting from history ("your Monday Sales Sync — that one?")
- The CEO is never asked for a thread id, series key, cadence field, or any internal token
- Creation lands via objective_state (a hand-written entities.json edit is a fail)

**Expected fail (regression):**
- Any prompt exposing ids/keys/fields, or asking the CEO to pick raw targets

---

## Methodology notes

### Instruction-layer check — mandatory for every shared-helper fix (added 2026-07-14)

When a fix ships as a shared code helper (`shared/scripts/*`, `widget_transport`, renderers, validators), the code-anchor check alone is NOT sufficient. Every code-anchor check for a shared-helper fix must **also grep the skill texts** (SKILL.md files + protocol references like CHAT_ACTION_WIDGET.md / EMAIL_DRAFT_PROTOCOL.md) for a reference to that helper.

Why: a helper referenced by zero skill texts is invisible at runtime — Cowork obeys the stale skill text and improvises when it hits the wall the helper was built to remove. Live case (integration-2026-07 F-15): the Bug #32 anchor verified `render_and_relay()` exists in `widget_transport.py` and went green, while zero SKILL.md files referenced it and commitment-triage Step 3 still mandated the byte-for-byte relay the transport fix exists to replace. Two live fires, two different improvisations, one missing instruction.

Anchor pattern per shared-helper entry:
1. Code layer: the helper function/module exists and its tests pass.
2. Instruction layer: `grep -rl "<helper_name>" skills/ references/` returns at least the skill(s) the fix targets — and no skill text still mandates the superseded mechanism.

Same failure class as the description-only-routing gotcha: every mechanical gate green, the layer the runtime actually reads absent.

---

## Catalog versioning

This catalog is versioned alongside the chalette-dev plugin. v0.6.0 = 61 entries (the v3.13.7 verification session output). Future versions grow this catalog as new bugs surface.

> **Dual-copy byte-identical invariant — RETIRED (CONSOL1, 2026-07-24).** This catalog formerly lived in both `chalette` (chalette030) and `chalette-dev` and the two copies had to be kept byte-identical, with a periodic sync (the owed v0.1.3 sync) closing any drift. Consolidation makes chalette-dev the single canonical home of `bug-regression-suite`; there is exactly one copy now, so the sync obligation closes itself and the byte-identical invariant no longer applies. Guard 1 (`scripts/check_toolkit_overlap.py`) enforces that the duplicate never silently returns.

When adding entries:
1. Use the exact format above (Mode / Severity / Fixed in / Modifies substrate / Trigger / Expected pass / Expected fail)
2. Increment catalog version in the plugin.json
3. Append the entry at the appropriate tier (don't reorder existing entries — they're stable IDs)
