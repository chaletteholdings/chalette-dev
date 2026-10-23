# chalette-dev: working on the Command Room 1 dev skills

This repo holds the four skills Matthew and Erick share for Command Room 1 work (`ChaletteHQ/cr1`): cr1-report, cr1-scrub, cr1-test and cr1-desk. Read `README.md` first.

## Rules

- **No client data, ever.** No real client, prospect, family member or any real person, and no money figure, in any file, commit, issue or pull request. Sample names only. Run cr1-scrub on anything before it goes up.
- **The skills are plain English on purpose.** SKILL.md is the product; keep it readable by a non-technical owner. Scripts only where a result must be exact (the scrub).
- **One change per pull request.** Matthew merges. This repo's own version and CHANGELOG go in the same pull request. (That rule is for this repo only; in cr1 a pull request never touches the version or CHANGELOG, which are set at release.)
- **Never commit** `config/operator.local.json` or `config/scrub.local.json`. The tests fail if the first is tracked.
- **Descriptions say when to fire.** Keep each under 980 characters (the test enforces it), and update `evals/triggers.json` when triggers change.
- **Keep `scrub_scan.py`'s `terms` and `scan` commands stable.** cr1's pre-commit guard calls them from `~/repos/chalette-dev/chalette-dev/skills/cr1-scrub/scripts/scrub_scan.py`.
- No em dashes and no exclamation marks in skill text.

## Checks before a pull request

`pytest tests/` passes, the diff scans clean with cr1-scrub, and the CHANGELOG says what changed and what was verified.

Building from an issue is cr1-build, a project skill inside the cr1 repo. Command Room 2 was retired on 2026-10-22; these skills were its cr2-* skills until v0.8.0.
