# Findings log format

Canonical append-only format for findings log entries. Preserves audit trail across multiple verification sessions.

## Location

Findings log at: `<workspace_root>/TEST_SESSION_FINDINGS_<date>.md` (workspace_root resolved from the operator profile — never a hardcoded machine path)

If multiple findings logs exist, prefer the most recent. If none exist for the current verification session, create one with header:

```markdown
# Command Room v<version> — Verification Session Findings

**Date:** YYYY-MM-DD
**Tester:** the operator (attended mode runs in M's Cowork) + verify-cr-release (via Code chat)
**Plan:** [absolute path]
**Plugin staging HEAD under test:** [git ref]
**Production HEAD:** [cr1 git ref promoted to the ChaletteHQ client repos via promote_core_to_clients.py]
```

## Per-test entry format

Each completed test appends a block:

```markdown
### {test_id} — {test_name} — {verdict_emoji} {verdict}

**Verdict:** {PASS | PARTIAL | FAIL | NEW_BUG | NEEDS_HUMAN_REVIEW}
**Confidence:** {0.0-1.0}
**Fired at:** {ISO timestamp}
**Trigger:** `{trigger_prompt}`

**What landed:**
{bullet list of matched pass signals from response classifier}

**Red flags (if any):**
{bullet list of red-flag signals — empty if PASS}

**Architectural observations:**
{any new patterns or strengths surfaced this fire}

**Cross-references:**
- Known bug verified: Bug #{N} (if applicable)
- New bug surfaced: Bug #{N+1} (if applicable)
- Strength to protect: Strength #{N} (if applicable)

**Evidence (excerpt from Cowork response):**
> {quoted excerpt — 1-3 sentences}

**Speed observation:**
{tool count estimate, render time, notable patterns}
```

## Phase-summary block

After each phase wraps, append a phase-summary block:

```markdown
---

## PHASE {phase_id} — {status_emoji} {STATUS}

{tests_passed}/{tests_total} tests complete

| Test | Verdict | Key findings |
|---|---|---|
| {test_id} | {verdict} | {1-line summary} |
| ...

**Phase decision gate:**
{decision_rule_outcome — e.g., "All Tier 1 ship-blockers verified → green-light prod promote"}

**Verdict for production-promote:** {SAFE | HOLD | BLOCKED}

---
```

## New-bug entry format

When the classifier surfaces a new bug, append:

```markdown
### Bug #{next_id} (NEW) — {brief_name}

**Tech severity:** {LOW | MEDIUM | HIGH}
**CEO lens:** {low/med/high — customer impact}
**Onboarding risk:** {YES | NO | MEDIUM — does this hit Day-1 trust?}
**Surface:** {file path or skill name}

**Symptom (Phase {phase_id} {test_id} {date}):**
{description of what surfaced — include Cowork's verbatim disclosure if helpful}

**Root cause hypothesis:**
{1-2 paragraph analysis}

**Fix shape ({target_version}):**
{specific fix recommendation with file paths if known}

**Class:** {ship-blocker / high-value / nice-to-have / defer-to-vX.Y}

**Evidence:** {test ID + Cowork response excerpt or trace}
```

## Strength-to-protect entry format

When the classifier surfaces a new strength worth protecting:

```markdown
### Architectural strength #{next_id} (added {date}) — {pattern_name}

{2-3 sentence description of the pattern}

**Pattern applies to:** {list of skills this should propagate to}

**Why it matters:** {customer-visible benefit OR architectural property maintained}

**Evidence (from {test_id} {date}):**
> {Cowork verbatim quote demonstrating the pattern}
```

## Append-only discipline

The findings log is canonical audit trail. **NEVER rewrite existing entries.** Always append. If a verdict needs correction (e.g., later evidence overturns earlier PASS), append a new block with a backreference:

```markdown
### {test_id} — VERDICT REVISION (added {later_date})

**Original verdict:** PASS ({original_date})
**Revised verdict:** PARTIAL
**Reason:** {new evidence surfaced via {test_id_or_session}}

{updated evidence}
```

## Version markers

At the start of each verification session, append a session marker:

```markdown
---

## VERIFY-CR-RELEASE SESSION — v{version} — {start_timestamp}

**Plan:** {plan_path}
**Plugin staging HEAD:** {git_ref}
**Tests planned:** {N}
**Variant rotation seed:** {session_id_for_reproducibility}

---
```

End of session marker:

```markdown
---

## SESSION END — v{version} — {end_timestamp}

**Tests completed:** {N}/{planned}
**Verdict breakdown:** PASS={n_pass} / PARTIAL={n_partial} / FAIL={n_fail} / NEW_BUG={n_new} / NEEDS_HUMAN_REVIEW={n_review}
**New bugs surfaced:** {list of bug IDs}
**Production-promote recommendation:** {SAFE | HOLD | BLOCKED}
**Decision doc:** {path to V{version}_VERIFIED_{date}.md if generated}

---
```
