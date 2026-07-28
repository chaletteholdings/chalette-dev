---
name: cross-skill-interaction-test
description: "INTERNAL — temporal substrate-coherence verification. Fires sequences of skills across time (skill A writes substrate at T0 → skill B reads at T+N → verifies coherence). Catches bugs that surface only when one skill's writes affect another skill's reads later — e.g., meeting-notes writes a placeholder commitment + team-intelligence enriches it 10 min later (the Phase 2G duplicate-detection pattern that worked) OR show-my-list closes a wrapper + morning brief should see the source close (Bug #51). Runs against the operator's real Cowork workspace — permitted only when config/operator.json grants 'real'. Triggers: 'run cross-skill test', 'test temporal coherence', 'verify cross-skill', 'cross-skill sequence [name]'. Plugin-developer use only. Companion to bug-regression-suite (single-fire tests) + ship-readiness-gate."
---

# cross-skill-interaction-test

**Tests bugs that only surface when skill A's writes affect skill B's reads later.** Single-skill tests miss these — they fire one skill at a time. Real workflows have skills interacting through substrate over time. This skill tests those interactions.

> **Operator profile (read first).** Load `config/operator.json`, then overlay `config/operator.local.json` per-key if present (gitignored; the operator's local overlay — not every operator has one). The multi-phase sequences drive a live Cowork workspace via paste-back — there is no synthetic paste-back mode — so if the merged `allowed_targets` does not include `"real"`, refuse and say so.
> ```python
> import json, os, sys
> op = {}
> for _n in ("operator.json", "operator.local.json"):
>     _p = os.path.join(SKILL_PLUGIN_ROOT, "config", _n)
>     if os.path.exists(_p): op.update(json.load(open(_p)))
> # SKILL_PLUGIN_ROOT must be a NATIVE path — on Windows `C:/Users/…`, never an MSYS
> # `/c/Users/…` (convert with `cygpath -m`): python.exe reads `/c/…` as `C:\c\…`, both
> # files miss, and an empty profile silently becomes the default. Fail loud instead.
> if not op: sys.exit(f"FATAL: operator profile unreadable under {SKILL_PLUGIN_ROOT}")
> if "real" not in op.get("allowed_targets", []): refuse("cross-skill-interaction-test needs an operator profile with 'real' in allowed_targets")
> ```

## Why this skill exists

Per V3.13.8_MASTER_PLAN §6 + the 20% gap analysis: cross-skill interaction bugs surface in real workflows because skill outputs feed downstream skill inputs through substrate. Examples we've seen:

1. **Phase 2G duplicate-detection coherence** (Strength #6) — meeting-notes wrote placeholder commitment + team-intelligence enriched + closed placeholder → exactly one open item. This worked, but ONLY because both skills coordinate via canonical substrate.

2. **Bug #51 show-my-list cascade** — show-my-list closed a wrapper at T0; morning brief 10 min later still showed the source as open. The bug only surfaces with the temporal sequence.

3. **Bug #52 morning-brief load_open_commitments** — morning-brief read events.jsonl AFTER show-my-list wrote a closure; freelance scan silently dropped malformed lines including the closure event → morning brief showed stale state.

4. **Hypothetical future bug:** ingest-context writes a commitment at T0; pulse fires at T+1 hour; pulse should consider the new commitment in its scan window. If pulse caches its prior fire's results, it might miss the new commitment.

These are temporal bugs invisible to single-fire tests.

## When this fires

| Trigger | Context |
|---|---|
| `run cross-skill test` | Run all sequences in catalog |
| `test temporal coherence` | Same |
| `verify cross-skill` | Same |
| `cross-skill sequence [name]` | Run one specific sequence |
| `run cross-skill test --catalog` | List available sequences |

## Behavior

### Step 1 — Load sequence catalog

Catalog in `references/sequence-catalog.md`. Each sequence has:

```markdown
## Sequence: show-my-list cascade verifies in morning brief (Bug #51 regression)

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
```

### Step 2 — Walk the operator through each phase

The skill drives the operator through each phase of a sequence. The operator:
1. Fires the phase's trigger in Cowork
2. Pastes Cowork response back
3. Skill validates phase output + advances OR stops on failure

Between phases the skill enforces wait times (substrate propagation, scheduled-task cadence). Sequences may span minutes or hours.

### Step 3 — Multi-phase verdict

After all phases of a sequence complete:

```
Sequence: show-my-list cascade verifies in morning brief

Phase 1 (show-my-list fire): PASS
- Widget rendered, item resolved
- Wrapper seq 1779426060120467301 → source seq 71

Phase 2 (substrate wait): PASS
- 60s wait completed

Phase 3 (morning brief fire): PASS  
- Brief rendered cleanly
- Source seq 71 ABSENT from "you owe" count
- Bug #51 cascade verified working

OVERALL: PASS
```

If any phase fails:

```
Sequence: show-my-list cascade verifies in morning brief

Phase 1: PASS
Phase 2: PASS  
Phase 3: FAIL
- Source commitment seq 71 STILL IN morning brief's "you owe" count
- Bug #51 cascade regression detected

Recommended action: investigate apply-choices Step 3a dispatch — may not be cascading source closure
```

### Step 4 — Cleanup

Substrate modifications across multi-phase fires accumulate. Cleanup helper (reuses bug-regression-suite's cleanup-helper.md logic):
- Pre-sequence snapshot
- Post-sequence diff
- Conservative archive-with-test-artifact-flag

## Sequence catalog

See `references/sequence-catalog.md`. Initial catalog (~15 sequences):

| Sequence | Bugs covered | Skills involved |
|---|---|---|
| show-my-list cascade verifies in morning brief | #51 | show-my-list, morning-briefing |
| meeting-notes placeholder + team-intelligence enriches | (Strength #6 pattern, no bug) | meeting-notes, team-intelligence |
| ingest-context update + morning-brief next day surfaces | (future-bug-candidate) | ingest-context, morning-briefing |
| email-writer send + dormant-customer-scan suppresses recipient | (validates Bug #28 chain) | email-writer, dormant-customer-scan |
| commitment_resolved + commitments scheduled task excludes | (Bug #51 + #14 chain) | apply-choices, commitments orchestrator |
| follow-up-ritual + commitments cap excludes wrapped | (Bug #14 + #51 chain) | follow-up-ritual, commitments |
| update-bridge migration sequence | (Bug #20 multi-write) | command-room-update-bridge |
| voice scrub propagation across skill family | (Bug #16/#60) | weekly-audit, dormant-scan, operator-report |
| closure-reversal awareness across thread-resurrection + intro-broker + email-writer | (Strength #20 propagation) | 3 skills |
| board pack + insight-generator dual deliverable conflict | (deliverables-as-substrate v3.14.x candidate) | board-pack-assembler, insight-generator |
| pulse + dormant-scan duplicate detection | (Strength #6 propagation candidate) | pulse, dormant-customer-scan |
| morning brief consumed by commitments scheduled task | (Bug #2 carry-forward chain) | morning-briefing, commitments |
| schedule-change + Pulse cadence adjustment | (Bug #5 + change-schedule chain) | change-schedule, pulse |
| objective harvest chain: create meeting-bound objective at T0 → meeting-notes processes a forum transcript at T+1 → readout derives the stated status, reprocess is a NO-OP | (SPEC OBJ1 draft — the Step 5g contract: one objective_review per meeting source_ref; absence writes nothing) | objectives, meeting-notes |
| objective drift isolation: quiet objective thread at T0 → stalled-projects scan at T+N excludes it while the objectives readout flags it WITH a suggested move | (SPEC OBJ1 draft — the D7-shaped fence; never double-flagged, never a bare flag) | objectives, stalled-projects, morning-briefing |
| inbox-triage Reply Now + chat_dismissal on skip | (Bug #39 chain) | inbox-triage, apply-choices |
| memo-writer + decision-memo cross-reference | (deliverables-as-substrate v3.14.x candidate) | memo-writer, decision-memo-composer |

## Sequence add discipline

When you discover a temporal bug:
1. Reproduce the sequence manually
2. Add a catalog entry per format above
3. Catalog grows over time — similar to bug-regression-suite

## Integration with ship-readiness-gate

ship-readiness-gate optionally runs the highest-priority sequences as part of its battery. The full catalog is too long for every push; ship-readiness-gate runs a CURATED subset (the 5 most critical sequences) + leaves the full catalog for periodic deep verification.

## Safety: substrate writes across sequences

Each sequence declares which substrate it modifies + how to clean up. Use bug-regression-suite/references/cleanup-helper.md logic. Some sequences (e.g., Bug #51 cascade) intentionally write legitimate state changes — don't clean those up. Others (e.g., test commitment created via ingest-context) need cleanup.

## What this skill catches that bug-regression-suite misses

| Pattern | bug-regression-suite | cross-skill-interaction-test |
|---|---|---|
| Single-fire bug | ✅ | partial (only as sub-component of sequence) |
| Multi-fire same-skill | partial | ✅ |
| Multi-skill same-session | (sequential phases possible but not natural) | ✅ |
| Multi-skill with substrate-propagation wait | ❌ | ✅ |
| Multi-session (skill fires hours/days apart) | ❌ | ✅ |
| Sequence ordering matters | unclear | explicit |

Both skills are complementary, not substitutes.

## References

- `references/sequence-catalog.md` — full catalog of cross-skill sequences (initial 15, growing)
- `references/temporal-wait-strategy.md` — when to actually wait vs simulate time-passage
- `references/multi-phase-verdict-aggregation.md` — how to combine per-phase verdicts into sequence-level verdict
