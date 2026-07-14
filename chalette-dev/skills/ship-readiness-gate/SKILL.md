---
name: ship-readiness-gate
description: "INTERNAL — automated post-push verification orchestrator. Fires in Code (M's plugin-dev environment) after a push to chaletteholdings/commandroom1 main. Detects the fresh ship, then runs the full canonical-surface verification battery against all synthetic fixtures + cross-references findings against the bug catalog + emits a PROMOTE/HOLD/BLOCKED verdict doc. No M paste-back loop required — fully unattended. Triggers: 'ship readiness gate', 'post-push verify', 'production rehearsal', 'pre-promote check'. Used to gate the production-promote decision (v3.6.4 → v{shipped}) without needing M to walk a Cowork verification cycle manually. Plugin-developer use only. Companion to verify-cr-release (M-attended Cowork loop), synthetic-workspace-runtime-test (per-fire code-path gate), compare-canonical-vs-freelance (per-skill ladder validation)."
---

# ship-readiness-gate

**The fully-unattended pre-promote verification gate.** Fires in Code immediately after M pushes to chaletteholdings/commandroom1 main. Runs the full verification battery automatically (no Cowork paste-back loop) + emits a PROMOTE / HOLD / BLOCKED verdict on production-promote decision.

## Why this skill exists

Per V3.13.8_MASTER_PLAN §10 Decision 5: production-promote follows a 24h M-only smoke window AFTER ship to staging. That smoke window is currently manual — M fires things in Cowork, checks for issues, decides whether to promote.

**This skill compresses the smoke window** by running an automated battery against synthetic fixtures + invariant assertions + bug-catalog cross-reference + emitting a PROMOTE verdict. M reviews the verdict doc (~5 min instead of 24h watch).

Caveat: this skill catches code-path issues but NOT Cowork-side LLM behavior. Final decision still M's. But the gate eliminates ~80% of the bug classes that have surfaced post-ship historically.

## When this fires

| Trigger | Context |
|---|---|
| `ship readiness gate` | Manual fire after a recent push |
| `post-push verify` | Same |
| `production rehearsal` | Same |
| `pre-promote check` | Same |
| `ship readiness gate --auto-detect` | Auto-detect fresh push via git log; abort if HEAD is > 24h old |
| `ship readiness gate --target=m-workspace` | Run battery against M's actual workspace (NOT synthetic fixtures) — preferred since fixtures unpopulated as of chalette v0.6.0 |
| `ship readiness gate --target=synthetic` | Run battery against synthetic fixtures (requires fixtures populated) |

DOES NOT fire on `verify cr release` (that's the M-attended Cowork loop). DOES NOT fire on `run synthetic workspace test` (that's a single-fixture single-skill test).

### Target mode behavior

**Per M's preference (2026-05-24): default target is M's actual workspace**, not synthetic fixtures. Reasons:
- M's workspace is realistic-scale with edge cases (more thorough than skeleton fixtures)
- Skeleton fixtures don't fully exercise canonical helpers yet
- Real-customer testing IS the bar for "this ships safely"

The skill runs:
- **bug-regression-suite** against M's workspace (with safety: pre-snapshot + test_artifact tagging + cleanup helper)
- **cross-skill-interaction-test** against M's workspace (multi-fire sequences with substrate snapshots)
- **synthetic-workspace-runtime-test** only if fixtures populated (else skipped with note)
- **compare-canonical-vs-freelance** post-v3.13.8 only

Always uses bug-regression-suite + cross-skill-interaction-test as primary gates. Synthetic + compare-canonical are SUPPLEMENTARY gates that activate when their dependencies are met.

## Behavior

### Step 0 — Detect fresh push

```bash
# Locate the Command Room staging clone
STAGING_ROOT=~/.claude/plugins/marketplaces/commandroom1/command-room

cd "$STAGING_ROOT"
git fetch origin main --quiet
LAST_COMMIT_TS=$(git log -1 --format="%ct" origin/main)
NOW=$(date +%s)
AGE_HOURS=$(( (NOW - LAST_COMMIT_TS) / 3600 ))

if [ "$AGE_HOURS" -gt 24 ]; then
    echo "ABORT: most recent commit is $AGE_HOURS hours old — not a fresh ship"
    exit 1
fi

VERSION=$(jq -r .version "$STAGING_ROOT/.claude-plugin/plugin.json")
COMMIT_REF=$(git rev-parse --short origin/main)
echo "Verifying ship: v$VERSION at $COMMIT_REF"
```

If no recent push detected and trigger wasn't `--force`, abort cleanly. M can override with `ship readiness gate --force` to run anyway.

