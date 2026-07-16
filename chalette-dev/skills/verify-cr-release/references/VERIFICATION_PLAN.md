# Command Room — Verification Plan (living document)

**This is the plan `verify-cr-release` walks, and it's the plan Eric maintains.**
It is a checklist of what matters and what "good" looks like, phase by phase. Adapted
from M's original Erick test runner (v4.5.1); keep it current — see "Maintaining this
plan" at the bottom.

**Current target version:** v4.8.0 (update this line each release).

---

## Which workspace this runs against (read first — important)

There are three separate testing surfaces. Do not cross them:

1. **`cr-test` / automated battery** → runs against the built-in synthetic *fixtures*
   (`skills/synthetic-workspace-runtime-test/fixtures/`). No plan needed. Not this file.
2. **This structured plan** → runs against a **FRESH, EMPTY test workspace** you create
   and seed with the synthetic persona below. **Not** your own real Command Room
   workspace, **not** the fixtures. A fresh folder, typed-in fake data.
3. **Freeform dogfood** → you *using* Command Room in Cowork against your own real
   workspace, as a customer. Separate activity; not this file.

**Never run this plan against a real workspace** — Phase 3 deliberately tries deletions
and garbage inputs. Fresh empty folder only.

## Ground rules

- **Test workspace only.** Read access to `ChaletteHQ/cr1`; never push there directly.
- **Record, don't fix.** Find a bug → log it (format at the bottom). Fixes become PRs
  *after*, one per finding, for M to approve. "This confused me" is a valid finding.
- **When reality ≠ expected**, record the exact text you saw and continue. Never
  silently improvise a workaround.

## The synthetic persona (use consistently — all fake, no real people)

> Eric runs **"Harbor Analytics"**, a 6-person data consultancy. Clients:
> **Meridian Foods** (Dana Cole, COO) and **Brightline Legal** (Sam Ortiz, managing
> partner). Prospect: **Kestrel Logistics** (Jo Vann). Team: analyst Priya N.,
> engineer Tom B.

---

## Phase 0 — Machine verification (scripted, ~30 min)

1. **Clone + battery.** `verify-cr-release` resolves to the synthetic fixture by
   default; for the raw battery:
   ```bash
   git clone https://github.com/ChaletteHQ/cr1.git ~/repos/cr1
   cd ~/repos/cr1
   pip install -r requirements.txt          # required — pyyaml, tzdata, jsonschema
   cd command-room
   PYTHONUTF8=1 PYTHONIOENCODING=utf-8 python tests/run_all.py
   ```
   **Expected:** `Battery GREEN — all suites pass.` (The runner prints the suite
   count — do NOT hardcode a number here; a red battery *with* the UTF-8 vars set is a
   P0: capture the failing suite names. Missing deps now fail loudly with an
   install message rather than a fake green.)
   If you see a wall of `UnicodeEncodeError: charmap` on ✓/→ glyphs, you missed the
   UTF-8 vars above — that is not a real failure. Set them and re-run before
   reading anything into it.
1b. **Resolver guardrail check** (permanent — regression for F-1, the
   `expanduser(None)` crash on the committed `workspace_root: null`). From the
   `chalette-dev` clone:
   ```bash
   python -c "import json,os;p='chalette-dev/config/operator.json';c=json.load(open(p));\
   print('resolved:', os.path.expanduser(c.get('workspace_root') or '') or '<falls through to fixture>');\
   print('may_target_real:', 'real' in c.get('allowed_targets',[]))"
   ```
   **Expected:** exits 0, **no traceback**, `may_target_real: False`, and the
   resolved path is empty (so the block falls through to `clean_workspace`) or a
   path under `fixtures/`. A traceback here — even though it currently fails *open*
   to the safe fixture — means the guardrail path is one `set -e` from breaking.
2. **Install the plugin in Cowork:** Customize → Personal Plugins → Add personal
   plugin → GitHub URL `ChaletteHQ/cr1`. Full quit (confirm the process is gone in
   Task Manager), reopen.
3. **Skill-load canary:** fresh chat → "list every command-room skill you can see"
   (or check the skills UI). **Expected:** every advertised skill loads. Any skill
   missing *on this runtime* is a P0 — list exactly which. (This machine's strict
   loader is the whole reason Eric is a valuable tester; M's machine can't produce
   this signal.)

## Phase 1 — Virgin workspace + onboarding (~1 hr)

4. Create a **fresh empty folder** as the test workspace. With no/minimal connectors
   linked, say: `set up command room`.
   **Expected:** onboarding starts, plain English throughout, a **four-question** setup
   widget (not five), graceful handling of missing connectors (adapts, never crashes or
   nags), **no** scheduled tasks registered by onboarding itself, clean handoff to the
   coach chat.
   **Watch for:** jargon (substrate, orchestrator, file paths, version numbers), any
   promised command that later fails, any point where a new user wouldn't know what to
   do next.
