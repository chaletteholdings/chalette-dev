# Multi-phase verdict aggregation — combining per-phase verdicts into a sequence verdict

**Owner:** `cross-skill-interaction-test` (cited from SKILL.md Step 3 and the References list).

> **Provenance (REFGAP1, 2026-07-29).** Cited by SKILL.md since authorship but never
> written — part of the BUILD_VCRRETIRE §7 dangling-read set. Authored from SKILL.md's
> Step 3 verdict examples. No prior version existed to recover.

## Per-phase verdicts

Each phase resolves to exactly one of:

- **PASS** — the phase's observable happened: the fire produced its expected output AND
  the expected substrate writes are present with the expected shapes. A wait phase counts
  as a phase; its PASS means the wait actually elapsed (Rule 1/2 of
  `temporal-wait-strategy.md`), not that nothing went wrong while waiting.
- **FAIL** — an expected write is missing/malformed, or the reading skill shows stale
  state. Record observed vs expected verbatim from the paste-back.
- **BLOCKED** — the phase could not be attempted (skill refused, connector down, operator
  profile lacks 'real'). Not a FAIL: nothing was disproven.

There is no partial credit inside a phase. A phase that wrote one of two expected events
is FAIL, not "half-pass" — the missing write is precisely the signal.

## Aggregation rules

1. **Fail-fast.** The first FAIL ends the sequence at that phase. Later phases read state
   the failed phase was supposed to write; firing them anyway produces cascading noise,
   not additional signal. Report the un-fired phases as NOT RUN.
2. **Sequence PASS = every phase PASS.** Nothing weaker. A sequence is a chain, not a
   checklist — never aggregate by count ("3 of 4 phases passed" is a FAIL at phase 4, and
   the verdict says so).
3. **Any BLOCKED phase → sequence BLOCKED** (unless a FAIL already occurred earlier, which
   wins). A BLOCKED sequence is re-runnable; a FAILED one needs investigation first.
4. **DRAFT-status sequences report ADVISORY, not blocking.** A catalog entry that has
   never had a confirmed walk (see the Status legend in `sequence-catalog.md`) may carry a
   wrong expected-write. Its FAIL means "investigate: real regression or wrong draft
   expectation" — fix whichever is wrong, and promote the entry to READY once a walk
   confirms it. Only READY-sequence FAILs assert a regression.

## Sequence-level output format

Mirror SKILL.md Step 3. Every FAIL carries the failing phase, observed vs expected, and a
recommended action naming the suspect component:

```
Sequence: show-my-list cascade verifies in morning brief

Phase 1: PASS
Phase 2: PASS
Phase 3: FAIL
- Source commitment seq 71 STILL IN morning brief's "you owe" count
- Bug #51 cascade regression detected

Recommended action: investigate apply-choices Step 3a dispatch — may not be cascading source closure
```

A recommended action is mandatory on FAIL — a verdict that names no suspect leaves the
operator re-deriving the sequence's whole dependency chain from scratch.

## Run-level aggregation (`run cross-skill test`)

When running the whole catalog, emit one table — sequence → verdict (with the failing
phase for FAILs) — then the overall verdict:

- **PASS** — every READY sequence passed (ADVISORY notes listed separately).
- **FAIL** — at least one READY sequence failed. Name each, with its recommended action.
- **BLOCKED** — no READY sequence failed but at least one couldn't run.

Never let ADVISORY findings from DRAFT sequences flip the run verdict — and never silently
drop them either: list every ADVISORY with what to verify. Silence is not coverage.
