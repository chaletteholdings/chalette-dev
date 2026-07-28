# chalette-dev — Command Room internal dev & QA toolkit

The shared testing, verification, and skill-building toolkit for everyone who builds on Command Room. Matthew (M) and Eric both install this; it is the single source of truth for how CR gets tested. Client repos, client data, and the release/promote pipeline are deliberately **not** in here.

As of **CONSOL1 (2026-07-24)** this is the **single canonical home** of the shared toolkit — the skills below used to be duplicated into M's private `chalette` plugin; that copy is gone. Guard 1 (`scripts/check_toolkit_overlap.py`) fails the build if any of them ever reappears in `chalette`.

**15 skills** (as of v0.5.0). Three have been retired: `compare-canonical-vs-freelance` (its niche — validating the v3.13.8 §3.6 canonical-vs-freelance widget ladder per skill — closed; the freelance fallback it diffed against no longer exists, and the synthetic invariants plus cr1's `widget_transport` validators cover the render path now), `run-command-room-tests` (folded into `cr-test`, which auto-discovers every suite instead of running a hardcoded five; its trigger phrases are aliases for `cr test --quick`), and `verify-cr-release` (the tier-5 paste-back orchestrator — retired per M's ruling: dogfood-before-promote plus BIG-TEST carry the attended layer, so the loop's state tracking and prompt ceremony went away. **What it owned was kept, not deleted:** its verification plan is now `cr-test/references/VERIFICATION_PLAN.md`, and its response classifier + findings-log format moved to `bug-regression-suite/references/`. `verify cr release` / `run verification suite` now alias `cr test --attended`).

## Setup (Eric)

1. Clone this repo: `git clone https://github.com/ChaletteHQ/chalette-dev ~/repos/chalette-dev`
2. Clone the Command Room staging repo (read-only for you): `git clone https://github.com/ChaletteHQ/cr1 ~/repos/cr1`
3. Edit `config/operator.json` on your machine if your paths differ. Leave `operator: "eric"` and the four authority keys (`allowed_targets`, `may_ship`, `may_promote`, `may_build_own_spec`) exactly as they ship — the skills read them to decide what you're allowed to target, and Guard 2 fails CI if any of them drifts. **There is nothing for you to create or turn on**; what you're granted is already in the file. See "What you can and can't do" below.
   *(There is also an optional gitignored `config/operator.local.json` overlay, loaded on top of `operator.json` per-key. You don't need one — M keeps one for his real machine paths. If you ever add one, it must never be committed; Guard 2 asserts that.)*
4. In Claude Code, install the plugin from your local clone (marketplace add → this repo path), so the `chalette-dev:*` skills are available in every session.
5. The synthetic fixtures live in this repo at `chalette-dev/skills/synthetic-workspace-runtime-test/fixtures/` (four workspaces: clean / degraded / fresh_install / mature, built by `_generate_fixtures.py`). `synthetic-workspace-runtime-test` resolves to one of them by default; `config/operator.json` (`workspace_root: null`) points the QA skills at the `clean_workspace` fixture unless you say otherwise.

**Three testing tracks** (see `CLAUDE.md`): (A) **dogfood your own Cowork workspace** as a real user — your own accounts, your own data, encouraged; (B) **controlled regression** with the QA skills against the synthetic fixtures above — these never target a real workspace; (C) **the structured plan**, `skills/cr-test/references/VERIFICATION_PLAN.md`, walked by hand against a **fresh, empty** test workspace (this is the plan Eric maintains, and the only track that reaches virgin onboarding, empty states, and the destructive probes). The rule "you never test against a real workspace" is about the *automated test tools*; it does not stop Track A. A + C together are `cr test --attended`; no skill drives them.

## What you can and can't do

The four authority keys in `config/operator.json`, in plain English. All four ship set correctly — **nothing to turn on**:

| Key | Ships | What it means for you |
|---|---|---|
| `may_build_own_spec` | **`true`** | **You can write a spec and build from it in one pass.** No stopping to get the spec approved first — the pull request is where M reviews. (GATE1, v0.5.0.) |
| `may_ship` | `false` | No version bumps, no CHANGELOG entries, no releases, no merging your own PR. |
| `may_promote` | `false` | No fan-out to client repos. |
| `allowed_targets` | `["synthetic"]` | The automated test skills run against the synthetic fixtures, never a real workspace. (Doesn't stop you dogfooding your own Command Room — that's Track A.) |

Build authority and ship authority are separate on purpose; being granted the first grants none of the second. And these keys are a working agreement, not a lock — what actually holds is your GitHub access: read-only on cr1, fork → PR, M merges.

## The rules of the road

- **You never test against a real workspace.** All skills here run against synthetic fixtures for any operator that isn't M. This is enforced in the skills and in `config/operator.json` (`allowed_targets: ["synthetic"]`).
- **You never ship.** Releases, version bumps, and promotion to client repos are M's alone. The ship tooling is not in this plugin on purpose.
- **All work goes through PRs.** You have read access to cr1: fork it, build on a branch in your fork, open a PR against cr1 `main`. M reviews, adjusts, merges. **The PR is the review point** — as of v0.5.0 that includes specs you wrote yourself and built from in one pass (`may_build_own_spec`), so there is no separate approve-the-spec step in front of the build. If a decision is genuinely architecture-shaping, send M a one-line heads-up and keep building unless he objects.
- **The skills are English on purpose.** SKILL.md files are the product. Your lane is the rails around them — tests, validation, schema, CI, tooling. Don't rewrite prompt logic as code.

## What's in here

| Skill | What it does |
|---|---|
| `cr-test` | The one-command entry point — sequences the whole test battery and gives a GREEN/HOLD/RED verdict. Also owns `references/VERIFICATION_PLAN.md`, the hand-walked attended plan (tier 5) |
| `ship-readiness-gate` | Unattended post-push verification → PROMOTE/HOLD/BLOCKED verdict |
| `synthetic-workspace-runtime-test` | Spins up the synthetic fixture workspace and fires the canonical surfaces against it |
| `bug-regression-suite` | Fires every known-bug repro prompt; every new bug you find gets added here permanently |
| `cross-skill-interaction-test` | Multi-skill sequences over time — substrate coherence |
| `scale-stress-test`, `smoke-watch` | Scaffolds — performance at scale, post-release observation (not fully built) |
| `cr-skill-builder` | Builds new CR skills with all contract gates enforced; also audits drafts |
| `capture-for-code`, `triage-intake` | The intake pair — capture a bug/idea the moment you spot it → verify it against the repo and write a spec (operator-keyed queue via `intake_root`) |
| `skill-creator`, `skill-generator`, `regenerate-skill` | General skill scaffolding and eval tooling |
| `voice-test` | Scores composer-skill output against the CR voice rules |
| `preview-command-room-widget` | Renders CR widgets locally for visual checks |

## Finding something broken

When a test run surfaces a bug: write it up as a findings entry (what fired, expected vs actual, repro prompt), commit it to your fork on a `findings/...` branch, and open a PR. Serious/blocking issues: flag M directly as well.
