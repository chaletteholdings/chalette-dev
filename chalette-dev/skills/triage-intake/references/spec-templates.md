# Spec templates — two sizes

Pick by item size. Never inflate a bug into the feature skeleton; never compress a multi-decision feature into the bug form. Both land in `<intake_root>/specs/` (intake_root from `config/operator.json`).

---

## Bug-fix spec (≤1 page) — `SPEC_<TAG>_<snake_name>.md`

```markdown
# SPEC_<TAG> — <one-line symptom, user-visible phrasing>

> Build spec for a fresh session. Repo: <cr1_clone> (git: ChaletteHQ/cr1; do NOT bump version/CHANGELOG — releases stay with M). Baseline: main @ **<SHA>** (<date>) — pull and verify before starting; battery baseline **<N>/0**. Land on a branch, deliver as a PR for review. Read this entire file before writing code.
> Origin: intake `<intake-file-id>`, captured <date>. Verified at triage <date> (verdict CONFIRMED, level L<1/2/3>).

## 1. Verified diagnosis
<file:line refs + root cause, re-verified by reading — grounded @ <SHA>. State what the capture's hypothesis got right/wrong.>

## 2. Fix approach
<the change, in 2-6 sentences. Rejected alternatives in one line each if any were close.>

## 3. Blast radius (same-class sweep)
<sweep result: N sites, listed. Fix scope: surgical / sweep / structural — and why.>

## 4. Regression test (mandatory)
<suggested test file + the specific assertions; synthetic-fixture-shaped data, placeholder names only; prefer negative pins (assert the bad behavior is GONE) over positive ones.>

## 5. Out of scope
<explicitly — adjacent staleness the sweep found but this spec does not authorize.>

## 6. Acceptance
- New regression test green; full battery `tests/run_all.py` green (re-verify live baseline at branch time).
- No real client/org names anywhere on the branch (full `git log -p`, all commits).

## 7. Kickoff prompt (paste as first message of the build session)
<paste-ready block: repo, branch name suggestion, "read SPEC_<TAG> in full, build §2, prove §6, deliver as PR">
```

---

## Feature / skill spec (≤3 pages) — `SPEC_<TAG>_<snake_name>.md`

```markdown
# SPEC_<TAG> — <outcome, plain terms>

> Build spec for a fresh session. Repo: <cr1_clone> (git: ChaletteHQ/cr1; do NOT bump version/CHANGELOG). Baseline: main @ **<SHA>** (<date>) — pull and verify; battery baseline **<N>/0**. §2 refs grounded @ <SHA> — RE-VERIFY by reading before editing. Land on a branch, deliver as a PR for review. Read this entire file before writing code.
> §0 status: <"all ruled — build" / "D1, D3 AWAIT ruling — DO NOT BUILD">
> Origin: intake `<intake-file-id>`, captured <date>; triaged <date>. ICE <I×C×E>.

## 0. Open decisions
| # | Decision | Options | Recommended default + why | Status |
|---|---|---|---|---|
<every genuine fork gets a row with a recommended default — flag ambiguity, never silently guess. Blocking decisions marked AWAIT ruling.>

## 1. Goal
<the outcome: "the user can ___." One paragraph. What "done" looks like from the chair.>

## 2. Current state (grounded @ <SHA> — re-verify by reading)
<surfaces/files the build touches; nearest existing skill + why it doesn't cover this (from the overlap check); trigger-collision findings.>

## 3. Design decisions
**D1 — ...** <each ruled decision, with mechanism.>
**Acceptance criteria (EARS-lite):**
- WHEN <trigger/condition> THE SYSTEM SHALL <behavior>
- WHEN <failure/edge condition> THE SYSTEM SHALL <behavior>   ← at least one failure-mode line
**Rejected:** <alternatives + why, one line each.>

## 4. Contract-gate notes
<only the gates this build actually trips: new event types → events.schema.json enum + EVENT_TYPES.md + named consumer; name-bearing triggers → ENTITY_RESOLVE gate; privacy → placeholder names only; widgets → canonical verbs + render_and_persist; first-run questionnaire ≤5; scheduled → SILENT_TASKS + watchdog receipt. Route the finished skill through cr-skill-builder AUDIT mode before it ships.>

## 5. Build order
1. Branch off main (suggested: `<tag>-<name>`).
2. <changes in dependency order>
3. New test file `tests/run_<tag>_test.py` — <the assertions that pin §3's EARS lines>.
4. Full battery green + name sweep, deliver as PR.

## 6. Out of scope
<explicit — the adjacent wishes this spec does not authorize.>

## 7. Kickoff prompt (paste as first message of the build session)
<paste-ready block.>
```

---

## Intake-file pointer rewrite (after the spec lands)

Replace the intake file's body (keep frontmatter) with:

```markdown
**Superseded by `specs/SPEC_<TAG>_<snake_name>.md` — <date>.** Triage verdict: <CONFIRMED L1 / SPEC / ...>. History below the line.

---
<original body, unchanged>
```

Then move the file to `speced/`.
