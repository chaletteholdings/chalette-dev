# Phase decision gates

Logic that fires at phase boundaries during a verification session. Determines whether to continue, pause for M's call, or block production-promote.

## Why decision gates matter

Verification sessions can run for hours. M should NOT be asked to make a phase-level decision after every single test. Instead, phase-level decisions surface at well-defined boundaries — after Phase 0 sanity, after Phase A ship-blocker verification, etc.

## Per-phase gate rules

### Phase 0 — Sanity checks

**Continue rule:** ALL Phase 0 tests PASS → green-light Phase A
**Pause rule:** ANY Phase 0 test FAIL → STOP, surface to M, do NOT proceed to Phase A

If Phase 0 fails:
- Plugin install is broken — Phase A would produce unreliable results
- Surface the specific failure + recommend remediation (e.g., "re-run Cowork update" / "reinstall plugin")

### Phase A — Tier 1 ship-blocker verification

**Continue rule:** ALL Phase A tests PASS → green-light prod promote + Phase B
**Pause rule:** ANY Phase A test FAIL → STOP, triage with M, consider patch ship
**Caveat:** PARTIAL verdicts on Phase A → continue to Phase B BUT mark production-promote HOLD

Critical: Phase A failure means the production-promote decision is BLOCKED until fixed. The skill must NOT auto-continue to "promote" without explicit M approval after a Phase A failure.

### Phase B-Tier 1 — Bug #4 cascade unblock (or equivalent — first set of high-impact downstream verifications)

**Continue rule:** ALL B-Tier 1 tests PASS → green-light remaining B-Tiers
**Caveat:** PARTIAL verdicts here typically mean cascade fixes only partially propagated. Surface to M before continuing.

### Phase B-Tier 2 / 3 / 4 / 5 — Lower-priority tiers

**Continue rule:** ANY verdict (including PARTIAL or NEW_BUG) → continue. These tiers don't gate production-promote.
**Pause rule:** Only NEEDS_HUMAN_REVIEW → pause for M's call

### Phase B-Tier 6 — M1 fresh-install (or equivalent fresh-install scope)

**Defer rule:** Most B-Tier 6 tests require fresh-install workspace. The skill SHOULD detect this and offer to defer rather than try to run on M's mature workspace.
- Output: "B-Tier 6 tests require fresh-install workspace. Skip for this session, or set up fresh-install fixture?"

## Decision-gate emission format

When a phase boundary fires, the skill emits a phase-summary block to chat AND to findings log:

```
## PHASE {phase_id} COMPLETE — {pass_count}/{total_count} passed

| Test | Verdict | Key finding |
|---|---|---|
| {test_id} | {verdict} | {1-line summary} |
| ...

**Phase decision gate:** {decision_outcome}

{Next-phase recommendation}
```

For Phase A specifically (highest-stakes gate):

```
## PHASE A — SHIP BLOCKER VERIFICATION COMPLETE

8/8 tests PASS

| Test | Bug | Verdict |
|---|---|---|
| A1 | #4 email cascade | ✅ PASS |
| A2 | #14 commitments | ✅ PASS |
| A3 | #19 disambiguation | ✅ PASS |
| A4 | #28 dormant live-check | ✅ PASS |
| A5 | #11 entity_resolve | ✅ PASS |
| A6 | #2 carry-forward | ✅ PASS |
| A7 | #5 Pulse Calendar half | ✅ PASS |
| A8 | M1 coach rename | ✅ PASS |

**Phase decision gate:** ALL SHIP-BLOCKERS VERIFIED.

✅ **Production-promote recommendation: SAFE**
✅ **New-customer onboarding: SAFE**

Continuing to Phase B-Tier 1.
```

Or for the failure case:

```
## PHASE A — INCOMPLETE — 1 FAIL

6/8 tests PASS
1/8 tests PARTIAL
1/8 tests FAIL ← BLOCKS PROMOTE

| Test | Bug | Verdict | Issue |
|---|---|---|---|
| A1 | #4 email cascade | ❌ FAIL | Gmail draft created before widget render |
| A2 | #14 commitments | ✅ PASS |
| ... |

**Phase decision gate:** Ship-blocker A1 FAILED.

🚩 **Production-promote: BLOCKED** until A1 resolved
🚩 **New-customer onboarding: BLOCKED**

Recommended action: triage A1 with code session, ship v{version}.1 patch, re-run A1.

Do you want to:
(a) Pause verification + triage A1 now?
(b) Continue with Phase B (Tier 1 ship-blocker tagged unresolved, but other phases proceed)?
(c) STOP and roll back to v{prior_version}?
```

## Gate state persistence

Phase-gate decisions persist in `active.json`:

```json
{
  "phase_gates": {
    "0": {"outcome": "GREEN", "decided_at": "<ISO>", "auto_decided": true},
    "A": {"outcome": "BLOCKED", "decided_at": "<ISO>", "auto_decided": false, "m_response": "(a) pause + triage"},
    ...
  }
}
```

On `continue verification`, the skill respects prior phase-gate decisions and resumes accordingly.

## Production-promote auto-recommendation

After all phases complete, the skill computes the production-promote recommendation per:

```python
def production_promote_decision(phase_gates: dict, verdicts: dict, new_bugs: list) -> str:
    """
    Returns: SAFE | HOLD | BLOCKED
    """
    if any(g["outcome"] == "BLOCKED" for g in phase_gates.values()):
        return "BLOCKED"
    if any(v.verdict == "FAIL" for v in verdicts.values() if is_tier_1(v.test_id)):
        return "BLOCKED"
    if any(b.is_ship_blocker for b in new_bugs):
        return "BLOCKED"
    if any(g["outcome"] in ("YELLOW", "PARTIAL") for g in phase_gates.values() if g.phase in ("0", "A")):
        return "HOLD"
    if any(v.verdict == "PARTIAL" for v in verdicts.values() if is_tier_1(v.test_id)):
        return "HOLD"
    return "SAFE"
```

This is reflected in the §0 headline of the verdict doc.
