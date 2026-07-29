# Cross-skill sequence catalog

**Owner:** `cross-skill-interaction-test` (SKILL.md Step 1 loads this file).
Wait rules: `references/temporal-wait-strategy.md`. Verdict rules: `references/multi-phase-verdict-aggregation.md`.

> **Provenance (REFGAP1, 2026-07-29).** SKILL.md cited this file since authorship, but it
> never existed — one of the dangling reference reads recorded in BUILD_VCRRETIRE §7. No
> prior version was recoverable (chalette-dev, chalette030, and retired-plugin git history
> plus session transcripts all checked — the file was never written). Authored from
> SKILL.md's inline index table and its format example. Event names verified against
> cr1 `command-room/shared/data-schemas/events.schema.json`.

## Status legend

- **READY** — phases and expected writes confirmed against at least one live walk. A FAIL
  on a READY sequence is a regression.
- **DRAFT** — derived from the SKILL.md index row and current skill texts, not yet walked.
  Walk it once and confirm the expected substrate writes before trusting a FAIL as a
  regression; on the first confirmed walk, promote to READY and correct any wrong
  expected-write here. Per `multi-phase-verdict-aggregation.md`, DRAFT failures report as
  ADVISORY, not blocking.

Two named surfaces in this catalog are **scheduled tasks, not `skills/` directories**: the
*commitments scheduled task* and *pulse*. Their fires are cadence-bound — see
`temporal-wait-strategy.md` before simulating either.

---

## Sequence: show-my-list cascade verifies in morning brief (Bug #51 regression)

**Status:** READY

**Phases:**
1. Fire show-my-list
2. Click resolved on a discuss-wrapper item (capture source commitment seq from data.commitment_id)
3. Wait minimum 60 seconds (substrate write propagation)
4. Fire morning brief
5. Verify: source commitment NOT in morning brief's "you owe" count

**Skills involved:** show-my-list, morning-briefing
**Expected substrate writes:**
- commitment_resolved event for wrapper
- commitment_resolved event for source (via v3.13.8 §2.9 cascade)
- pack_run events for both fires

