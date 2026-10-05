# chalette-dev: working on the Command Room 2 dev skills

This repo holds the four skills Matthew and Erick share for Command Room 2 work: cr2-report, cr2-scrub, cr2-test and cr2-desk. Read `README.md` first.

## Rules

- **No client data, ever.** No real client, prospect, family member or any real person, and no money figure, in any file, commit, issue or pull request. Sample names only. Run cr2-scrub on anything before it goes up.
- **The skills are plain English on purpose.** SKILL.md is the product; keep it readable by a non-technical owner. Scripts only where a result must be exact (the scrub).
- **One change per pull request.** Matthew merges. Version and CHANGELOG in the same pull request.
- **Never commit** `config/operator.local.json` or `config/scrub.local.json`. The tests fail if the first is tracked.
- **Descriptions say when to fire.** Keep each under 980 characters (the test enforces it), and update `evals/triggers.json` when triggers change.
- No em dashes and no exclamation marks in skill text.

## Checks before a pull request

`pytest tests/` passes, the diff scans clean with cr2-scrub, and the CHANGELOG says what changed and what was verified.

The Command Room 1 toolkit and its long contributor guide moved to Matthew's `chalette` plugin on 2026-10-04 (`chalette/references/CR1_TOOLKIT_GUIDE.md` there).