### Step 1 — Run synthetic-workspace-runtime-test against all 4 fixtures

```python
fixtures = ["clean_workspace", "mature_workspace", "degraded_workspace", "fresh_install"]
canonical_surfaces = [
    "morning-briefing", "orchestrator-inbox", "orchestrator-commitments",
    "orchestrator-dont-forget", "orchestrator-upcoming-meetings", 
    "orchestrator-past-meetings", "orchestrator-friday-wrap",
]

verdicts = {}
for fixture in fixtures:
    for surface in canonical_surfaces:
        result = run_synthetic_fire(fixture, surface)
        invariant_failures = verify_invariants(result, surface, fixture)
        verdicts[(fixture, surface)] = invariant_failures
```

See `synthetic-workspace-runtime-test/SKILL.md` for the invariant catalog (18 invariants per fire).

### Step 2 — Run compare-canonical-vs-freelance against widget-rendering skills

For each skill that renders interactive widgets, run the side-by-side diff:

```python
widget_skills = [
    "email-writer", "intro-broker", "follow-up-ritual", "thread-resurrection",
    "calendar-writer", "commitments", "show-my-list", "decision-memo-composer",
]
for skill in widget_skills:
    diff = run_canonical_vs_freelance(skill)
    verdicts[(skill, "ladder_compliance")] = check_ladder_compliance(diff)
```

(post-v3.13.8 only; pre-v3.13.8 this step skips with "BLOCKED — depends on §2.1")

### Step 3 — Cross-reference against bug catalog

For every PASS/FAIL outcome, cross-reference against the latest findings log:

```python
findings_log = Path("~/Desktop/Claude/Command Room/TEST_SESSION_FINDINGS_2026-05-21.md")
known_bugs = parse_bug_catalog(findings_log)

# Did any KNOWN bug surface in this run? (regression detection)
regressions = []
for verdict in verdicts.values():
    if verdict.has_failures():
        matched_bugs = match_against_catalog(verdict, known_bugs)
        if matched_bugs:
            regressions.extend(matched_bugs)

# Did any NEW failure surface that doesn't match catalog? (new bug class)
new_failures = [v for v in verdicts.values() if v.has_failures() and not v.matched_known_bug]
```

### Step 4 — Aggregate verdict

```python
verdict = compute_ship_readiness_verdict(verdicts, regressions, new_failures)

# Logic:
# BLOCKED — any Tier 1 ship-blocker test FAILED OR any KNOWN ship-blocker bug regressed
# HOLD — any Tier 2 fix verification PARTIAL OR new failure class surfaced
# PROMOTE — all Tier 1 PASS, no regressions, no new failures
```

### Step 5 — Emit verdict doc

Write `Desktop/Claude/Command Room/SHIP_READINESS_v{version}_{date}.md`:

```markdown
# Ship Readiness Gate — v{version}

**Date:** {ISO}
**Ship commit:** {ref}
**Auto-fired:** {true | false}
**Verdict:** {PROMOTE | HOLD | BLOCKED}

## §1. Surface verification — synthetic fixtures

{tabular results per fixture × surface}

## §2. Widget ladder compliance — render-path diffs

{per-skill canonical vs freelance verdict}

## §3. Known bug regression check

{any bugs from catalog that reappeared}

## §4. New failure classes detected

{any failures that don't match catalog — surface for M's call}

## §5. Production-promote recommendation

{PROMOTE | HOLD | BLOCKED} with rationale

{If PROMOTE:}
**You may safely run:**
- git push origin main → chaletteholdings/commandroom main
- OR run ship-cr-plugin Step 9 production promote

{If HOLD:}
**Pending:**
- {list of items needing M's judgment call}

{If BLOCKED:}
**Must fix before promote:**
- {list of failing tests + likely cause + recommended action}
```

### Step 6 — Surface to chat

```
Ship Readiness Gate — v3.13.8

Verifying ship at commit abc1234 (2 hours ago)...

Synthetic fixtures: 4/4 fired
Canonical surfaces: 7/7 per fixture (28 total fires)

PASS: 27/28 fires
PARTIAL: 1/28 (mature_workspace × morning-briefing — I6 defensive_read partially fired but skipped_lines not surfaced)

Widget ladder compliance: 8/8 skills
PASS: 8/8

Known bug regression check: 0 regressions detected
- Bug #4 email cascade: not regressed ✓
- Bug #14 commitments transmission: not regressed ✓
- Bug #19 disambiguation: not regressed ✓
- ... (all 21 known ship-blockers checked)

New failure classes: 1 detected
- morning-briefing × mature_workspace: defensive_read called but skipped_lines not surfaced to user
- Likely cause: Bug #52 fix partially incomplete

VERDICT: HOLD

Recommended action: review the morning-briefing skipped_lines surface; either fix in v3.13.8.1 OR accept as known-residual-fix.

Full report: Desktop/Claude/Command Room/SHIP_READINESS_v3.13.8_2026-05-25.md
```

