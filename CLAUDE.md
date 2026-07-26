# Working on Command Room — contributor guide (read every session)

This file is auto-loaded by Claude Code. If you're helping a contributor (Eric) work
on Command Room, **follow this workflow and hold these guardrails.** Matthew is the
owner and the only approver; the contributor proposes, Matthew disposes.

## The one question to ask about anything you find

> **Is this the *machinery*, or is this *how the product behaves*?**

- **Machinery** — a bug, broken plumbing, a test, a schema, CI, a dev tool, the
  locking/substrate code. → **Fix it and open a pull request.** This is your lane.
- **Behavior / voice / product judgment** — how a skill reads, its tone, whether a
  brief is too long, what a skill *should* do. → **Do NOT change it. Flag it to
  Matthew in plain English.** That's his call, not yours. The English SKILL.md files
  are the product; don't rewrite prompt logic as code.

When unsure which lane something is in, ask Matthew before touching it.

## Testing — two tracks, both valuable

**Track A — Dogfood your own workspace (be a real user).**
Install Command Room in *your own* Cowork, connected to *your own* email/calendar/
meetings, and use it like a customer — onboarding, morning brief, meeting prep,
drafting. Read the outputs and feel where it's good and where it's off. This is
encouraged and it is *your* data, so it's fine.

**Track B — Controlled regression (synthetic fixtures).**
Run the QA skills (`cr-test`, `synthetic-workspace-runtime-test`, `bug-regression-suite`)
against the **synthetic fixtures**. These are repeatable and safe. **The automated
test skills only ever target synthetic fixtures — never a real workspace** (that rule
is about the *test tools*; it does not stop you dogfooding your own Command Room in
Track A).

**Track C — The structured plan (a fresh, empty test workspace).**
`chalette-dev/skills/cr-test/references/VERIFICATION_PLAN.md`, walked by hand — four
phases, ~5 hours, seeded with a synthetic persona. **This is your plan to maintain**;
keeping it current each release is what makes testing self-sustaining. It is a third
surface, not a synonym for either track above: Track A runs on your mature real
workspace, Track B on fixtures, and this on a **fresh empty folder** — which is the only
way to reach virgin onboarding, honest empty states, and the destructive probes in
Phase 3. Never run it against a real workspace.

Tracks A and C together are `cr test --attended` (tier 5). Nothing automates them — the
skill that used to drive the paste-back loop (`verify-cr-release`) is retired.

**The analysis loop (both tracks):** run it in Cowork → paste the output back into
Claude Code → analyze and root-cause here. If it's a machinery bug, write a repro +
fix + a regression test, then open a PR.

## Single canonical home for the shared toolkit

As of CONSOL1 (2026-07-24) **chalette-dev is the one and only home of the shared QA/dev
toolkit** — the 15 skills here (bug-regression-suite, capture-for-code, cr-test,
cr-skill-builder, ship-readiness-gate, synthetic-workspace-runtime-test, triage-intake,
…). They used to be duplicated into Matthew's private `chalette`
plugin; that copy is gone. Companion references say `chalette-dev:<skill>` (or just
"the <skill> skill"). Guard 1 (`scripts/check_toolkit_overlap.py`) fails the build if a
duplicate of any of these ever reappears in the `chalette` plugin.

## Operator profile — `config/operator.json` (+ optional local overlay)

Every skill that targets a workspace, a clone, or an intake queue resolves it from the
**operator profile**, never a hardcoded path:

- `config/operator.json` — committed, **contractor-safe default** (operator `eric`,
  `allowed_targets: ["synthetic"]`, `may_ship: false`, `may_promote: false`,
  `workspace_root: null`). Edit `cr1_clone` to your own clone; leave the safety keys alone.
