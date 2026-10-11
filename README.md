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

Each skill works out who is running it in this order: a gitignored `config/operator.local.json` when present (Matthew's says `"operator": "m"`), then the GitHub account the session posts as (`chaletteholdings` is Matthew, `erick559` is Erick, anyone else is treated as Erick), then the committed `chalette-dev/config/operator.json` (Erick's profile). The GitHub check is what lets web and phone chats, which never have the local file, know Matthew. The skill says who it took you for in its first reply.

- **Matthew** confirms what gets filed and closes an issue on a passing test.
- **Erick** gets the same steps, with those decisions turned into proposals tagged for Matthew.

## Setup

1. Clone: `git clone https://github.com/ChaletteHQ/chalette-dev ~/repos/chalette-dev`
2. Install the plugin in the Claude app from this repo.
3. Matthew only, optional: add `chalette-dev/config/operator.local.json` with `{"operator": "m", "operator_name": "Matthew"}`. Not needed when your GitHub account is signed in; it only matters on a computer where it isn't.
4. Optional, each person: `chalette-dev/config/scrub.local.json` with private lists for the scrub (format at the top of `skills/cr2-scrub/scripts/scrub_scan.py`). Never commit it.
5. In your cr2 clone, the scrub guard runs before every commit: see `04_tools/hooks/README.md` there.

## Checks

`pytest tests/` (also on every push): operator fences, `quick_validate` on every skill (`scripts/quick_validate.py`, vendored from Anthropic's skill-creator, Apache 2.0), and the description budget. Each skill has `evals/triggers.json`: phrases that should start it and near misses that should not.
