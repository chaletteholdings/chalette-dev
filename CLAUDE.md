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
Run the QA skills (`cr-test`, `verify-cr-release`, `synthetic-workspace-runtime-test`)
against the **synthetic fixtures**. These are repeatable and safe. **The automated
test skills only ever target synthetic fixtures — never a real workspace** (that rule
is about the *test tools*; it does not stop you dogfooding your own Command Room in
Track A).

**The analysis loop (both tracks):** run it in Cowork → paste the output back into
Claude Code → analyze and root-cause here. If it's a machinery bug, write a repro +
fix + a regression test, then open a PR.

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
   Phase 0 checks in `verify-cr-release/references/VERIFICATION_PLAN.md` that touch
   what you changed, and say in the PR how you verified it.
3. Open a PR with a **plain-English explanation**: what it changes, why, the upside,
   and any risk. Assume Matthew is non-technical — write for him.
4. Matthew reviews (he has a skill that lays your PR out for him), approves, and it
   merges to cr1 **staging**. Clients only get it when *he* separately promotes.

Serious/blocking issues: open the PR *and* flag Matthew directly.