- `config/operator.local.json` — **gitignored per-machine overlay.** A reading skill loads
  `operator.json`, then overlays `operator.local.json` per-key. Only Matthew keeps one (it
  carries his real paths and `"real"` in `allowed_targets`). **Do not edit the committed
  `operator.json` into a real-workspace profile** — drop an overlay instead. Guard 2
  (`tests/test_operator_fences.py`) fails CI if the committed default drifts or if
  `operator.local.json` is ever tracked.

Standard read pattern (identical in each reading skill's preflight):

```python
import json, os, sys
op = {}
for _n in ("operator.json", "operator.local.json"):
    _p = os.path.join(SKILL_PLUGIN_ROOT, "config", _n)
    if os.path.exists(_p): op.update(json.load(open(_p)))
# SKILL_PLUGIN_ROOT must be a NATIVE path — on Windows `C:/Users/…`, never an MSYS
# `/c/Users/…` (convert with `cygpath -m`): python.exe reads `/c/…` as `C:\c\…`, both
# files miss, and an empty profile silently becomes the default. Fail loud instead.
if not op: sys.exit(f"FATAL: operator profile unreadable under {SKILL_PLUGIN_ROOT}")
```

**Windows/Git-Bash trap (fixed in MAINT2, 2026-07-24 — do not reintroduce).** The bash
form of this preamble used to build the plugin root from `${BASH_SOURCE[0]}` and `pwd`.
`BASH_SOURCE` is empty when an agent runs the block through a Bash tool (it is not a
sourced script), and `pwd` under Git Bash yields an MSYS path (`/c/Users/…`) that native
`python.exe` resolves to `C:\c\…`. Both config reads missed, the merged profile came back
empty, and every skill silently fell through to its default — an operator granted `real`
ran synthetic with no error. The canonical bash preamble now searches for
`config/operator.json` (with a `$CHALETTE_DEV_ROOT` escape hatch), converts with
`cygpath -m`, and **fails loud** on an unreadable profile. It is delimited by
`# --- operator-profile resolution` / `# --- end operator-profile resolution ---` and
`tests/test_operator_fences.py` executes it out of each SKILL.md on every CI run.

## Hard guardrails

1. **Never push to cr1 directly.** You have read access only. Fork `ChaletteHQ/cr1`,
   branch in your fork, open a PR against `main`. Matthew reviews and merges.
2. **Never ship or promote to clients.** Version bumps, releases, and the client
   fan-out are Matthew's alone. That tooling is deliberately not here.
3. **Real data is for observing, never for committing.** Send Matthew and paste into
   Code any raw real data you want — no need to sanitize what you send *us*. But
   **never commit real data** (real names, emails, machine paths, secrets — yours or
   anyone's) into fixtures, tests, or SKILL.md files. Committed files use approved
   placeholders only. If you spot a real name/path/secret in a diff, flag it and don't
   merge until it's cleaned.
4. **Don't rewrite the English skills as code.** Your lane is the rails around them.

## Submitting work (every change → a PR Matthew approves)

1. Sync `main`, branch off it (`fix/*`, `findings/*`, `ci/*`, `feature/*` — the name
   isn't load-bearing).
2. Run the tests that exist for the repo you're changing. **cr1:** `pip install -r
   requirements.txt` then `python tests/run_all.py` — must be green. **chalette-dev:**
   there is no automated battery here (skills are English prose); instead run the
   Phase 0 checks in `chalette-dev/skills/cr-test/references/VERIFICATION_PLAN.md` that
   touch what you changed, and say in the PR how you verified it. There is also a small
   structural battery — `pytest tests/` (the operator-fence + quick_validate guards) and
   `python scripts/check_toolkit_overlap.py <chalette-dev> <chalette>` — that CI runs on
   every push; run `pytest tests/` locally before opening a PR.
3. Open a PR with a **plain-English explanation**: what it changes, why, the upside,
   and any risk. Assume Matthew is non-technical — write for him.
4. Matthew reviews (he has a skill that lays your PR out for him), approves, and it
   merges to cr1 **staging**. Clients only get it when *he* separately promotes.

Serious/blocking issues: open the PR *and* flag Matthew directly.