**Pass criteria:**
- TWO commitment_resolved events written (cascade per Bug #51 fix)
- Source commitment absent from morning brief's open-commitments surface
- load_open_commitments reads the cascade and excludes source

**Fail criteria (regression):**
- Only wrapper closed; source still open in morning brief

**Cleanup:** none — both closures are legitimate state changes

---

## Sequence: meeting-notes placeholder + team-intelligence enriches (Strength #6 pattern)

**Status:** DRAFT

**Phases:**
1. Fire meeting-notes on a real transcript in which a tracked person owns an action item; capture the placeholder commitment seq
2. Wait minimum 10 minutes
3. Fire team-intelligence for that person
4. Verify: the placeholder was enriched via canonical substrate — exactly ONE open item remains for that action

**Skills involved:** meeting-notes, team-intelligence
**Expected substrate writes:**
- meeting_processed + commitment (placeholder) from phase 1
- commitment_updated (enrichment) — or commitment_resolved on the placeholder plus one enriched commitment — from phase 3

**Pass criteria:**
- Exactly one open commitment for the action item after phase 3 (duplicate-detection coherence)
- Enrichment traceable to the phase-1 placeholder seq

**Fail criteria (regression):**
- Two open items for the same action (duplicate), or the enrichment silently dropped

**Cleanup:** none if the transcript is real — the enrichment is a legitimate state change

---

## Sequence: ingest-context update + morning-brief next day surfaces (future-bug-candidate)

**Status:** DRAFT

**Phases:**
1. Fire ingest-context with content carrying one new commitment; capture its seq
2. Wait for the next scheduled morning brief (early manual fire permitted — this sequence tests the scan window, not the cadence; see temporal-wait-strategy)
3. Verify: the new commitment appears in the brief's open-commitments surface

**Skills involved:** ingest-context, morning-briefing
**Expected substrate writes:**
- commitment from phase 1
- briefing / brief_state from phase 2

**Pass criteria:** the phase-1 commitment is inside the brief's scan window and surfaces

**Fail criteria (regression):** the brief reuses a prior fire's cached results and misses the new commitment

**Cleanup:** if the ingested commitment was synthetic, resolve it after the walk (tag test_artifact=true); prefer ingesting a real one

---

## Sequence: email-writer send + dormant-customer-scan suppresses recipient (validates Bug #28 chain)

**Status:** DRAFT

**Phases:**
1. Draft outreach to a dormant-leaning contact via email-writer; the operator reviews and actually sends it
2. Wait minimum 60 seconds after the send is reconciled into substrate
3. Fire dormant-customer-scan
4. Verify: the just-contacted recipient is NOT flagged dormant

**Skills involved:** email-writer, dormant-customer-scan
**Expected substrate writes:**
- email_drafted / draft_created from phase 1; email_sent or outreach_sent once the send lands
- the scan's own run records from phase 3

**Pass criteria:** recent outreach suppresses the recipient from the dormant list

**Fail criteria (regression):** recipient listed dormant despite the recorded outreach

**Cleanup:** none — a real send is real. Only walk this when an outreach to that contact is genuinely intended; the suppression keys on the SENT record, so a draft left unsent does not exercise the chain

---

## Sequence: commitment_resolved + commitments scheduled task excludes (Bug #51 + #14 chain)

**Status:** DRAFT

**Phases:**
1. Resolve an open commitment through a widget (apply-choices path); capture its seq
2. Wait for the commitments scheduled task's next fire (early manual fire permitted with the manual-fire caveat in temporal-wait-strategy)
3. Verify: the resolved item is absent from the task's list and from its cap counts

**Skills involved:** apply-choices, commitments scheduled task
**Expected substrate writes:**
- commitment_resolved + choices_applied (or apply_choices_applied) from phase 1

**Pass criteria:** the scheduled surface reads the closure and excludes the item everywhere it counts

**Fail criteria (regression):** resolved item still listed or still consuming cap

**Cleanup:** none — the closure is a legitimate state change

---

## Sequence: follow-up-ritual + commitments cap excludes wrapped (Bug #14 + #51 chain)

**Status:** DRAFT

**Phases:**
1. Run follow-up-ritual on a processed meeting; capture the wrapper/source seq pairs it creates
2. Wait minimum 60 seconds
3. Fire the commitments surface
4. Verify: each wrapped item is counted ONCE — the cap logic excludes wrapped duplicates per the Bug #14 fix

**Skills involved:** follow-up-ritual, commitments scheduled task
**Expected substrate writes:**
- followup_pack_drafted + wrapper commitment events referencing their sources from phase 1

**Pass criteria:** no double counting between wrapper and source anywhere the cap applies

**Fail criteria (regression):** wrapper and source both counted, cap consumed twice for one real item

**Cleanup:** none if the pack is real

---

## Sequence: update-bridge migration sequence (Bug #20 multi-write)

**Status:** DRAFT

**Phases:**
1. After a plugin version change, fire command-room-update-bridge; capture which migrations it reports applying
2. Fire it again immediately
3. Verify: the re-fire is a NO-OP — no migration applied twice — and substrate readers still parse cleanly

**Skills involved:** command-room-update-bridge
**Expected substrate writes:**
- plugin_update + one workspace_migration_applied per pending migration from phase 1
- workspace_migration_skipped (or no migration writes at all) from phase 2

**Pass criteria:** each migration applied exactly once across both fires

**Fail criteria (regression):** duplicate migration writes, or a partial multi-write leaving substrate inconsistent

**Cleanup:** none — migrations are legitimate one-way state

---

## Sequence: voice scrub propagation across skill family (Bug #16/#60)

**Status:** DRAFT

**Phases:**
1. Update the voice/scrub configuration at T0
2. Wait minimum 60 seconds
3. Fire cleanup (the ex-weekly-audit surface), dormant-customer-scan, and operator-report
4. Verify: every output reflects the updated block — zero pre-update phrasing or scrubbed tokens in any of the three

**Skills involved:** cleanup, dormant-customer-scan, operator-report
**Expected substrate writes:**
- voice_block_updated from phase 1
- each skill's own run records from phase 3

**Pass criteria:** the update propagates to all three consumers on their next fire

**Fail criteria (regression):** any one consumer still emits pre-update voice (partial propagation is the bug class)

**Cleanup:** none — restore the voice block only if the T0 change was itself synthetic

---

## Sequence: closure-reversal awareness across thread-resurrection + intro-broker + email-writer (Strength #20 propagation)

**Status:** DRAFT

**Phases:**
1. Resolve a thread at T0; capture its seq
2. Reverse the closure (reopen) at T+1
3. Wait minimum 60 seconds
4. Fire thread-resurrection, then intro-broker or email-writer in that thread's context
5. Verify: all consumers treat the thread as OPEN again

**Skills involved:** thread-resurrection, intro-broker, email-writer
**Expected substrate writes:**
- thread_resolved from phase 1; thread_updated (reopen) from phase 2

**Pass criteria:** resurrection may propose the thread; drafts reference current (open) state, not the stale closure

**Fail criteria (regression):** any consumer still reads the thread closed after the reversal

**Cleanup:** re-resolve the thread if the reopen was only for the test

---

## Sequence: board pack + insight-generator dual deliverable conflict (deliverables-as-substrate v3.14.x candidate)

**Status:** DRAFT

**Phases:**
1. Fire board-pack-assembler at T0
2. Fire insight-generator over the same period at T+N
3. Verify: the two deliverables coexist without conflicting or duplicated deliverable state

**Skills involved:** board-pack-assembler, insight-generator
**Expected substrate writes:**
- board_pack_assembled from phase 1
- insight-generator's own run records from phase 2

**Pass criteria:** no crash, no duplicated deliverable records, each artifact filed once

**Fail criteria (regression):** double-filed or mutually clobbered deliverable state

**Cleanup:** archive test artifacts with test_artifact=true if the period was synthetic. The precise invariant firms up when deliverables-as-substrate lands; until then this sequence is a canary, not a contract

---

## Sequence: pulse + dormant-scan duplicate detection (Strength #6 propagation candidate)

**Status:** DRAFT

**Phases:**
1. A pulse fire surfaces a dormancy-shaped signal; capture which account
2. Fire dormant-customer-scan at T+N
3. Verify: the same account is not re-surfaced as if new — deduplicated or marked already-surfaced

**Skills involved:** pulse (scheduled surface), dormant-customer-scan
**Expected substrate writes:**
- pulse_run (and dormancy_signal where emitted) from phase 1

**Pass criteria:** the scan sees the pulse's earlier signal and does not duplicate it

**Fail criteria (regression):** operator shown the same dormancy signal twice as two fresh items

**Cleanup:** none

---

## Sequence: morning brief consumed by commitments scheduled task (Bug #2 carry-forward chain)

**Status:** DRAFT

**Phases:**
1. Morning brief at T0 carries forward an overdue commitment; capture its seq
2. Fire the commitments scheduled task at T+N
3. Verify: the item appears once, with state consistent between the two surfaces

**Skills involved:** morning-briefing, commitments scheduled task
**Expected substrate writes:**
- briefing / brief_state from phase 1

**Pass criteria:** single consistent representation — no double carry-forward, counts agree across surfaces

**Fail criteria (regression):** the item duplicated or the two surfaces disagree on its state

**Cleanup:** none

---

## Sequence: schedule-change + Pulse cadence adjustment (Bug #5 + change-schedule chain)

**Status:** DRAFT

**Phases:**
1. Adjust the pulse cadence via change-schedule at T0
2. REAL cadence wait — the cadence IS the subject under test; never simulate this wait (temporal-wait-strategy rule 2)
3. Verify: the next pulse fire honors the new cadence, and no fire occurs on the old cadence

**Skills involved:** change-schedule, pulse (scheduled surface)
**Expected substrate writes:**
- schedule_config_changed from phase 1
- pulse_run at the NEW cadence from phase 3

**Pass criteria:** exactly the new cadence observed

**Fail criteria (regression):** a fire at the old cadence, or no fire at the new one

**Cleanup:** restore the original cadence via change-schedule if the adjustment was only for the test

---

## Sequence: objective harvest chain (SPEC OBJ1 draft — the Step 5g contract)

**Status:** DRAFT — verify against the landed OBJ1 spec before first walk

**Phases:**
1. Create a meeting-bound objective at T0
2. meeting-notes processes a forum transcript at T+1 that states the objective's status
3. Verify: the objectives readout derives the stated status — one objective_review carrying the meeting's source_ref
4. Reprocess the same transcript
5. Verify: NO-OP — still exactly one objective_review per meeting source_ref; a transcript stating no status writes nothing

**Skills involved:** objectives, meeting-notes
**Expected substrate writes:**
- objective_created from phase 1
- meeting_processed + objective_review (one, keyed to source_ref) from phase 2

**Pass criteria:** exactly one objective_review per meeting source_ref regardless of reprocessing; absence writes nothing

**Fail criteria (regression):** duplicate reviews on reprocess, or a review fabricated from a transcript that stated no status

**Cleanup:** archive the test objective (objective_archived) if it was synthetic

---

## Sequence: objective drift isolation (SPEC OBJ1 draft — the D7-shaped fence)

**Status:** DRAFT — verify against the landed OBJ1 spec before first walk

**Phases:**
1. Arrange an objective thread quiet past the drift window at T0
2. Fire stalled-projects at T+N
3. Verify: the quiet objective is EXCLUDED from the stalled-projects output
4. Fire the objectives readout (or morning brief where it surfaces)
5. Verify: the readout flags the objective WITH a suggested move

**Skills involved:** objectives, stalled-projects, morning-briefing
**Expected substrate writes:**
- the readout's objective_review / objective_report flag from phase 4

**Pass criteria:** flagged exactly once, by the objectives surface, with a suggested move attached — never double-flagged, never a bare flag

**Fail criteria (regression):** stalled-projects also flags it (double), or the readout flags it with no suggested move (bare)

**Cleanup:** none

---

## Sequence: inbox-triage Reply Now + chat_dismissal on skip (Bug #39 chain)

**Status:** DRAFT

**Phases:**
1. Fire inbox-triage; the widget offers Reply Now items
2. Skip/dismiss one item; capture its identifier
3. Wait minimum 60 seconds
4. Re-fire inbox-triage
5. Verify: the dismissed item stays suppressed

**Skills involved:** inbox-triage, apply-choices
**Expected substrate writes:**
- chat_dismissal (via apply-choices) from phase 2

**Pass criteria:** the dismissal is honored on the re-fire; chat_dismissal_cleared appears only on an explicit clear

**Fail criteria (regression):** the skipped item resurfaces as if never dismissed

**Cleanup:** clear the dismissal if the skipped item still needs attention

---

## Sequence: memo-writer + decision-memo cross-reference (deliverables-as-substrate v3.14.x candidate)

**Status:** DRAFT

**Phases:**
1. memo-writer drafts a memo touching a logged decision at T0
2. Fire decision-memo-composer for that decision at T+N
3. Verify: the two artifacts cross-reference the same decision record rather than forking state

**Skills involved:** memo-writer, decision-memo-composer
**Expected substrate writes:**
- memo_drafted from phase 1
- decision_memo_drafted from phase 2

**Pass criteria:** both artifacts anchored to one decision record; neither duplicates the other's content as new state

**Fail criteria (regression):** two divergent decision representations in substrate

**Cleanup:** archive test artifacts with test_artifact=true if the decision was synthetic. Firm invariant lands with deliverables-as-substrate

---

## Adding sequences

Follow SKILL.md's "Sequence add discipline": reproduce the temporal bug manually first, then
add an entry in the format above, Status DRAFT, and promote to READY on the first confirmed
walk. Keep the SKILL.md index table in sync — it is the summary index of this file, not the
executable catalog.
