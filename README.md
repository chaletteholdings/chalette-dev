# chalette-dev — Command Room internal dev & QA toolkit

The shared testing, verification, and skill-building toolkit for everyone who builds on Command Room. Matthew (M) and Eric both install this; it is the single source of truth for how CR gets tested. Client repos, client data, and the release/promote pipeline are deliberately **not** in here.

As of **CONSOL1 (2026-07-24)** this is the **single canonical home** of the shared toolkit — the 18 skills below used to be duplicated into M's private `chalette` plugin; that copy is gone. Guard 1 (`scripts/check_toolkit_overlap.py`) fails the build if any of them ever reappears in `chalette`.

## Setup (Eric)

1. Clone this repo: `git clone https://github.com/ChaletteHQ/chalette-dev ~/repos/chalette-dev`
2. Clone the Command Room staging repo (read-only for you): `git clone https://github.com/ChaletteHQ/cr1 ~/repos/cr1`
3. Edit `config/operator.json` on your machine if your paths differ. Leave `operator: "eric"` and the safety keys (`allowed_targets`, `may_ship`, `may_promote`) as is — the test skills read them to decide what you're allowed to target. (M does not edit this committed file; he keeps a gitignored `config/operator.local.json` overlay that the skills merge on top of it. Guard 2 fails CI if the committed default ever drifts, or if the overlay is ever tracked.)
4. In Claude Code, install the plugin from your local clone (marketplace add → this repo path), so the `chalette-dev:*` skills are available in every session.
5. The synthetic fixtures live in this repo at `chalette-dev/skills/synthetic-workspace-runtime-test/fixtures/` (four workspaces: clean / degraded / fresh_install / mature, built by `_generate_fixtures.py`). `synthetic-workspace-runtime-test` resolves to one of them by default; `config/operator.json` (`workspace_root: null`) points the QA skills at the `clean_workspace` fixture unless you say otherwise.

**Two testing tracks** (see `CLAUDE.md`): (A) **dogfood your own Cowork workspace** as a real user — your own accounts, your own data, encouraged; (B) **controlled regression** with the QA skills against the synthetic fixtures above — these never target a real workspace. The rule "you never test against a real workspace" is about the *automated test tools*; it does not stop Track A.

## The rules of the road

- **You never test against a real workspace.** All skills here run against synthetic fixtures for any operator that isn't M. This is enforced in the skills and in `config/operator.json` (`allowed_targets: ["synthetic"]`).
- **You never ship.** Releases, version bumps, and promotion to client repos are M's alone. The ship tooling is not in this plugin on purpose.
- **All work goes through PRs.** You have read access to cr1: fork it, build on a branch in your fork, open a PR against cr1 `main`. M reviews, adjusts, merges.
- **The skills are English on purpose.** SKILL.md files are the product. Your lane is the rails around them — tests, validation, schema, CI, tooling. Don't rewrite prompt logic as code.

## What's in here

| Skill | What it does |
|---|---|
| `cr-test` | The one-command entry point — sequences the whole test battery and gives a GREEN/HOLD/RED verdict |
| `verify-cr-release` | Walks a release verification plan step by step (the prompt/paste loop) |
| `ship-readiness-gate` | Unattended post-push verification → PROMOTE/HOLD/BLOCKED verdict |
| `synthetic-workspace-runtime-test` | Spins up the synthetic fixture workspace and fires the canonical surfaces against it |
| `bug-regression-suite` | Fires every known-bug repro prompt; every new bug you find gets added here permanently |
| `cross-skill-interaction-test` | Multi-skill sequences over time — substrate coherence |
| `compare-canonical-vs-freelance` | Validates rendering went through the canonical path |
| `run-command-room-tests` | Runs the cr1 test battery (`command-room/tests/run_all.py` — house-convention suites, not pytest; `pip install -r requirements.txt` first) |
| `scale-stress-test`, `smoke-watch` | Scaffolds — performance at scale, post-release observation (not fully built) |
| `cr-skill-builder` | Builds new CR skills with all contract gates enforced; also audits drafts |
| `capture-for-code`, `triage-intake` | The intake pair — capture a bug/idea the moment you spot it → verify it against the repo and write a spec (operator-keyed queue via `intake_root`) |
| `skill-creator`, `skill-generator`, `regenerate-skill` | General skill scaffolding and eval tooling |
| `voice-test` | Scores composer-skill output against the CR voice rules |
| `preview-command-room-widget` | Renders CR widgets locally for visual checks |

## Finding something broken

When a test run surfaces a bug: write it up as a findings entry (what fired, expected vs actual, repro prompt), commit it to your fork on a `findings/...` branch, and open a PR. Serious/blocking issues: flag M directly as well.
