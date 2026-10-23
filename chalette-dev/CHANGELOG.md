# chalette-dev — Changelog

(Release history before v0.3.0 lives in `.claude-plugin/plugin.json`'s `description` field.
This file starts at the CONSOL1 release.)

## v0.8.0 (2026-10-22): the skills move to Command Room 1

Matthew retired Command Room 2 on 2026-10-22 and went back to building cr1 (`ChaletteHQ/cr1`). There is no second developer: Matthew builds with Claude Code (cr1-build, a project skill in the cr1 repo, which runs a fresh-context reviewer before it opens a pull request) and merges. Erick still uses these skills and still gets proposals, not decisions. MINOR bump (skills renamed and retargeted).

- **Renamed with history (`git mv`):** cr2-report, cr2-scrub, cr2-test, cr2-desk became cr1-report, cr1-scrub, cr1-test, cr1-desk. Trigger phrases are unchanged except the "log this for Louis" ones, which are gone.
- **Retargeted:** every `repos/ChaletteHQ/cr2` call is now `cr1`; rules point at cr1's `ISSUES.md`, `CONTRIBUTING.md` and `DEVELOPMENT.md`; title area tags use cr1 skill names (`[Morning briefing]`, `[Inbox triage]`, `[Meeting notes]`, ...). Each skill keeps one line: when the owner explicitly says a problem is on CR2, it still files on `ChaletteHQ/cr2`.
- **Removed, not renamed (CR2-only):** the CR2 developer (hand-offs, mentions, "waiting on" piles), the `core`/`labs` routes and route question, CR2 folders (`00_docs`, `02_product`, `03_tests`, `06_labs`), the cloud intake drop, the CR2 run-log folder, the labs plugin, `CR2_RUNTIME`. A build brief's "Writes:" is now nothing / events in the book / a page in the project folder.
- **cr1-test version gate:** the fix must be in what is installed. For Matthew's staging `cr` plugin (follows `main` by commit), its installed commit must be at or after the fix's merge (GitHub's compare API). For `command-room` (clients get changes only when Matthew promotes), a released version must list the issue in `command-room/CHANGELOG.md` on `main`. The CHANGELOG is over 1 MB, so it is read raw.
- **cr1-desk:** piles are waiting on your test, waiting on Matthew's merge, needs your decision, ready to build. The brief asks at most five questions (the route question is gone). Glossary: "Merge: Matthew accepting the change into main; clients get it at the next promote."
- **Versions and CHANGELOG** in cr1 are set only at release by Matthew's ship-cr-plugin flow; a pull request never touches them (was "needs version" / "Louis sets the version").
- **cr1-scrub:** the scrub's `terms` step now also reads a cr1 book's single `_hq/data/entities.json` (people, orgs, threads). Before this it read only the older split `_hq/data/entities/*.jsonl.txt`, and a cr1 book has none, so on Matthew's book it returned no names at all. Output on a split book is unchanged. `terms` and `scan` keep the same arguments and output, because cr1's pre-commit guard calls them. `CR1_SCRUB_LOCAL` is read first, `CR2_SCRUB_LOCAL` still works. The skill now says how to switch on cr1's commit guard (`git config core.hooksPath scripts/hooks`, `git config scrub.book`) and warns when the name list came back empty. One example in Step 3 was replaced with a neutral one.
- **Tests:** `test_who_is_running`, `test_test_log` and the description budget follow the new names. New `test_cr1_target.py` (the four skills exist under cr1 names, `ChaletteHQ/cr2` appears only in the one fallback line, no CR2-only text or route remains, no em dash or exclamation mark) and `test_scrub_scan.py` (a cr1 book and a split book give the same names; a name and an amount are caught). README, CLAUDE.md, marketplace and workflow text say cr1.

Verified: `pytest tests/` 57 passed, 4 skipped (the bash-preamble tests, as before). `quick_validate` passes on all four skills. Both new tests were seen to fail on purpose: a planted route and developer name in cr1-desk, and the scrub with its `entities.json` read switched off. The scrub's terms on a synthetic split book are byte-identical before and after; on Matthew's real cr1 book the old script found 0 names and the new one finds several hundred (count only, nothing printed). The `gh api` commands in the skills were checked against cr1: repo and labels, the plugin version on `main`, the staging marketplace, the compare call and the raw CHANGELOG search. Not verified: cr1's `ISSUES.md`, `scripts/hooks/`, the `--quick` flag and cr1-build are being added in parallel and are not on cr1 `main` yet; the trigger evals are not run.

## v0.7.2 (2026-10-15): every test ends with a test log

Matthew's ruling (2026-10-15): a test script always gives the prompt that makes the test chat list what it did, without being asked. In the 0.8.109 test of cr2 #169 the answer was right in 3 of 3 runs while the fix's own path never ran; only the book's run log showed it.

- **cr2-test, the script:** every script ends with "After every run: the test log" and the test-log prompt in its own code block. Matthew pastes it into the same test chat after the answer and brings both replies back. Test chats get only the test prompts and the log prompt.
- **cr2-test, the verdict:** judge the path, not only the answer. A right answer reached by a workaround is partial, never a pass. The log's claims are checked against the book's run log where the folder is reachable. A run with no log is posted as "no test log".
- **cr2-test, fail reports:** the chat log is built from the test log.
- **Test:** `tests/test_test_log.py` pins the prompt verbatim, its place in the script template, and the partial-not-pass rule.
- Description and triggers unchanged.

## v0.7.1 (2026-10-10): the skills know Matthew in web and phone chats

Web and phone chats load a fresh copy of the plugin, which never holds Matthew's local profile, so cr2-test took him for Erick and turned his closes into proposals.

- **All four skills:** "Who is running this" now checks, in order, the local profile, then the GitHub account the session posts as (`chaletteholdings` is Matthew, `erick559` is Erick, anyone else is treated as Erick), then the shared default. The first reply says who it took the person for, and the person's correction stands for the chat. The unreadable-profile rule is unchanged.
- **README:** the order above; the local profile is now optional for Matthew.
- **Test:** `test_who_is_running_is_identical_across_skills` keeps the section word for word the same in all four skills.
- **Committed `operator.json` unchanged**, so every operator fence still holds.

## v0.7.0 (2026-10-04): Command Room 2 only

Matthew's ruling: chalette-dev keeps only the Command Room 2 dev skills; everything else moves to his private `chalette` plugin (its v0.12.0).

- **Moved out (16 skills):** bug-regression-suite, capture-for-code, cr-skill-builder, cr-test, cross-skill-interaction-test, demo-prospect-workspace, preview-command-room-widget, regenerate-skill, scale-stress-test, ship-readiness-gate, skill-creator, skill-generator, smoke-watch, synthetic-workspace-runtime-test, triage-intake, voice-test. Erick no longer has them; Command Room 1 is legacy after 6 October 2026.
- **Kept:** cr2-report, cr2-scrub, cr2-test, cr2-desk, and `config/operator.json` (Erick's profile; Matthew's overlay is local).
- **Tests:** the demo, triage and reference-integrity tests moved with their skills. `quick_validate.py` is vendored at `scripts/` (from Anthropic's skill-creator, Apache 2.0) since skill-creator left. The overlap guard and its workflow job are retired. 32 passed, 4 skipped (preamble tests with no bash-preamble skill left to check).
- **Docs:** README and CLAUDE.md rewritten for the four skills. The old Command Room 1 contributor guide and README went to chalette as `chalette/references/CR1_TOOLKIT_GUIDE.md`.

## v0.6.0 (2026-10-04): the Command Room 2 dev skills

Four skills added, so Matthew and Erick report, scrub, test and plan Command Room 2 work the same way. Skill count 15 -> 19. MINOR bump (new skills).

- **cr2-report:** turns a chat into one GitHub issue on `ChaletteHQ/cr2` (bug or feature, chat log, version, build brief with a `core` or `labs` route). Its scrub section now points at cr2-scrub instead of carrying its own copy of the script.
- **cr2-scrub:** checks text, files or the whole cr2 repo for client names, personal information and money figures. The script now ships as `skills/cr2-scrub/scripts/scrub_scan.py`. The real family surnames, contact first names and org-name words that were written inside the old script moved to a gitignored, per-machine `config/scrub.local.json`; nothing real is committed. Fixed on Windows: the name list is written as UTF-8, so the scan step can read it back.
- **cr2-test:** Matthew's supervised acceptance tests: the queue, a step-by-step script, and the result posted in the repo's fixed shape.
- **cr2-desk (new):** the build desk. "what's pending to build" sorts open issues into needs your decision, ready to build, waiting on Louis and waiting on your test, each explained from the client's side; "get #N ready" briefs, asks up to six questions and posts the build brief on a yes.
- **Operator-aware:** each skill reads `operator` from `config/operator.json` + `operator.local.json`. Matthew (`m`) decides routes and closes issues; for anyone else those become proposals tagged for Matthew. An unreadable profile says `FATAL: operator profile unreadable` and asks.
- `.gitignore`: `scrub.local.json`.
- **Research pass folded in (same release, before merge).** Sources and the full list: four web research passes on bug reporting, scrubbing, owner testing, backlog practice and skill authoring.
  - cr2-report: every fact tagged (owner said / Claude saw / Claude's guess), a check that every step and number points to a chat turn, last-worked and first-broke versions, severity S1 to S3 from two plain questions, a "for whoever fixes it" block (trigger prompt, likely area, suggested fix as a guess), a drafted-by footer, a short-body target.
  - cr2-test: the original failure run 3 times (3 of 3 pass, 1 or 2 flaky, 0 fail), yes/no checks with named evidence, a regression step and a near-miss step, an optional look-around for risky fixes, evidence quoted before a pass, model, surface and deviations recorded, `blocked` label for a specific blocker.
  - cr2-desk: multiple-choice questions with the recommendation first and why it matters, stop early, answers kept as they come, appetite instead of size, one-way and two-way doors, brief gains Today, After, Out of scope, Appetite and Door.
  - cr2-scrub: edited GitHub comments keep the old text, so each redaction lists the revisions to delete by hand; when history may be rewritten (Matthew's decision) and how.
  - All four: descriptions say when to fire; report no longer claims "scrub this". Each skill has `evals/triggers.json` with 10 phrases that should start it and 10 near misses (not yet run).
- Not moved: cr2-build stays a project skill inside the cr2 repo (`.claude/skills/cr2-build`, cr2 PR #127), so it loads for anyone working in that repo.

Verified: scrub terms from the new script are byte-identical to the old script's on Matthew's book (517 terms); the new skill files scan clean against them; a planted surname and amount are caught. Battery: 134 passed, 4 failed; the same 4 (`quick_validate` on four older skills) fail on `main` on Windows from a cp1252 decode and are unrelated.

## v0.5.1 (2026-07-29) — REFGAP1: cross-skill-interaction-test references recovered + dangling-reference guard

Fix + fence. Skill count unchanged (**15**). PATCH bump per this repo's convention
(fixes take a patch).

**The bug (found at the v5.5.1 attended gate, 2026-07-29):** `cross-skill-interaction-test`
Step 1 loads `references/sequence-catalog.md` (plus `temporal-wait-strategy.md` and
`multi-phase-verdict-aggregation.md`), but git tracked only SKILL.md — the `references/`
directory existed and was empty, so the skill failed on a missing file even with a valid
operator profile. The 16-row table inline in SKILL.md is a summary index, not the
executable catalog.

**Recovery finding — the files never existed.** Before writing anything, the "recover the
originals" path was exhausted: chalette-dev, chalette030, and retired-plugin git history
never tracked any of the three under any path, and no session transcript contains a write
of them. BUILD_VCRRETIRE §7 (2026-07-26) had already recorded all three inside a
13-citation dangling-read set across five skills. So the three docs were **authored from
SKILL.md's own inline content** — the format example (the Bug #51 cascade sequence, which
ships READY) and the index table (17 rows today: the original 15 plus the two OBJ1
sequences added in `6636e80`). Every other catalog entry ships **DRAFT** with an explicit
promotion rule: walk it once, confirm the expected substrate writes, then mark READY —
and DRAFT failures report ADVISORY, not blocking, so an unverified draft expectation can
never assert a phantom regression. Event names in expected-writes were checked against
cr1's `events.schema.json`; the catalog also flags that *pulse* and the *commitments
scheduled task* are scheduled surfaces, not `skills/` dirs, and that the row's
*weekly-audit* surface is now `cleanup`. Each file carries a provenance header so nobody
hunts a "lost original" again.

### Added — Guard 4: `tests/test_reference_integrity.py`

The mechanization BUILD_VCRRETIRE deferred: every `references/*.md` a SKILL.md cites must
be **git-tracked** (not merely on disk — untracked is absent at client install), present,
and non-empty. Bare citations resolve against the citing skill; `other-skill/references/…`
prefixed citations resolve against the named skill **when it exists in this repo** —
cross-repo citations (`command-room/…` lives in cr1, verified present there) are outside
this guard's jurisdiction and skipped. The remaining 8 pre-existing dangling citations
(bug-regression-suite ×2, ship-readiness-gate ×3, skill-generator ×2, and skill-creator's
mis-citation of a checklist that actually lives under `cr-skill-builder/references/`) are
**grandfathered in a baseline that ratchets both ways**: a NEW dangling citation fails
immediately, and fixing a grandfathered one without deleting its baseline row also fails,
so a stale row cannot mask a re-regression. Coverage is asserted, not assumed: the scan
must visit every skill's SKILL.md, plus three controls — positive (the three repaired
citations resolve tracked), negative (a fabricated citation registers as dangling), and a
misattribution pin (a prefixed citation resolves to its OWNER, not the citing skill — the
false-dangling the naive resolver produced during this very build). Mutation-verified
both directions: untracking the catalog → 2 red; satisfying a baseline entry → ratchet
red; restored → green. Battery 59 → **65 passed**; Guard 1 OK (15 / 20 / 0).

**Deliberately NOT done here:** authoring the 8 grandfathered reference docs (each
belongs to its owning skill's build, with review), and any SKILL.md text change —
frontmatter descriptions are untouched repo-wide, so zero trigger changes.

## v0.5.0 (2026-07-27) — GATE1: build authority decoupled from `may_ship`

Capability addition. Skill count unchanged (**15**). MINOR bump, per this repo's own
convention: retirements and fixes take a patch (v0.4.1 VCRRETIRE, v0.3.1 MAINT2), a
capability addition takes a minor (v0.4.0 TI2). GATE1 adds an operator key and a new
delivery path; it removes nothing.

**The ruling (2026-07-27, M, by phone):** Eric writes a spec and builds from it in one
continuous pass. Review happens **once**, at the pull request, before anything is pushed
or shipped. The pre-build approval step goes away. What does **not** change: zero ship
authority — no version bumps, no CHANGELOG entries, no promote/fan-out, no merging his
own PR. M stays the final gate before anything lands.

**Why this had to be a code change and not a verbal agreement.** The pre-build gate was
prose inside `skills/triage-intake/SKILL.md`, and prose re-asserts itself on every run: the
next `triage intake` session would read "contractors never self-approve a spec into a
build" and tell Eric to hand the spec over again, regardless of what was agreed on a call.
Same instruction-layer-drift class the intake queue already tracks — a skill's prose
contradicting the actual intent with nothing to catch it. Fixed in the text, and fenced.

### Root cause — one key was carrying three authorities

`may_ship` conflated (1) may I build from a spec I wrote myself, (2) may I bump the
version / write CHANGELOG / cut a release, and (3) may I promote to client repos. M grants
(1) and withholds (2) and (3). There was no key for (1) — it rode `may_ship` by
implication. Now there is.

### Added — `may_build_own_spec` in `config/operator.json`

Third authority key, placed next to `may_ship` / `may_promote` so all three read together.
Independent of `may_ship` in both directions: a contractor carries spec→build in one pass
while holding zero ship authority.

**It ships `true` — the one authority key that does.** The spec ruled it overlay-only with
a committed `false`, matching the other two. M overruled that on the call, and he is right:
an overlay is a hand-created, gitignored file, so the grant would have been invisible to
`git pull`, absent on a fresh clone, and silently lost the first time Eric re-cloned — a
setup step that can be forgotten, guarding something a PR review already catches. Shipping
it on means **a plain `git pull` is the entire setup**. What that costs: the value travels
with the repo, so a future contributor inherits build authority rather than being granted
it one at a time. With two collaborators on a private repo, and with `may_ship` /
`may_promote` / `allowed_targets` all still shipping locked, that is a real but small price
and M took it knowingly.

The safety keys are unchanged and still ship locked. **"Contractor-safe" now means zero
ship authority and synthetic targets only — it no longer means zero authority**, and both
`operator.json`'s header comment and `CLAUDE.md` say so, because that phrase is load-bearing
in three places and a reader who assumes the old meaning would read the new default as a
regression.

### Changed — two sentences in `skills/triage-intake/SKILL.md`

- **Operator-aware blockquote:** `may_build_own_spec` added to the keys-used list, and the
  closing sentence split so the two authorities are stated separately instead of one
  implying the other. `may_ship: false` now spells out what it actually withholds (version
  bump, CHANGELOG, release, promote, self-merge) and states that it binds regardless of the
  build grant.
- **"Writing the spec" delivery rule:** re-gated from `may_ship` onto `may_build_own_spec`.
  Granted → the spec lands in `specs_dir` ready to build **regardless of `may_ship`**, the
  build proceeds in a normal build session, and **the PR is the review point** (no
  approve-the-spec step in front of it). Ungranted → the previous behaviour verbatim
  (attach to the related cr1 PR / hand over; contractors never self-approve a spec into a
  build). The granted branch carries the load-bearing sentence explicitly: building from
  your own spec does **not** grant ship authority — the `may_ship` rules in the Writer
  contract still bind in full.

**Deviation from the spec, deliberate: the granted branch fires on `may_build_own_spec:
true` OR `may_ship: true`.** Under the spec's overlay-only design this was load-bearing —
M's overlay predates the key, so re-gating on the new key alone would have fallen through
to the committed `false` and started telling the maintainer to hand his own specs over.
Once the shipped value became `true` the clause stopped being load-bearing, but it is kept:
a ship operator may always build his own spec, including one who deliberately turns the key
off in an overlay. **Neither machine needs an overlay edit for this release.**

### NOT changed — deliberately

- **"Routing work out" stays gated on `may_ship`.** Contributor packets and the cr1
  `BACKLOG.md` route work OUT to other people; that is genuinely a ship-operator function,
  and a contractor does not route work to themselves. Same for the three `may_ship`
  references in `references/spec-templates.md`.
- The Writer contract line "Ship/promote stays with M (`may_ship` in operator.json)".
- The `triage-intake` frontmatter **description** is byte-identical — zero trigger changes,
  G11 description budget untouched. Body text only.
- `cr-test`'s tier-5 "the ship operator's call (`may_ship`)" — a different concept.
- `allowed_targets` stays `["synthetic"]` for contractors. This grants build authority, not
  real-workspace access. `may_promote` untouched.

### Guards

- **Guard 2** (`tests/test_operator_fences.py`) pins `may_build_own_spec == true`. **This
  fence runs the opposite direction from its two neighbours, deliberately.** It is not a
  safety fence — it is a don't-silently-take-it-away fence: a revert to `false` sends every
  contractor back to the pre-build handoff with no error and no clue why, which is precisely
  the failure GATE1 exists to prevent. The real safety fences (`may_ship`, `may_promote`,
  `allowed_targets`, `workspace_root`, `scrub_roster`) still pin the locked values and are
  untouched. Mutation-verified both directions against the shipped value: reverted to
  `false` → **1 failed, 49 passed** (fence RED); assertion then removed with the bad value
  still in place → **49 passed, 0 failed** (only the fence caught it). Restored
  byte-identical, back to **50 passed, 9 skipped**.
- **Guard 3** (`tests/test_triage_outbound_fences.py`) gains three instruction-layer fences
  on the new delivery rule — same class as the existing outbound fences, one section over.
  The rule is prose and can fail in **both** directions: narrowed back to `may_ship` (the
  handoff silently returns) or widened to no gate at all (every profile self-approves its
  own specs). Mutation-verified: drift back to the old sentence → **3 failed**; false-branch
  deleted → **1 failed**; "does not grant ship authority" sentence deleted → **1 failed**;
  fences removed with the prose still drifted → **9 passed** (green, i.e. nothing else was
  catching it). Guard 3 total 9 → 12.
- Battery **50 passed, 9 skipped** (the 9 are the bash-preamble tests, skipped for no
  `bash` on PATH in this shell; CI runs them on ubuntu). `quick_validate` green on all 15
  skills — it is Guard 2 Fence 3, so the battery number covers it.

### Docs

- `README.md` gains **"What you can and can't do"** — all four authority keys in plain
  English with what each ships as, written for the contractor rather than the maintainer.
  This section is why the release is not inert: the docs previously said only M keeps an
  overlay, so under the spec's overlay-only design nothing would have told Eric the key
  existed. Setup step 3 now says explicitly that there is **nothing to create or turn on**.
  The "All work goes through PRs" rule names the PR as the review point; skill-count line
  repointed to v0.5.0.
- `CLAUDE.md` enumerates `may_build_own_spec: true` in the committed default, carries a
  four-column authority table (grants / ships / what Guard 2 pins), and explains why one
  fence points the other way. It also states the thing worth being honest about: these keys
  are a **coordination contract, not a security boundary** — the boundary is GitHub access
  (read-only on cr1, fork→PR, M merges).

### Same-class sweep — the overlay claim that GATE1 makes false

Nine `SKILL.md` files carried the parenthetical **"only M has one"** about
`config/operator.local.json`. The moment Eric keeps an overlay that is simply untrue, and a
false statement in the instruction layer is the exact class this release exists to fix.
Swept to **"not every operator has one"** — descriptive prose that gates nothing (the gates
are `allowed_targets` / `may_ship` / `may_build_own_spec`), so no behaviour moves:
`bug-regression-suite`, `capture-for-code`, `cr-skill-builder`, `cr-test`,
`cross-skill-interaction-test`, `scale-stress-test`, `ship-readiness-gate`, `smoke-watch`,
`triage-intake`.

Two sites deliberately **excluded** and verified still carrying the old phrase:
`config/operator.json`'s `_comment_chalette_clone` (that one is about a chalette030 **clone**
— still true), and `plugin.json`'s description (a historical narrative chain; you do not
rewrite history to match the present).

**Zero trigger changes, proven not asserted:** each of the 9 changed files had its
frontmatter `description` compared byte-for-byte against `HEAD` — 9 same, 0 changed. Routing
runs on descriptions only, so this is the fence between a body-text edit and a silent
re-route of the whole plugin.

### Known limitation — the `§0 AWAIT ruling` tradeoff, accepted knowingly

Specs carry a `§0 Open decisions` table whose rows are marked `AWAIT ruling — DO NOT BUILD`
on genuine design forks. Eric now rules those himself and builds. The template already has
the slot for surfacing it: the PR description's "Reviewer-visible defaults — every judgment
call you made that the spec did not rule." The cost accepted: a rejected **approach** at PR
time wastes the whole build, where a two-minute answer beforehand would not have. Middle
ground, no ceremony and no gate — for architecture-shaping decisions only, a one-line
heads-up, and keep building unless M objects. Working practice, not a code change.

## v0.4.1 (2026-07-27) — VCRRETIRE: `verify-cr-release` retired, tier 5 becomes the dogfood ritual

Retirement. Skill count **16 → 15**. PATCH bump, per this repo's own convention: retirements
and fixes take a patch (v0.3.1 carried two retirements plus the Git-Bash fix), a capability
addition takes a minor (v0.4.0 TI2). VCRRETIRE removes a skill and re-homes what it owned;
it adds nothing.

**The ruling (2026-07-25, M):** the tier-5 paste-back orchestrator retires. Dogfood-before-promote
plus BIG-TEST carry the attended layer now, so the loop's state tracking (`_hq/verify-runs/active.json`),
prompt-rotation templates, phase-decision gates, and verdict-doc generation are ceremony we no longer
run. This is the retirement `chalette030 review-cr-build/SKILL.md:27` predicted and pinned the
authority chain for ("dogfood-before-promote plus BIG-TEST, as an M ruling, and **never** on
`review-cr-build`'s existence") — that note is updated in place rather than deleted, so the reasoning
survives the thing it was reasoning about.

### Retired

- `skills/verify-cr-release/` — deleted. `SKILL.md` plus the four paste-back-machinery references
  (`confirm-prompt-templates.md`, `phase-decision-gates.md`, `test-parsing.md`,
  `verdict-doc-template.md`), each verified to have **zero** citers outside the retired skill.

### Kept, not deleted — three reference docs relocated to their real owners

The skill owned assets that other skills cite **by name**. Deleting the folder wholesale would
have turned every citer into a dangling read (the DANGLING_READ / G3 dead-ref class). Each moved
with `git mv`, so history follows the file:

| Doc | New home | Why there | Citers repointed |
|---|---|---|---|
| `VERIFICATION_PLAN.md` | `skills/cr-test/references/` | `cr-test` owns tier 5; this is tier 5's structured half. Repo-level asset, **not** the retired skill's private detail — line 3 always said "the plan Eric maintains" | `CLAUDE.md` (Eric's PR procedure), `README.md` |
| `response-classifier.md` | `skills/bug-regression-suite/references/` | that skill fires prompts and classifies responses — step 3 of its own procedure | `bug-regression-suite/SKILL.md`, `synthetic-workspace-runtime-test/references/invariants.md` (I5) |
| `findings-log-format.md` | `skills/bug-regression-suite/references/` | keeps the classify-and-log pair together; `cleanup-helper.md` already integrated with it | `synthetic-workspace-runtime-test/references/invariants.md`, `cleanup-helper.md` |

Both relocated shared docs gained a **"shared asset — cited across skills, sweep the citers before
moving"** header, so the next retirement doesn't re-orphan them the same way.

### Changed — tier 5 is now "the dogfood ritual," and it is explicitly two halves

`cr-test` Step 4 + the tier table no longer hand off to a skill. Tier 5 is walked **by hand**, and
it is stated as **both**: (1) freeform dogfood on the operator's real workspace, and (2) the
structured plan against a **fresh, empty** workspace. This distinction is load-bearing and was
already written down in the plan itself (surfaces #2 vs #3): dogfood runs on a mature real
workspace, so it structurally **cannot** reach virgin-workspace onboarding, honest empty states,
the Phase-3 destructive/garbage probes (which must never touch a real workspace), late-fire
behavior, or the fresh-runtime skill-load canary. `cr-test` now refuses to call tier 5 covered on
dogfood alone. `CLAUDE.md` / `README.md` grew a **Track C** to match — the two-track framing had no
slot for the plan.

### Changed — routing for the orphaned trigger phrases

`verify cr release` and `run verification suite` alias `cr test --attended`; `pre-ship check`
aliases `cr test --ship` (no collision with `ship-readiness-gate`'s own `pre-promote check`).
`continue verification` / `resume verification` are **deliberately dropped** — they resumed a
stateful session that no longer exists, and re-homing them would promise resumption nothing
provides. The two DOES-NOT-FIRE fences that pointed at the dead skill
(`ship-readiness-gate:43`, `synthetic-workspace-runtime-test:37`) now name where the phrases
actually go; left as-was they would have told those skills not to fire on phrases **no** skill
owned. `cr-test`'s description is 1007/1024 — the `run-command-room-tests` clause was compressed
to buy the room.

### Changed — `ship-readiness-gate`'s ~80/20 coverage claim, corrected rather than deleted

The "remaining 20% needs verify-cr-release" sentence named a skill that no longer exists. It was
**not** quietly dropped. The 20% is still *addressable* — same attended tier — but it is no longer
*enforced*: nothing tracks position through the plan, auto-classifies responses, or emits a verdict
artifact. The gate now says so, adds the two coverage lines a fixture can never satisfy
(virgin onboarding, destructive probes / loader canary), and carries two consequences: never infer
the attended tier from a PROMOTE, and make the operator state what was actually walked — "attended:
dogfood only, plan not walked" is a legitimate verdict-doc line. **Silence is not coverage.**

### Companion sweep

`bug-regression-suite` (description + 3 body sites + `cleanup-helper.md`),
`synthetic-workspace-runtime-test` (description, fence, the comparison table rewritten to
"attended tier", `fire-mocking.md` ×2, `invariants.md` ×2), `ship-readiness-gate` (description,
fence, coverage block), `cr-skill-builder` (companion list), `cr-test` (description, tier table,
Step 4, consolidation map), `CLAUDE.md` ×3, `README.md` ×3. In `chalette030`:
`review-cr-build/SKILL.md` ×3 (description fence, §3 retirement-chain note, DOES-NOT-FIRE line).

### Owed at ship — closed at the v0.4.1 cut (2026-07-27)

1. **Done.** `plugin.json` version bump 0.4.0 → 0.4.1 + description entry (skill count 16 → 15).
   Its historical `v0.1.0` prose naming `verify-cr-release` among the extracted 16 is accurate
   history — left as written.
2. **Done.** `README.md:7` skill-count parenthetical settled to "15 skills (as of v0.4.1)".
   `chalette030`'s `plugin.json` description names the retired skill inside a sentence about
   what *moved out* at CONSOL1 — that sentence is accurate history (all 18 did move), so it
   gained a "three have since been retired there" clause rather than a rewritten roster.
   chalette030's own CHANGELOG entries are append-only and were not touched.
3. Cowork mirror — carried at the ship step.

## v0.4.0 (2026-07-24) — TI2: triage-intake routes work out (contributor packet + cr1 BACKLOG)

Capability addition. Skill count unchanged (**16**). Zero trigger changes — `triage-intake`'s
frontmatter description is **byte-identical** to v0.3.1 (verified by diff against the branch base).

### Added — "Routing work out" mode in `triage-intake` (`may_ship` operators ONLY)

The gap: work that a fork contributor could execute cold pooled in the maintainer's own
build-specs queue, where a contributor cannot see it, and ad-hoc handoffs had no gate standing
between triage prose and a contributor's eyes.

An item whose verdict is `SPEC` and which passes the **five-clause suitability test** — target
repo is `cr1_clone`; fully specifiable from repo contents; buildable AND testable against the
battery + synthetic fixtures alone; zero client/org/person names needed in spec, code, tests or
PR text; zero ship authority — now yields two extra outputs:

1. **`<specs_dir>/packets/PACKET_<TAG>.md`** — self-contained for a cold fork contributor:
   handoff header (fork → branch → PR, what the builder never does, the BACKLOG TAG), a spec
   body shaped per cr1's checked-in `templates/TEMPLATE_SPEC.md` with §0 **already ruled**, the
   kickoff prompt, acceptance including the scrub AC verbatim, and a **PR-description
   requirements** block carrying the `TEMPLATE_BUILD_REPORT` slots (deviations at top, gates
   table with numbers incl. the mutation check demonstrated by REMOVING the fence, files
   touched, reviewer-visible defaults). Never committed into cr1 — filled records stay out of
   the repo (cr1 G12).
2. **One scrubbed `READY` row on `<cr1_clone>/BACKLOG.md`** (repo root, contributor-visible via
   fork, never fanned out to client repos — promote writes `command-room/` only).

Any "no" on the suitability test → normal maintainer-side spec, no packet, no BACKLOG row. On a
contractor profile the whole section is inert prose behind the `may_ship` gate: delivery stays
PR-attach, `BACKLOG.md` is never touched. INTAKE1 F1 (append offers restricted to `new/`) and F5
(resurrection guard) untouched.

### Added — `scrub_roster` operator key + a FAIL-CLOSED outbound scrub gate

New key in `config/operator.json`, committed default **`null`** (contractor-safe; the real value
lives ONLY in the gitignored overlay, per the CONSOL1 D3 pattern). Before either outbound write,
the full outbound text is grepped against every client/org/person name in the roster.

- `scrub_roster` null / missing / unreadable / **readable but yielding zero names** → **both
  writes refused** with the explicit line `scrub roster unavailable — BACKLOG/packet emission
  disabled`; the maintainer-side spec is still delivered. Fail-closed by construction: a
  contractor has no roster and never needs the feature. An empty or truncated roster is an
  unavailable roster, never an all-clear (REVIEW_TI2 F-1 — Drive-sync truncation is a live
  failure mode on this substrate). The grep matches individual name tokens as well as full
  names, case-insensitive.
- A roster hit blocks the write and surfaces the offending line for rewrite — **never** an
  automatic name substitution.

This cannot ride cr1's G9 alone: G9's first-name dictionary plus placeholder allowlist cannot
know real ORG names, which is precisely how an org name has slipped past a name guard before.
The mechanized backstop is CI-side in cr1 (`BACKLOG.md` joins G9's staging scan).

### Changed — writer contract (explicit amendment, not a silent widening)

`triage-intake` may now write exactly **two** outbound surfaces, both post-scrub:
`<specs_dir>/packets/PACKET_*.md` and `<cr1_clone>/BACKLOG.md` — the latter **staged via
`git add`, never committed, never pushed**. No other file in any repo is ever written by triage.
A triage session still ends with **zero new commits** in the cr1 clone; the maintainer commits
and pushes in his own ship window. Everything else (no substrate events, no version/CHANGELOG,
ship/promote stays with `may_ship`) is unchanged, as are the single-writer folder rules.

### Changed — closing decision table gains an `Eric?` column

Records the suitability verdict per `SPEC` item (`n/a` for non-SPEC verdicts, `—` on a
contractor profile). When a packet is emitted, the staged `BACKLOG.md` diff is shown under the
table — that staged diff IS the "this is pending" marker.

### Companion change in cr1 (separate repo, separate branch)

Repo-root `BACKLOG.md` seeded with its covenant header, `BACKLOG.md` added to G9's staging scan
(`SCAN_STAGING_FILES`), G2's `BACKLOG\.md` token relabelled (the ban still holds over the plugin
payload — the repo-root dev backlog is the only legitimate home), one `CONTRIBUTING.md` pointer,
and regression pins for both guards. No cr1 version movement.

## v0.3.1 (2026-07-24) — MAINT2: Git-Bash fence fix + two skill retirements

Maintenance batch. Skill count **18 → 16**.

### FIX (priority) — the operator-profile pattern silently no-opped under Git Bash on Windows

`SHIP_RECORD_CONSOL2` finding 3. **Pattern-wide across all 11 reading skills, pre-existing**
(it predates CONSOL1; the F-1 fix in `901898f` correctly matched the established pattern and
did not introduce it).

Two compounding traps, both silent:

1. `${BASH_SOURCE[0]}` is **empty** when an agent runs a SKILL.md block through a Bash tool —
   it is not a sourced script. `dirname ""` is `.`, so the plugin root resolved against
   whatever the cwd happened to be.
2. `pwd` under Git Bash yields an MSYS path (`/c/Users/…`). Native `python.exe` resolves a
   leading `/c/…` against the current drive → `C:\c\Users\…`, so `os.path.exists()` returned
   **False for both config files**. MSYS rewrites path-like ARGV for a native `.exe` but never
   text inside a `python -c` script string — and that interpolation is exactly how the skills
   pass the paths. The merged profile came back **empty**, resolution fell through to the
   synthetic default, and **nothing raised**: an operator granted `allowed_targets: ["real"]`
   silently ran synthetic.

The canonical bash preamble now **searches** for `config/operator.json` (candidates: the
`$CHALETTE_DEV_ROOT` escape hatch, `$PWD`, `$PWD/chalette-dev`, the parent, `~/repos/chalette-dev/…`,
`~/.claude/plugins/marketplaces/*/chalette-dev` — never a hardcoded machine path), converts
the hit with `cygpath -m` (`C:/Users/…`, readable by both MSYS bash and Windows python), and
**fails loud** when the root or the profile is unreadable. It is delimited by
`# --- operator-profile resolution` / `# --- end operator-profile resolution ---`, and the code
inside is byte-synced across the four bash-form skills (comments are per-skill; code is not).

- **Bash form (4):** bug-regression-suite, ship-readiness-gate, synthetic-workspace-runtime-test,
  verify-cr-release. Also `DEV_PLUGIN_ROOT` replaces the ambiguous `PLUGIN_ROOT`/`SELF` naming —
  in synthetic-workspace-runtime-test `PLUGIN_ROOT` means the *Command Room* plugin under test.
- **Python form (7):** capture-for-code, cr-skill-builder, cr-test, cross-skill-interaction-test,
  scale-stress-test, smoke-watch, triage-intake — each gains the same loud fence and states the
  native-path contract for `SKILL_PLUGIN_ROOT`. `cr-skill-builder/references/cr-contract-checklist.md`
  also moves off its `operator.json`-only read onto the merged-overlay form. `CLAUDE.md` documents
  the trap so it is not reintroduced.

**Guard 2 gains Fence 4 — +29 tests, 24 → 53** (51 once the two retirements below drop their
two `quick_validate` cases). Static analysis was structurally blind to this bug, so
the fence **executes** the shipped preamble out of each SKILL.md and asserts the merged profile
reads at least one file: once with cwd = repo root (no env hints), once from an unrelated cwd via
the escape hatch. Plus: an unfindable root must exit non-zero with `FATAL`; resolution code must
stay byte-synced; `BASH_SOURCE` is banned outside comments; every operator-reading skill must
carry the loud-failure line; and one test documents the MSYS-resolution mechanism itself.
Parametrization is keyed on the **consumer** (`'$OPERATOR_CFG'`), not the sentinel, so a skill
that drops the preamble fails instead of vanishing from the test run.
Mutation-verified: reverting the preamble to the pre-MAINT2 form fails 5 tests (all 4 executable
ones); removing only the `cygpath -m` conversion fails the repo-root resolution test.

### RETIRED — compare-canonical-vs-freelance (deleted)

Its validation niche is complete. It existed to validate the **v3.13.8 §3.6 widget degradation
ladder** per skill by firing each widget skill twice — once canonical, once through a mocked
freelance fallback — and diffing. Command Room is at v5.2.0; the freelance fallback it diffed
against no longer exists, widget output goes through `widget_transport.render_and_persist` and its
validators, and the property the ladder diff was inferring is asserted directly by synthetic
invariant **I2 `no_freelance_render`** (plus I1 `canonical_render_invoked` and I16
`file_uri_transport`). The `ship-readiness-gate` step built on it (old Step 2) is gone and its
steps renumbered 3–6 → 2–5. Its coverage claims were **corrected, not silently inherited**:
Bug #46 now cites I1/I2/I16, and Bug #48 (action-label drift) is stated honestly as **not**
covered here at all — it is cr1's `CanonicalActionError` renderer validator running in the unit
tier (`cr test --quick`); I15 covers dispatch shape, not labels.

### FOLDED — run-command-room-tests → cr-test (deleted)

Step-0-verified: `cr-test` **never delegated to it** — it always called `tests/run_all.py`
directly, which discovers every suite at call time, while the retired skill ran a hardcoded five
of 40+. Its trigger phrases now live in **cr-test's frontmatter description** (description-only
routing — the phrase has to be in the description to route) as aliases for `cr test --quick`:
`internal: run plugin tests`, `run command room tests`, `command room health check`,
`verify plugin code`. cr-test's description: 607 → 905 chars, inside the ≤980 doctrine.

### Sweep

Every live companion reference to both retired skills removed: `ship-readiness-gate` (description
companion list, target-mode bullet, Step 2, coverage claim, failure mode, implementation
references), `verify-cr-release` (description companions, DOES-NOT-FIRE fence, companion-skills
list, plugin-family list), `bug-regression-suite` (SKILL.md ladder list + `bug-catalog.md` trigger
line), `synthetic-workspace-runtime-test` fence, `preview-command-room-widget` see-also, `cr-test`
(3 places), `README.md` table (+ a retirement note), `CLAUDE.md` skill count, `plugin.json`
description head. Earlier CHANGELOG entries and the `PRIOR HISTORY` half of the plugin.json
description are **append-only history** and keep their original wording — this entry is what tells
a reader the skills are gone.

## v0.3.0 (2026-07-24) — CONSOL1: single canonical home for the shared QA/dev toolkit

chalette-dev is now the **one and only home** of the shared testing / verification /
skill-building toolkit. The same 18 skills were duplicated in the private `chalette` plugin
(chalette030) and the two copies had silently drifted; CONSOL1 removes the `chalette` copies
(there, `chalette` v0.10.0) and reconciles the survivors here to their canonical, operator-fenced
form. Skill count unchanged (18). Second-eyes review (REVIEW_CONSOL1) is pending before either
repo publishes.

### Per-skill reconciliation (newest-wins WITH fence preservation)
- **bug-regression-suite** — kept dev base (operator-fenced target resolution + overlay);
  ported `ChaletteHQ/cr1` repo naming; noted the dual-copy byte-identical catalog invariant
  RETIRED (single copy now); L1 real-name audit-residue docs confirmed removed (deletion-forward).
- **capture-for-code** — kept dev base; scoped the placeholder-names rule to non-`real` operators
  (INTAKE1 F7); added the operator.local.json overlay.
- **cr-test** — added rule 0 (`cr1_clone` from the operator profile wins if set); "M's call"
  delegate → "the ship operator's call (`may_ship`)".
- **cross-skill-interaction-test** — operator-fenced (requires `real`; no synthetic paste-back mode);
  neutralized M-identity prose.
- **ship-readiness-gate** — A (chalette030) won content (ChaletteHQ/cr1 + promote fan-out wording);
  **rebuilt on the operator pattern** — default synthetic, m-workspace only when `allowed_targets`
  grants `real`; dropped the false "fixtures unpopulated" claim; verdict/findings paths resolve
  from the profile; Step-0 clone detection resolves `cr1_clone`.
- **synthetic-workspace-runtime-test** — kept dev base (populated fixtures); **re-added Invariant 7
  `event_gate_routed`** (D6); `cr1_clone`-resolved fallback replaces the stale `commandroom1`
  marketplace path; shape-prose neutralized.
- **triage-intake** — kept dev base; **ported INTAKE1 F5 (resurrection guard)** — which had landed
  only in chalette030 and would otherwise have been lost; F4 `chalette_clone` operator-aware;
  `specs_dir` + `parking_doc` keys; `may_ship`-gated spec delivery; F1 single-writer verified present.
- **verify-cr-release** — kept dev SKILL.md + VERIFICATION_PLAN.md; ported A's findings-log-format
  production-HEAD wording (ChaletteHQ + `promote_core_to_clients`); `Tester: the operator`; output
  paths resolve from the profile (attended M's-Cowork prose kept — authority-accurate).
- **cr-skill-builder** (L4) — output dir resolves from the profile (workspace_root or a
  cr1_clone-adjacent scratch); the leak-token negative example's real Windows username swapped for a
  placeholder; overlay added to the clone read; companion refs re-pointed `chalette:`→`chalette-dev:`.
- **skill-creator** — stale `plugin-source-v2/skills/` path rule replaced with the cr1-clone
  canonical surface + cr-skill-builder contract pointer.
- **smoke-watch / scale-stress-test** (L2 / L3) — operator-fenced: smoke-watch requires `real`
  (no synthetic mode — honest); scale-stress-test defaults to the populated `mature_workspace`
  fixture, real only when granted. Paths resolve from the profile.
- Byte-identical clean skills (compare-canonical-vs-freelance, preview-command-room-widget,
  run-command-room-tests) — no change beyond deletion of the chalette030 duplicate.

### Operator profile + overlay
- `config/operator.json` gains `chalette_clone`, `specs_dir`, `parking_doc` (all null / contractor-safe).
- New gitignored `config/operator.local.json` overlay: every reading skill loads `operator.json`
  then overlays `operator.local.json` per-key. Committed default stays contractor-safe; M's real
  profile lives only in the overlay. `.gitignore` added.
- `CLAUDE.md` + `README.md` document the overlay, the single-canonical-home rule, and the guards.

### Structural guards (permanent)
- **Guard 1** `scripts/check_toolkit_overlap.py` — fails if any shared-toolkit skill name exists in
  both plugins. Mutation-fence verified (planted duplicate → exit 1 naming it; intersection logic
  disabled → passes silently).
- **Guard 2** `tests/test_operator_fences.py` — asserts the committed operator.json stays
  contractor-safe (allowed_targets==["synthetic"], may_ship/may_promote false, workspace_root null,
  operator!="m"), operator.local.json untracked, and quick_validate passes for all 18 skills.
  Mutation-fence verified (may_ship→true → test fails; assertion removed → passes).
- `.github/workflows/toolkit-guard.yml` runs Guard 2 + quick_validate unconditionally, Guard 1 only
  when `CHALETTE030_READ_TOKEN` is present (absent → SKIPPED/green, so forks never fail).

### quick_validate hygiene
- Removed stray top-level `template_version` frontmatter key from regenerate-skill, skill-generator,
  voice-test.
- Shrank regenerate-skill (1082→906) and skill-generator (1113→927) descriptions to the ≤980
  doctrine, preserving every trigger phrase + DOES-NOT-FIRE fence verbatim.
- 18/18 skills pass quick_validate.
