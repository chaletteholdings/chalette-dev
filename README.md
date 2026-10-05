# chalette-dev: Command Room 2 dev skills

The skills Matthew and Erick share to report, scrub, test and plan work on Command Room 2 (`ChaletteHQ/cr2`). Install this plugin and both of you work the same way.

As of v0.7.0 (2026-10-04) this repo holds **only** the Command Room 2 dev skills. The Command Room 1 QA toolkit (cr-test, bug-regression-suite, cr-skill-builder and the rest) moved to Matthew's private `chalette` plugin.

## The four skills

| Skill | Say | What it does |
|---|---|---|
| `cr2-report` | "report this", "file a bug", "spec it" | Turns the chat where something broke, or an idea, into one GitHub issue on cr2: facts tagged by source, severity, a "for whoever fixes it" block, a build brief for features. |
| `cr2-scrub` | "scrub this", "scrub the repo" | Keeps client names, personal information and money figures out of the repo. Builds the name list fresh from your own book. |
| `cr2-test` | "what needs me", "test #N" | Your acceptance test on a fix: a short script, the original failure run 3 times, the result posted to the issue. |
| `cr2-desk` | "what's pending to build", "get #N ready" | Everything pending in plain language from the client's side, and a short multiple-choice briefing that becomes the build brief. |

Building from an issue is `cr2-build`, a project skill inside the cr2 repo itself.

## Who decides

Each skill reads `operator` from `chalette-dev/config/operator.json`, with a gitignored `config/operator.local.json` laid over it. The committed file is Erick's profile. Matthew's overlay says `"operator": "m"`.

- **Matthew** files everything as `core` by default and moves an item to `labs` himself; he tests on his preview (`ChaletteHQ/cr2-preview`) before Louis merges and closes an issue after the final check.
- **Erick** gets the same steps, with those decisions turned into proposals tagged for Matthew.

## Setup

1. Clone: `git clone https://github.com/ChaletteHQ/chalette-dev ~/repos/chalette-dev`
2. Install the plugin in the Claude app from this repo.
3. Matthew only: add `chalette-dev/config/operator.local.json` with `{"operator": "m", "operator_name": "Matthew"}`.
4. Optional, each person: `chalette-dev/config/scrub.local.json` with private lists for the scrub (format at the top of `skills/cr2-scrub/scripts/scrub_scan.py`). Never commit it.
5. In your cr2 clone, the scrub guard runs before every commit: see `04_tools/hooks/README.md` there.

## Checks

`pytest tests/` (also on every push): operator fences, `quick_validate` on every skill (`scripts/quick_validate.py`, vendored from Anthropic's skill-creator, Apache 2.0), and the description budget. Each skill has `evals/triggers.json`: phrases that should start it and near misses that should not.
