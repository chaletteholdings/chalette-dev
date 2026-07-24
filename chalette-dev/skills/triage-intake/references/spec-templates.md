# Spec templates

Two M-side spec sizes (below), plus the outbound **contributor packet** wrapper and the **BACKLOG.md** shape at the end — those two are `may_ship`-only and post-scrub; see SKILL.md "Routing work out".

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

## Contributor packet (`may_ship` only) — `<specs_dir>/packets/PACKET_<TAG>.md`

Emitted ONLY when the Eric-suitability test passes on a `may_ship: true` profile, and ONLY after the scrub gate clears (`scrub_roster` null/unreadable → refuse, spec-only). Never committed into cr1.

The **body** (§0–§7) is shaped per cr1's checked-in `templates/TEMPLATE_SPEC.md` — read it from the clone at write time, do not copy it here; the contributor's fork carries the same file and `CONTRIBUTING.md` binds them to it. One spec grammar on their side of the fence. The wrapper below is what goes AROUND that body.

```markdown
# PACKET_<TAG> — <outcome, plain terms>

**Repo:** `ChaletteHQ/cr1` — fork → branch in your fork → PR against `main`. Reviewed and merged by the maintainer; never self-merged. Read `CONTRIBUTING.md` in the repo root first.
**BACKLOG row:** `<TAG>` (repo-root `BACKLOG.md`). Say so when you claim it.
**Branch:** suggested `<tag>-<short-name>`.
**Battery:** `PYTHONUTF8=1 python tests/run_all.py` from `command-room/` — baseline **<N>/0**, re-verify at branch time.

**What you never do** (mirrors CONTRIBUTING.md "What contributors never do"):
- No version bumps, no CHANGELOG entries, no release manifests.
- No promote / fan-out to client repos.
- No filled BUILD/REVIEW records committed into the repo — that content goes in the PR description.
- No merge. STOP at review.

---

<the spec body, §0–§7 per cr1 templates/TEMPLATE_SPEC.md. §0 rows are ALREADY RULED —
a packet never ships with an open "AWAIT ruling" row. Acceptance carries the scrub AC verbatim:
"no real client, person, or org name in any changed file or anywhere in the branch history —
grep over the worktree AND full `git log -p` over every commit on the branch against the
roster (`command-room/references/PRIVACY_POLICY.md`). Second-eyes re-runs this independently.">

---

## Your PR description must contain

The `templates/TEMPLATE_BUILD_REPORT.md` slots — the PR description IS the build record for fork contributors (filled records are never committed):

- **Deviations from this packet, loud, at the top** — anything you built differently, and why.
- **Gates table with numbers** — full battery (N passed / N failed), guard tier, and the mutation check *demonstrated by removing the fence* (a regression test that never went red proves nothing). Show both numbers.
- **Files touched** — every path, one line each on what changed.
- **Reviewer-visible defaults** — every judgment call you made that the packet did not rule.
- The org-name rule applies to PR text too: placeholder names only.

---

## BACKLOG.md — shape + covenant (repo root of cr1)

Staged with `git add`, never committed or pushed by triage. Seeded shape:

```markdown
# BACKLOG — specs ready for contributor pickup

Ready-to-build items with a maintainer-written spec behind each one. Ask the maintainer for the packet by TAG; packets come from the maintainer, not this repo.

**Covenant:** every row is scrubbed — phrased by mechanism, placeholder names only, no client/org/person names and no maintainer-workspace paths. Maintained by the maintainer's triage tooling, staged only; the maintainer pushes. Process and gates: [CONTRIBUTING.md](CONTRIBUTING.md).

| TAG | Outcome | Size | Status |
|---|---|---|---|
```

Row grammar: `| <TAG> | <one line, mechanism-phrased> | S/M/L | READY \| CLAIMED — PR #<n> \| MERGED @ <short-SHA> |`. Rows are added when a packet is emitted; statuses flip on reconciliation; `MERGED` rows are deleted after one run of visibility (git holds the history). No `parked` status — `parking_doc` owns parking; BACKLOG lists READY-or-in-flight only.

---

## Intake-file pointer rewrite (after the spec lands)

Replace the intake file's body (keep frontmatter) with:

```markdown
**Superseded by `specs/SPEC_<TAG>_<snake_name>.md` — <date>.** Triage verdict: <CONFIRMED L1 / SPEC / ...>. History below the line.

---
<original body, unchanged>
```

Then move the file to `speced/`.
