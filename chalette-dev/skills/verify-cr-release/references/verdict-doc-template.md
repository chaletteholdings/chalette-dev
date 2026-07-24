# Verdict document template

When `verify cr release verdict` fires (or all tests complete), generate `V{version}_VERIFIED_{date}.md` under the resolved `<workspace_root>` (from the operator profile) using this template.

## Template

```markdown
# Command Room v{version} — Verified

**Date:** {ISO date}
**Plan:** {absolute path to verification plan}
**Plugin staging HEAD:** {git ref}
**Production HEAD (untouched):** {git ref}
**Verification session:** {hours total, M-attention} | {N tests run}

---

## §0. Headline verdict

**Production-promote recommendation:** {SAFE | HOLD | BLOCKED}

**New-customer onboarding:** {SAFE | HOLD | BLOCKED}

**v{next_version} ship scope confirmed:** {YES | PARTIAL | NEEDS_REVISION}

{1-paragraph executive summary of the verification outcome}

---

## §1. Per-phase verdicts

### Phase 0 — Update + sanity checks
{status_emoji} {STATUS}
{tests_passed}/{tests_total} passed

| Test | Verdict | Notes |
|---|---|---|
| ... | ... | ... |

### Phase A — Ship-blocker verification
{status_emoji} {STATUS}
...

[repeat per phase]

---

## §2. Bug fixes verified

| Bug # | Description | Verification | Verdict |
|---|---|---|---|
| {N} | {description} | {test_id} | ✅ LANDED |
| ...

## §3. New bugs surfaced this session

| Bug # | Description | Severity | Target version |
|---|---|---|---|
| {N+1} | {description} | {LOW/MED/HIGH} | {v3.13.8.1 / v3.13.9 / v3.14.x} |
| ...

If zero new bugs: "No new bugs surfaced. The v{version} fix scope is the complete story."

## §4. Architectural strengths confirmed

[List of Strengths #X-#Y verified during this session]

## §5. Test-artifact cleanup

[List of test residue requiring cleanup per Master Plan §8]

## §6. Decision points pending M's call

[Any NEEDS_HUMAN_REVIEW outcomes that weren't resolved during the session]

[Any phase decision gates that surfaced ambiguity]

[Any v3.{next}.x scope questions raised]

## §7. Production-promote checklist

Before promoting v3.6.4 → v{version}, confirm:

- [ ] All Tier 1 ship-blocker tests PASS (Phase A)
- [ ] All Bug #{specific bugs} verifications PASS (per phase decision gates)
- [ ] No new ship-blocker bugs surfaced
- [ ] Update-bridge migration tested against M's mature workspace
- [ ] M-only smoke window completed (24h minimum per Master Plan §10 Decision 5)
- [ ] No critical regressions reported by M during smoke window

**If all checked → PROMOTE.** If any unchecked → HOLD pending resolution.

## §8. v{next_version} scope confirmation

Per Master Plan v{this_version} §9, deferred queue includes:
{list of v3.14.x candidates that weren't in v{version} scope}

This verification session did NOT surface scope changes to v{next_version} unless noted in §3 above.

---

**End of verdict document.**
```

## Verdict logic

The skill computes the headline production-promote verdict per:

```python
def compute_promote_verdict(verdicts: dict) -> str:
    """
    SAFE = all Tier 1 ship-blockers PASS + zero new ship-blocker bugs
    HOLD = Tier 1 mostly PASS but >= 1 PARTIAL on ship-blocker; OR new high-severity bug
    BLOCKED = any Tier 1 FAIL; OR new ship-blocker class bug
    """
    tier_1_tests = [v for tid, v in verdicts.items() if is_tier_1(tid)]
    new_ship_blocker_bugs = [b for b in new_bugs if b.severity == "HIGH" and b.class_ == "ship-blocker"]
    
    if any(v.verdict == "FAIL" for v in tier_1_tests):
        return "BLOCKED"
    if new_ship_blocker_bugs:
        return "BLOCKED"
    if any(v.verdict == "PARTIAL" for v in tier_1_tests):
        return "HOLD"
    if not all(v.verdict == "PASS" for v in tier_1_tests):
        return "HOLD"  # any non-PASS Tier 1 → hold
    return "SAFE"
```

The verdict doc is the final artifact of a verification session. It's what M reviews before clicking the production-promote button.