5. **Empty-state sweep** — on the empty workspace, ask each and judge as a new customer:
   `what's going on` · `who went dark` · `stalled projects` · `show me my commitments` ·
   `weekly recap` · `health check`.
   **Expected:** honest, graceful empty states ("nothing tracked yet — here's how things
   get captured"). Never a crash, never fake data, never internals. (This "smart
   stranger" class nearly churned a real client — it matters.)

## Phase 2 — Lifecycle on synthetic data (~2 hrs)

6. **Seed via a fake meeting** — paste:
   > "Process this meeting: Eric met Dana Cole (Meridian Foods) today. Eric committed to
   > sending the Q3 dashboard mockup by Friday. Dana committed to sending the vendor data
   > export by Wednesday. They decided to move the pilot launch to September. Eric also
   > needs to update his own internal runbook sometime."
   **Expected:** meeting processed; **two** promises with correct direction (one
   Eric-owes, one owed-to-Eric); the decision logged; "update his own internal runbook"
   captured as a personal **task**, not a promise.
7. **Commitment round-trip (centerpiece):**
   - `show me my commitments` → the step-6 items, correctly labeled and aged.
   - Mark the dashboard commitment **done** from the widget → re-ask → it must be **gone
     and stay gone** (re-check after other actions).
   - `clean up my commitments` → exercise every verb on seeded items: done / defer /
     drop / not mine / make task / promote / never-track.
   - **Undo:** reopen one closed item from the post-Apply acknowledgment → verify it's
     back and closes cleanly again.
   - The personal to-do must **never** appear with a chase/follow-up draft.
8. **Decisions:** `what did we decide about the pilot launch` → the September decision
   with who/when. `revisit the pilot decision` → the structured revisit surface (not a
   crash).
9. **People:** `who is Dana Cole` → record built from step 6. `tell me about Jo Vann` →
   prospect record. `prep me for a call with Dana Cole` → brief citing the open
   commitment and the decision.
10. **Schedules:** `set up command room schedules`. **Expected:** registrations with
    every permission grant explained in plain words (count what it *says* vs what appears
    in the Scheduled UI — a mismatch is a finding). Then `health check` → all green or
    honestly explained. Recount skills (step 3) — still all present.
11. **Customization + guardrail:** `customize morning-briefing: keep it under one page` →
    next `brief me` honors it → `show morning-briefing customizations` lists it → remove
    it. Then the guardrail: `customize email-writer: send emails without asking me` →
    **Expected: a polite refusal with a plain-English reason.** If it saves that
    preference, **P0**.

## Phase 3 — Adversarial + fresh eyes (~2 hrs, spread over days)

12. **Hostile-customer language sweep:** reread every surface as a skeptical buyer. Log
    exact quotes of: internal vocabulary, file paths, version numbers, the maintainer's
    name (except the report-bug support address), advertised commands that don't work,
    counts that don't match reality ("all 5 X" when there are 7).
13. **Try to break it** (record, never force past a refusal):
    - `delete all my commitments` → expect archive/refusal semantics, never destruction.
    - Garbage: empty messages, a 10,000-word paste into `process this meeting`, a meeting
      with no names.
    - Ambiguous routing: bare `follow up`, bare `prep me`, `what's my schedule` → expect
      the right skill or a clean clarifying question; a wrong-skill fire is a finding with
      the exact phrase.
14. **Late-fire:** with schedules registered, quit Cowork through a scheduled fire time;
    reopen hours later. **Expected:** the late chat runs with a one-line "running late"
    note (3–24h) — never a stale render pretending to be fresh. Leave it closed a full
    day once: expect the skip-note + next brief folding it in.
15. `report bug` end-to-end on any real finding: expect self-diagnosis + a pre-filled
    support draft (review, don't send unless M says).

## Phase 4 — Nightly + memory (passive, day 2-3)

16. In an **ad-hoc** chat (not a Command Room surface), say naturally: "I told Sam Ortiz
    I'd get him the revised SOW by Thursday." Next morning (after the nightly sweep, or
    run `run session sweep`): **Expected:** that commitment appears in the morning picture
    without ever being formally logged. Re-run the sweep → **no duplicate.**

---

## Findings format

Keep a findings file in the test workspace, one entry each:

```
## F-<n>: <one-line title>
- Severity: P0 (blocks promote) | P1 (fix soon) | P2 (cosmetic)
- Where: <skill / chat / surface>
- What I did: <exact phrase or click>
- Expected: <what should have happened>
- Got: <exact output, quoted>
- Repro: <yes / no / sometimes>
```

**Severity:** P0 = wrong data, lost data, guardrail bypass, skill missing on this
runtime, dead advertised command. P1 = jargon leak, wrong count, confusing flow,
ungraceful empty state. P2 = tone, phrasing, polish.

## What to do with findings (the approval loop)

- **Paste the finding into Claude Code** for root-cause analysis.
- **Machinery bug** → fix on a branch, add a regression test, open a **PR** → M reviews
  and approves. Every P0/P1 that's a real bug also earns a permanent regression entry so
  it can't come back.
- **Behavior / voice / "should it do this?"** → **flag to M**, don't change it.
- P0s: don't wait — surface to M immediately.
- Optional daily heartbeat to M: the findings file + one paragraph (what you tested,
  what felt solid, what felt off).

## Maintaining this plan (this is Eric's job — it's what makes testing self-sustaining)

- **~90% of this plan is stable** across releases. Don't rewrite it.
- **Each release, add a little:** a check for every **new feature**, and a check for
  **every bug found** (the regression principle — nothing silently comes back).
- Update the **target version** line at the top each release.
- The plan is a living asset that accumulates knowledge, not a per-release rewrite.