## What this skill catches

**High coverage:**
- Canonical render path bypass (Bug #32 + #45 + #52 + #53 class) — synthetic invariants I1, I2, I7, I8, I9
- Substrate corruption tolerance (Sub-bug #14b family) — invariant I6 against mature_workspace fixture
- Schema compliance (Bugs #24, #34, #43, #49) — invariant I10
- Leak gate (Bugs #54, #57, #59) — invariant I5 + universal post-render scan
- Atomic-write multi-write deadlock (Bug #20) — invariant I14
- Widget ladder adherence (Bug #46) — compare-canonical-vs-freelance ladder verdict
- Action-label drift (Bug #48) — caught in widget ladder compliance

**Partial coverage:**
- Voice contract violations (Bugs #16, #60) — synthetic captures chat narration; word-boundary scan applies; but LLM-driven variations limit detection
- Cross-mount corruption (Bug #55) — environmental, can't be reproduced synthetically

**NO coverage (still requires Cowork-side verify-cr-release):**
- Cowork LLM judgment quality
- Voice / tone subjective assessment
- Customer-specific edge cases not in fixtures
- Cowork's prompt-pattern-matching adaptation over time

**Conclusion:** This skill is ~80% of pre-promote verification. The remaining 20% needs verify-cr-release on M's actual workspace.

## Verdict logic

```python
def compute_ship_readiness_verdict(verdicts, regressions, new_failures) -> str:
    """
    BLOCKED — any Tier 1 ship-blocker test FAILED OR any KNOWN ship-blocker bug regressed
    HOLD — Tier 2 verifications PARTIAL OR new failure class surfaced
    PROMOTE — all Tier 1 PASS, no regressions, no new failures
    """
    tier_1_failures = [v for v in verdicts.values() if v.is_ship_blocker and v.failed]
    if tier_1_failures:
        return "BLOCKED"
    
    ship_blocker_regressions = [r for r in regressions if r.severity == "HIGH"]
    if ship_blocker_regressions:
        return "BLOCKED"
    
    tier_2_partials = [v for v in verdicts.values() if v.is_high_value and v.partial]
    if tier_2_partials or new_failures:
        return "HOLD"
    
    return "PROMOTE"
```

## Connection to V3.13.8_MASTER_PLAN

This skill operationalizes V3.13.8_MASTER_PLAN §10 Decision 5 (24h M-only smoke before promote). Instead of M watching for issues over 24h, this skill compresses the gate to ~10 minutes of automated verification + ~5 min M review of the verdict doc.

The compression doesn't ELIMINATE the smoke window — M still observes real-use behavior in Cowork over the following 24h before final promote click. The gate just adds a high-confidence automated checkpoint at the beginning of that window.

## Failure modes

**Synthetic fixtures not populated:** skill returns "BLOCKED — fixtures need population" with clear pointer to fixtures/README.md. (This is the v0.6.0 ship state until fixtures filled in.)

**Plugin code path crashes during synthetic fire:** captured in trace; surfaces as a CRASH verdict rather than PASS/FAIL. Surfaces stack trace for M debugging.

**Bug catalog drift:** if findings log moved or renamed, skill falls back to last-known-good catalog + flags the issue.

**Pre-v3.13.8 ship:** `compare-canonical-vs-freelance` returns BLOCKED for the §2 step; gate continues with just synthetic + catalog cross-reference.

## Pre-promote workflow (M's daily ritual once v3.13.8 ships)

```
1. (Code session) Implement v3.13.8.X fixes per master plan
2. Run pre-commit hook + tests pass
3. git push to chaletteholdings/commandroom1 main
4. (Same Code session) ship readiness gate
5. Review SHIP_READINESS_v3.13.8.X_<date>.md
6. If PROMOTE → safe to fire ship-cr-plugin Step 9 production promote
   If HOLD → check the partial-pass items + fix in v3.13.8.X+1 OR accept residual
   If BLOCKED → must fix the blocker before any promote consideration
```

## Implementation references

- `references/verdict-logic.md` — full ship-readiness verdict decision tree
- `references/bug-catalog-parser.md` — how to extract bug records from findings log
- `references/regression-matching.md` — how to detect known-bug regressions in test failures
- Reuses `synthetic-workspace-runtime-test` fixture system + invariant catalog
- Reuses `compare-canonical-vs-freelance` ladder validation logic
