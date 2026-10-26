# chalette-dev: the Command Room dev toolkit

New to the team? Start with [docs/TEAM_GUIDE.md](docs/TEAM_GUIDE.md). Brand and positioning during the rebrand: [docs/POSITIONING_AND_BRAND_SHEET.md](docs/POSITIONING_AND_BRAND_SHEET.md).

The skills the owner and the team share to report, scrub, test and plan work on Command Room 1 (`chaletteholdings/cr1`, branch `main`). Install this plugin and both of you work the same way.

As of v0.8.0 (2026-10-22) the skills target cr1. Command Room 2 was retired that day, and as of v0.8.2 nothing in this plugin files on it or names its repository.

## The four cr1 skills

| Skill | Say | What it does |
|---|---|---|
| `cr1-report` | "report this", "file a bug", "spec it" | Turns the chat where something broke, or an idea, into one GitHub issue on cr1: facts tagged by source, severity, a "for whoever fixes it" block, a build brief for features. |
| `cr1-scrub` | "scrub this", "scrub the repo" | Keeps client names, personal information and money figures out of the repo. Builds the name list fresh from your own book. |
| `cr1-test` | "what needs me", "test #N" | Your acceptance test on a fix: a short script, the original failure run 3 times, the result posted to the issue. |
| `cr1-desk` | "what's pending to build", "get #N ready" | Everything pending in plain language from the client's side, and a short multiple-choice briefing that becomes the build brief. |

## The toolkit (moved in from the owner's plugin, v0.9.0)

Every skill below opens with the team fence: a contractor runs it on the synthetic fixtures or a copied test brain only, never a real client folder, and never ships or promotes. Release and promote stay in the owner's private plugin.

| Skill | Say | What it does |
|---|---|---|
| `battery` | "run the battery", "battery --quick", "battery --ship" | The whole Command Room test battery in tiers, one GREEN, HOLD or RED verdict. Was `cr-test`; renamed so it never collides with `cr1-test`. |
| `bug-regression-suite` | "run the regression suite" | Replays every bug ever found to prove none came back; an adversarial mode on top. |
| `synthetic-workspace-runtime-test` | "run the synthetic workspace test" | Builds a fake executive's workspace from fixtures and runs the product against it. |
| `cross-skill-interaction-test` | "run the cross-skill test" | Checks skills do not break each other across time. |
| `scale-stress-test` | "run the scale test" | Checks the helpers degrade gracefully on a very large workspace. |
| `ship-readiness-gate` | "ship readiness", "post-push verify" | The unattended is-this-safe-to-promote verdict after a push. Verifies only; it never ships. |
| `cr-skill-builder` | "new CR skill", "audit this skill" | Builds or audits a Command Room skill with the house contract enforced. |
| `skill-creator` | "create a skill", "improve this skill" | General skill writing, evals and description tuning. |
| `skill-generator` | "generate a skill for [project]" | A project-scoped skill for one client or workstream. |
| `regenerate-skill` | "regenerate [skill]" | Rebuilds a generated skill when its template changes, keeping the customizations. |
| `preview-command-room-widget` | "internal: preview widget [name]" | Renders a widget before it ships. |

Building from an issue is `cr1-build`, a project skill inside the cr1 repo itself. It runs a fresh-context reviewer before it opens a pull request, and Matthew merges. Versions and the CHANGELOG in cr1 are set only at release, by Matthew's ship-cr-plugin flow; clients get a change when he promotes that release.

## Who decides

Each skill works out who is running it in this order: a gitignored `config/operator.local.json` when present (Matthew's says `"operator": "m"`), then the GitHub account the session posts as (`chaletteholdings` is Matthew, `erick559` is Erick, any other account is another team member under their own name), then the committed `chalette-dev/config/operator.json` (Erick's profile). The GitHub check is what lets web and phone chats, which never have the local file, know Matthew. The skill says who it took you for in its first reply.

- **Matthew** decides what is ready to build, merges, and closes an issue on a passing test.
- **Erick, and anyone else on the team,** gets the same steps, with those decisions turned into proposals tagged for Matthew, under their own name.

## Setup

1. Clone: `git clone https://github.com/chaletteholdings/chalette-dev ~/repos/chalette-dev` (cr1's commit guard looks for the scrub script there).
2. Install the plugin in the Claude app from this repo.
3. Matthew only, optional: add `chalette-dev/config/operator.local.json` with `{"operator": "m", "operator_name": "Matthew"}`. Not needed when your GitHub account is signed in; it only matters on a computer where it isn't.
4. Optional, each person: `chalette-dev/config/scrub.local.json` with private lists for the scrub (format at the top of `skills/cr1-scrub/scripts/scrub_scan.py`). Never commit it.
5. In your cr1 clone, switch on the scrub guard that runs before every commit: `git config core.hooksPath command-room/.githooks` and `git config scrub.book "<book folder>"`.

## Checks

`pytest tests/` (also on every push): the committed operator profile stays the contractor default with exactly the two keys the skills read and the local overlay is never tracked; `quick_validate` on every skill (`scripts/quick_validate.py`, vendored from Anthropic's skill-creator, Apache 2.0); the description budget on every skill and on both manifests; the cr1 target guard (no CR2-only text left in the skills); the scrub script on sample books; the test-log prompt. Each skill has `evals/triggers.json`: phrases that should start it and near misses that should not. The evals are not run by the tests yet.
