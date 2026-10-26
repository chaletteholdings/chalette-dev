# Temporal wait strategy — when to actually wait vs simulate time-passage

**Owner:** `cross-skill-interaction-test` (cited from SKILL.md Step 2 and the References list).

> **Provenance (REFGAP1, 2026-07-29).** Cited by SKILL.md since authorship but never
> written — part of the BUILD_VCRRETIRE §7 dangling-read set. Authored from SKILL.md's
> Step 2 contract ("Between phases the skill enforces wait times… Sequences may span
> minutes or hours") and the catalog's wait phases. No prior version existed to recover.

## The two kinds of time in a sequence

Every wait phase in the catalog is one of exactly two things:

1. **Propagation wait** — time for a substrate write to become readable by the next
   consumer (file flush, shard state, connector reconcile). Short: the catalog floor is
   **60 seconds** (the Bug #51 sequence's "wait minimum 60 seconds").
2. **Cadence wait** — time until a *scheduled surface* (the commitments scheduled task,
   pulse, the next morning brief) fires on its own. Long: minutes to a day.

Which one a phase is decides whether you may compress it.

## Rule 1 — propagation waits are ALWAYS real

Never simulate a propagation wait. The bug class this skill exists to catch is exactly
*staleness between a write at T0 and a read at T+N*. Collapse the wait and T0 and T+N
become one session state — the test can no longer fail, so a PASS proves nothing. Sit out
the full 60 seconds (or the entry's stated minimum) on a clock, not on trust.

## Rule 2 — a cadence wait may be compressed ONLY when the cadence is not the subject

If the phase merely needs the scheduled surface to *read* substrate (e.g. "the commitments
task excludes the resolved item"), you may fire the surface manually after the propagation
floor instead of waiting for its slot. Mark the verdict notes "manual fire" — a manual
fire is not identical to a scheduled fire (late-fire handling and since-last-run windows
differ), so a PASS obtained manually is slightly weaker evidence than a scheduled PASS.

If the phase's *subject IS the cadence* — the schedule-change + pulse sequence, anything
verifying when or whether a task fires — the wait must be real. Simulating it deletes the
thing under test.

## Rule 3 — never fake timestamps

Do not back-date or forward-date events in substrate to simulate passage of time. This
skill runs against the operator's REAL workspace: a fabricated timestamp is workspace
corruption, it survives the sequence, and no cleanup sweep can reliably tell it from
legitimate history afterward. If a sequence seems to need a time-shifted event, the
sequence is misdesigned — restate it as a real wait or drop it.

## Rule 4 — long sequences span sessions; record the cursor

Sequences with hour-plus cadence waits will not finish in one sitting. At each phase
boundary record in the running verdict notes: sequence name, last completed phase, every
captured seq/identifier, and the earliest time the next phase may fire. Resuming means
re-reading that cursor — never re-firing completed phases, which would double their
substrate writes.

## Decision table

| The phase verifies… | Wait type | May compress? |
|---|---|---|
| A later skill reads an earlier skill's write | Propagation | No — real 60s+ floor |
| A scheduled surface's *read* of substrate | Cadence | Yes — manual fire after the floor, noted as manual |
| A scheduled surface's *firing behavior* (when/whether) | Cadence | Never |
| Same-session widget → substrate → widget | Propagation | No — floor still applies |
