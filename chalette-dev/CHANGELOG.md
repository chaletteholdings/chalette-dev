# chalette-dev — Changelog

(Release history before v0.3.0 is at the bottom of this file, moved out of `plugin.json` on 2026-10-24.)

## v0.9.8 (2026-11-12): the three-computer build rules and the Nov 11 merge gates

Owner rulings 2026-11-11: the three-computer rules (cr1#1051) and the merge gates (cr1#1041). Until now they lived only in the owner's workspace and in cr1 issue text, so builder chats on the other computers had no copy in git.

- **docs/trains/THREE_COMPUTER_PLAYBOOK.md (new):** the Mac checks and never builds, two builders on each PC, one coordinator on either PC that merges without asking, the control issue, the ten rules, what happens when a computer goes quiet, and who decides what. Adds the eight merge gates from cr1#1041 (Mac CI, full battery every 5 merges, no path list, promote overrides, red main keeps merging outside the broken area, stacked lanes, one review round, one timeout re-run), what is not built yet, and the check-name rename in flight (cr1#1114).
- **docs/trains/CHAT_PROMPTS.md (new):** the coordinator and builder prompts, now pointing at the repo copy of the playbook instead of a workspace file.
- **docs/trains/TWO_MACHINE_PLAYBOOK.md:** bannered as superseded, kept for history.
- **docs/trains/merge_pr.sh:** a red main no longer blocks every merge; the coordinator re-runs with `MAIN_RED_OK=1` for a pull request outside the broken area (gate 5).
- **battery skill:** the full battery runs every 5 merges, not per batch; a known red does not stop merging, a new one does and starts a fix; failures are logged on cr1#1041; revert-first is gone.
- **cr1-desk skill:** the rulings paragraph names the coordinator and the Nov 11 gates in place of the Oct 25 ones.
- **README:** one line pointing at the playbook.
- **tests/test_train_rules.py:** pins the gates in the playbook, the prompts' pointer, the banner, the skills' wording and the script switch.
- **Verified:** `pytest tests/` passes; the diff scans clean with cr1-scrub; no em dashes or exclamation marks added. Not verified by a run: `merge_pr.sh` with `MAIN_RED_OK=1` against a real red main. cr1's own `cr1-build`, `ISSUES.md` and `DEVELOPMENT.md` still carry the old gates; that is cr1#1041's acceptance check, not this release.

## v0.9.7 (2026-11-06): critical or backlog, decided at filing

Owner ruling 2026-11-06 (cr1 ISSUES.md sections 7 and 12, cr1 PR #855): the tracker keeps only critical tickets, and a merged fix is tested by use. A ticket is critical only if it can write the wrong thing to a book or lose data, send or draft without the owner's word or to the wrong person, expose client or personal information, or stop the Hub or Maintenance. This release is the mechanism, so the ruling binds at report time without anyone remembering it.

- **cr1-report section 1a:** every report is judged against the four tests from the chat. One met: label `critical`, one line at the top of the body naming the test (`**Critical:** can close the wrong commitment`), nothing asked. None met: one question, "This does not meet the four tests. File it anyway, or drop it?", and a filed-anyway ticket gets `backlog`, no milestone. Unsure is treated as critical with the evidence named. Severity and the four tests are kept apart. Section 6 files the decided label and reads it back; section 7's reply says which, and that a backlog ticket is owed no test.
- **cr1-test section 1:** "what needs me" lists only issues carrying both `critical` and `needs UAT`. A `needs UAT` without `critical` is not owed a test; "sort them" judges those against the four tests, labels the critical ones and closes the rest on the builder's verification (Matthew closes, a team member proposes).
- **cr1-test section 7, backlog review:** "backlog review" lists `backlog` tickets over 30 days old, oldest first, and "close them" closes each as not planned with a one-line comment. A team member lists and tags Matthew, never closes. Three trigger phrases added.
- **cr1-desk:** a Backlog pile, counted only, between the test pile and Ready to build; the glossary says when UAT is owed.
- **docs/trains/merge_pr.sh:** after the merge, reads the issue's labels: `critical` gets the verify comment and `needs UAT` as before; anything else is closed with the one-line close comment. The playbook line says so.
- **tests/test_critical_only.py:** pins the four tests and the question in cr1-report, the decided labels in its filing step, the `critical,needs UAT` queue and the backlog review in cr1-test, the trigger phrase, and the label gate in the merge script. Seven of eight were seen to fail before the change.
- The build side (cr1-build reads the label, never guesses; `needs UAT` and Please verify only on `critical`; other fixes close on merge) and the ISSUES.md section 2 paragraph pointing at this mechanism are a separate pull request on cr1, `Refs #846`. The labels `critical` and `backlog` were created on chaletteholdings/cr1 the same day.
- **Verified:** `pytest tests/` passes; the diff scans clean with cr1-scrub against the owner's book; no em dashes or exclamation marks added. Not verified by a run: the three skill flows in a fresh chat (done looks like in the pull request).

## v0.9.6 (2026-11-01): testers use their own folder

Owner ruling 2026-11-01, extending cr1#448 (which allowed it on 2026-10-26; the skill never picked it up).

- **cr1-test step 2.3:** a team member always tests in their own real folder, never a client's and never a sample brain. Back up before any step that converts, moves, deletes or rewrites files, resets settings or runs Maintenance; sample entries a test adds are removed after. Matthew's own tests keep the test-folder rule for destructive steps.
- **cr1-test script and evidence:** the setup line names the backup; files are reset from the backup between runs; visual evidence is the exact error text, since a real-folder screenshot is never attached.
- **docs/TEAM_GUIDE.md and docs/REPO_GUIDE.md:** the same rule in the setup and the test-queue lines.

## v0.9.5 (2026-10-26): the name check refuses when it has no names (cr1#455)

- **cr1-scrub `terms`:** reads people, orgs and threads from a current Command Room 1 book, which keeps them under an "entities" block, as well as from the older flat layout and the split parts. Before this, a current book gave no names and every scan passed on the fixed checks alone while reporting clean.
- **cr1-scrub `terms` refuses:** when no names come out of the book (a wrong folder, an unreadable or empty book, or the private family list alone), it prints nothing, says "The name check did not run: no names could be read from this workspace." and exits 2. cr1's pre-commit guard and cr1's promote step already stop on a failed terms step.
- **cr1-scrub SKILL step 2:** says what to do on that refusal.
- **tests/test_scrub_scan.py:** a nested book gives the same names as a flat one; a missing folder, an empty book and an empty book with a sample family list loaded each refuse. Each new test was seen to fail before the change.
- **Verified:** `pytest tests/` passes. Checked by hand, not by a test: on the owner's own book the name list is identical before and after (same entries, same order).

## v0.9.4 (2026-10-26): a guide to every repo the team can open

- **docs/REPO_GUIDE.md:** what each repository Isabella and Erick can open holds (cr1, this toolkit, the CRM pilot, the brand tools, the website, and the read-only and retired ones), how it works, how to use it, where their time helps most, and what stays with Matthew. Links to TEAM_GUIDE for setup and the after-test sequence rather than restating them; counts are dated. States the team's jobs as Matthew set them on 2026-10-26: test fixes, keep the Chalette Design System current as the source of truth, with Matthew approving every change before it is published, and (Isabella) test the CRM; nobody is asked to build.
- **docs/TEAM_GUIDE.md and README:** one line each pointing at the new guide.
- **Verified:** `pytest tests/` passes; the new and changed files scan clean against the full name list; no em dashes or exclamation marks added. Rebased onto v0.9.3 (#28).

## v0.9.3 (2026-10-26): the team tests, Claude checks, Matthew signs off

Owner ruling 2026-10-26, cr1#448. The rules side is ISSUES.md section 12 in cr1.

- **cr1-test:** Erick and Isabella test on the staging plugin `cr`, in a test folder only. Starting a test assigns the issue to the tester, so two people never test the same fix; stopping without a result releases it. A team member's pass never closes: it swaps `needs UAT` for the new label `ready to close` and tags Matthew.
- **cr1-test section 6, Matthew's sign-off:** "what needs my sign-off" lists every `ready to close` issue, and Claude checks each pass fresh against six conditions (right build, 3 of 3 runs, a log per run showing the fix's own path ran, evidence per criterion, neighbours checked, scrub clean). One line each, holds or does not hold. Only Matthew's word in that chat closes. A pass that does not hold goes back to the tester (a gap in the test) or to build (a real failure).
- **cr1-test queue:** Matthew's "what needs me" opens with the sign-off count; a team member's leaves out issues someone else is testing and lists real-folder tests as Matthew only.
- **cr1-desk:** a new first pile, waiting on Matthew's sign-off; the closing line names the sign-off path.
- **docs/TEAM_GUIDE.md:** install `cr` from `chaletteholdings/cr1`, a test folder, and what happens after a test.
- **tests/test_signoff.py:** pins that a team member never closes, the label swap, and that only Matthew's word closes. The sign-off checks the GitHub account first; a person saying they are Matthew is not enough there.
- **tests/test_who_is_running.py:** compares the whole "Who is running this" section, bullets included, across the four cr1 skills; it used to stop before the bullets. Seen to fail on a changed bullet.

## v0.9.2 (2026-10-26): a guide for the team, and a sheet for the rebrand

- **docs/TEAM_GUIDE.md:** what this repo is, setup, the four things to say, what a team member decides and what goes to the owner, the no-client-data rule, what a good report and a good test look like, where things live. Written for Isabella and Erick.
- **docs/POSITIONING_AND_BRAND_SHEET.md:** the source of truth while Chalette is rebranded and repositioned. Every brand and positioning item with a status (Ruled, Working, Open, Retired), which file wins, and how a row gets decided. No client names, prices or money figures.
- **cr1-scrub:** Isabella joins the team list, so her own name in an issue she files is not flagged. `scrub_scan.py` TEAM and TEAM_FULL, and the SKILL's allowed list.
- **README** points at both documents.

## v0.9.1 (2026-10-25): the team, the merge rule and the battery, as they are now

- **Who is running this (cr1-report, cr1-desk, cr1-test, cr1-scrub):** a GitHub account other than the owner's or Erick's is another team member under their own name, not Erick. Proposals read "Proposed by <their name>, Matthew to confirm."
- **cr1-desk:** who merges follows the owner ruling on cr1#289 of 2026-10-25 (three green quick-check shards plus the review; one full battery on main per batch; a red battery on main stops merges until fixed or reverted). The ISSUES.md update is tracked in cr1#420. The "no second developer" line is gone.
- **battery:** `battery --quick` is cr1's quick check (`run_all.py --quick`, about 4 to 8 minutes), the same check CI runs before a merge. `run the battery` is the full battery (about 35 to 47 minutes), run once on main per batch and before a promote, not before every commit. The "~10s" claim is gone.
- **cr1-scrub:** the departed developer's first name is no longer on the team allowlist, so the scan flags it.
- **CI:** toolkit-guard runs on pull requests and on pushes to main only; every pull request used to run it twice.

## v0.9.0 (2026-10-25): the dev toolkit moves in from the owner's plugin

Owner ruling 2026-10-25: `chalette` is the owner's personal plugin; `chalette-dev` is the development toolkit for the owner and the team. Eleven skills moved here from `chalette` and leave it in its v0.13.0.

- **Moved in:** `battery` (was `cr-test`), `bug-regression-suite`, `synthetic-workspace-runtime-test`, `cross-skill-interaction-test`, `scale-stress-test`, `ship-readiness-gate`, `cr-skill-builder`, `skill-creator`, `skill-generator`, `regenerate-skill`, `preview-command-room-widget`.
- **Renamed `cr-test` to `battery`** so it cannot collide with `cr1-test`. Say "run the battery", "battery --quick", "battery --ship" or "battery --attended"; the old "cr test" phrases are gone, and a test fails if they come back.
- **Scrubbed on the way in:** the old `ChaletteHQ/cr1` address now reads `chaletteholdings/cr1`; a real company name used as a fixture placeholder in `synthetic-workspace-runtime-test` and `cr-skill-builder` is now `Acme Bakery`; the owner and the implementer are named by role; plugin prefixes on moved skills now read `chalette-dev:`; three packaged `.skill` archives nothing referenced were dropped from `skill-creator`. The private name scan is clean over the branch.
- **Team fence:** every moved skill opens with the same note: a contractor runs it on the synthetic fixtures or a copied test brain only, never a real client folder, and never ships or promotes.
- **Tests:** the skill set is pinned at the four `cr1-*` skills plus the eleven; new fences for the old `cr-test` name, the old repo address and the team note, each seen to fail when its rule is broken. A pre-existing defect in `test_no_cr2_repository_reference_remains` is fixed in passing: its pattern held two literal backspace characters, so the bare `cr2` check never matched; it now reads `cr2` and the four skills still pass.

## v0.8.2 (2026-10-24): nothing here files on Command Room 2 any more

Command Room 2 is retired (owner ruling 2026-10-22) and its three stale pull requests and the core/labs issue were closed on 2026-10-24. This release removes the last of it from the four skills.

- **cr1-desk, cr1-report, cr1-scrub, cr1-test** lose the one-line fallback that let the owner route an item to the CR2 repository. The skills name one repository, `chaletteholdings/cr1`.
- **cr1-scrub `scrub_scan.py`** drops the `CR2_SCRUB_LOCAL` environment fallback, and the former CR2 developer is no longer on the allowed team list, so the name is flagged like any other.
- **tests/test_cr1_target.py** now asserts that no skill names CR2 at all, instead of allowing exactly one fallback line.
- **README** says so.

Verified: `pytest tests/` green; `quick_validate` passes on all four skills.

## v0.8.1 (2026-10-24): the manifest says what the plugin is, the config holds what the skills read

Cleanup from the 2026-10-23 dev-system audit. No skill text changed; triggers unchanged.

- **plugin.json description** was a 22,892-character changelog, 22 times the per-skill description cap and loaded wherever the manifest is read. It is now two sentences, the same ones the marketplace entry uses. The old text is preserved verbatim under "Release history before v0.3.0" at the bottom of this file. The `verification` keyword is gone with the QA toolkit.
- **config/operator.json** keeps the two keys the four skills read, `operator` and `operator_name`. Removed: `role`, `cr1_clone`, `workspace_root`, `intake_root`, `chalette_clone`, `specs_dir`, `parking_doc`, `scrub_roster`, `allowed_targets`, `may_ship`, `may_promote`, `may_build_own_spec` and their comments. No skill on main read any of them (the QA toolkit that did moved to the chalette plugin on 2026-10-04). Who may merge, ship or promote is the GitHub role on the repo, not a JSON field.
- **tests/test_operator_fences.py** drops the fences on the removed keys and the bash-preamble execution tests, which had been skipped on every run since v0.7.0 because no skill carries the `$OPERATOR_CFG` preamble any more (4 skipped on every CI run). Kept: the committed profile is not the owner, the overlay is never tracked, every skill passes quick_validate, every operator read fails loud, no `BASH_SOURCE` path resolution. Added: the committed profile carries exactly the keys the skills read, so dead fields cannot creep back.
- **tests/test_description_budget.py** now also checks `plugin.json` and `marketplace.json` descriptions against the same 980-character budget; the docstring describes the four cr1 skills instead of the retired toolkit.
- **toolkit-guard.yml, .gitignore, README** comments and the Checks paragraph describe what runs now.

Verified: `pytest tests/` green with 0 skipped; `quick_validate` passes on all four skills; a planted 1,100-character manifest description and a planted extra key in operator.json were each seen to fail before the change was reverted.

## v0.8.0 (2026-10-22): the skills move to Command Room 1

Matthew retired Command Room 2 on 2026-10-22 and went back to building cr1 (`ChaletteHQ/cr1`). There is no second developer: Matthew builds with Claude Code (cr1-build, a project skill in the cr1 repo, which runs a fresh-context reviewer before it opens a pull request) and merges. Erick still uses these skills and still gets proposals, not decisions. MINOR bump (skills renamed and retargeted).

- **Renamed with history (`git mv`):** cr2-report, cr2-scrub, cr2-test, cr2-desk became cr1-report, cr1-scrub, cr1-test, cr1-desk. Trigger phrases are unchanged except the "log this for Louis" ones, which are gone.
- **Retargeted:** every `repos/ChaletteHQ/cr2` call is now `cr1`; rules point at cr1's `ISSUES.md`, `CONTRIBUTING.md` and `DEVELOPMENT.md`; title area tags use cr1 skill names (`[Morning briefing]`, `[Inbox triage]`, `[Meeting notes]`, ...). Each skill keeps one line: when the owner explicitly says a problem is on CR2, it still files on `ChaletteHQ/cr2`.
- **Removed, not renamed (CR2-only):** the CR2 developer (hand-offs, mentions, "waiting on" piles), the `core`/`labs` routes and route question, CR2 folders (`00_docs`, `02_product`, `03_tests`, `06_labs`), the cloud intake drop, the CR2 run-log folder, the labs plugin, `CR2_RUNTIME`. A build brief's "Writes:" is now nothing / events in the book / a page in the project folder.
- **cr1-test version gate:** the fix must be in what is installed. For Matthew's staging `cr` plugin (follows `main` by commit), its installed commit must be at or after the fix's merge (GitHub's compare API). For `command-room` (clients get changes only when Matthew promotes), a released version must list the issue in `command-room/CHANGELOG.md` on `main`. The CHANGELOG is over 1 MB, so it is read raw.
- **cr1-desk:** piles are waiting on your test, waiting on Matthew's merge, needs your decision, ready to build. The brief asks at most five questions (the route question is gone). Glossary: "Merge: Matthew accepting the change into main; clients get it at the next promote."
- **Versions and CHANGELOG** in cr1 are set only at release by Matthew's ship-cr-plugin flow; a pull request never touches them (was "needs version" / "Louis sets the version").
- **cr1-scrub:** the scrub's `terms` step now also reads a cr1 book's single `_hq/data/entities.json` (people, orgs, threads). Before this it read only the older split `_hq/data/entities/*.jsonl.txt`, and a cr1 book has none, so on Matthew's book it returned no names at all. Output on a split book is unchanged. `terms` and `scan` keep the same arguments and output, because cr1's pre-commit guard calls them. `CR1_SCRUB_LOCAL` is read first, `CR2_SCRUB_LOCAL` still works. The skill now says how to switch on cr1's commit guard (`git config core.hooksPath command-room/.githooks`, `git config scrub.book`) and warns when the name list came back empty. One example in Step 3 was replaced with a neutral one.
- **Tests:** `test_who_is_running`, `test_test_log` and the description budget follow the new names. New `test_cr1_target.py` (the four skills exist under cr1 names, `ChaletteHQ/cr2` appears only in the one fallback line, no CR2-only text or route remains, no em dash or exclamation mark) and `test_scrub_scan.py` (a cr1 book and a split book give the same names; a name and an amount are caught). README, CLAUDE.md, marketplace and workflow text say cr1.

Verified: `pytest tests/` 57 passed, 4 skipped (the bash-preamble tests, as before). `quick_validate` passes on all four skills. Both new tests were seen to fail on purpose: a planted route and developer name in cr1-desk, and the scrub with its `entities.json` read switched off. The scrub's terms on a synthetic split book are byte-identical before and after; on Matthew's real cr1 book the old script found 0 names and the new one finds several hundred (count only, nothing printed). The `gh api` commands in the skills were checked against cr1: repo and labels, the plugin version on `main`, the staging marketplace, the compare call and the raw CHANGELOG search. Not verified: cr1's `ISSUES.md`, `command-room/.githooks/`, the `--quick` flag and cr1-build are being added in parallel and are not on cr1 `main` yet; the trigger evals are not run.

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

## Release history before v0.3.0

Moved verbatim from `.claude-plugin/plugin.json`'s `description` field on 2026-10-24. Historical; the toolkit it describes moved to the chalette plugin on 2026-10-04.

Chalette Command Room 1 dev skills, shared by Matthew and Erick: cr1-report, cr1-scrub, cr1-test, cr1-desk. v0.8.0 (2026-10-22): retargeted from the retired Command Room 2 (ChaletteHQ/cr2) to Command Room 1 (ChaletteHQ/cr1). The four cr2-* skills are renamed cr1-* with their git history; CR2-only mechanics are removed (the CR2 developer handoffs, core/labs routes, CR2 folders, preview repo and labs plugin); the version gate in cr1-test checks the staging cr plugin by commit and the command-room plugin by released version; the scrub also reads a cr1 book's single entities.json. Each skill still files on ChaletteHQ/cr2 when the owner explicitly says a problem is there. PRIOR HISTORY: Chalette Command Room 2 dev skills, shared by Matthew and Erick: cr2-report, cr2-scrub, cr2-test, cr2-desk. v0.7.0 (2026-10-04): the Command Room 1 QA toolkit (16 skills) moved to Matthew's private chalette plugin; this plugin is Command Room 2 only. PRIOR HISTORY: Chalette internal dev & QA toolkit for Command Room. v0.6.0 (2026-10-04): the Command Room 2 dev skills join the toolkit so Matthew and Erick work the same way: cr2-report (file a bug or feature on ChaletteHQ/cr2), cr2-scrub (keep client, personal and money information out of the repo; private name lists stay in a gitignored config/scrub.local.json), cr2-test (supervised acceptance tests, results posted to the issue), cr2-desk (everything pending to build, in plain language, and a guided build brief). Operator-aware: Matthew decides routes and closes issues; for anyone else those become proposals. cr2-build stays a project skill in the cr2 repo. Skill count 15 -> 19. PRIOR HISTORY: Chalette internal dev & QA toolkit for Command Room. v0.5.1 (2026-07-29) — REFGAP1: cross-skill-interaction-test's three cited reference docs recovered + a permanent dangling-reference guard. The bug, found live at the v5.5.1 attended gate: SKILL.md Step 1 loads references/sequence-catalog.md (plus temporal-wait-strategy.md and multi-phase-verdict-aggregation.md), but git tracked only SKILL.md — the references/ directory existed and was EMPTY, so the skill failed on a missing file even with a valid operator profile. Recovery finding: the files never existed anywhere — chalette-dev, chalette030, and retired-plugin git history never tracked them and no session transcript contains a write of them; BUILD_VCRRETIRE §7 had already recorded all three inside a 13-citation dangling-read set across five skills and deferred the guard to its own build. This is that build. The three docs were authored from SKILL.md's own inline content: the catalog carries all 17 index rows (original 15 + the two OBJ1 sequences), with the Bug #51 cascade sequence READY and every derived entry DRAFT under an explicit promotion rule (walk once, confirm expected substrate writes, promote to READY; DRAFT failures report ADVISORY, never blocking — an unverified draft expectation cannot assert a phantom regression). Expected-write event names checked against cr1's events.schema.json; pulse and the commitments task are flagged as scheduled surfaces rather than skills; the weekly-audit row's surface is noted as now living in cleanup; each file carries a provenance header so nobody hunts a lost original again. Guard 4 added (tests/test_reference_integrity.py), the instruction-layer-gap class inverted from G13: every references/*.md a SKILL.md cites must be git-TRACKED (untracked is absent at client install), present on disk, and non-empty. Bare citations resolve against the citing skill; prefixed other-skill/references/ citations resolve against the named skill when it exists in this repo; cross-repo citations (command-room/… lives in cr1, verified present there) are skipped as outside CI's jurisdiction. The 8 remaining pre-existing dangling citations (bug-regression-suite x2, ship-readiness-gate x3, skill-generator x2, skill-creator's mis-citation of a checklist that actually lives under cr-skill-builder/references/) are grandfathered in a baseline that RATCHETS BOTH WAYS: a new dangling citation fails immediately, and fixing a grandfathered one without deleting its baseline row also fails, so a stale row cannot mask a re-regression. Coverage asserted, not assumed: the scan must visit every skill's SKILL.md, with three controls — positive (the three repaired citations resolve tracked), negative (a fabricated citation registers as dangling), and a misattribution pin (a prefixed citation resolves to its OWNER, not the citing skill — the exact false-dangling the naive resolver produced during this build). Mutation-verified both directions: untracking the catalog went 2 red, satisfying a baseline entry went ratchet-red, restored green. Battery 59 -> 65 passed; Guard 1 OK 15/20/0. Deliberately NOT done: authoring the 8 grandfathered docs (each belongs to its owning skill's build, with review) and any SKILL.md text change — all frontmatter descriptions untouched repo-wide, zero trigger changes. Skill count unchanged (15). PRIOR HISTORY: Chalette internal dev & QA toolkit for Command Room. v0.5.0 (2026-07-27) — GATE1: build authority decoupled from may_ship. A contractor can now write a spec and build from it in one continuous pass, with review happening ONCE at the pull request — and still hold ZERO ship authority. Root cause: may_ship conflated three distinct authorities (may I build from a spec I wrote myself / may I bump the version + write CHANGELOG + cut a release / may I promote to client repos) and there was no key for the first, so it rode may_ship by implication. New operator key may_build_own_spec splits it out. It SHIPS TRUE — the one authority key that does. The spec ruled it overlay-only with a committed false, matching the other two; M overruled that on the call: an overlay is a hand-created gitignored file, so the grant would have been invisible to git pull, absent on a fresh clone, and silently lost on a re-clone — a forgettable setup step guarding something a PR review already catches. Shipping it on makes a plain git pull the entire setup. The cost taken knowingly: the value travels with the repo, so a future contributor inherits build authority instead of being granted it one at a time; with two collaborators on a private repo and may_ship / may_promote / allowed_targets all still shipping locked, that is a small price. Consequence recorded in three places: contractor-safe now means zero SHIP authority and synthetic targets only, not zero authority. This had to be a code change and not a verbal agreement: the pre-build gate was prose inside triage-intake/SKILL.md, and prose re-asserts itself on every run — the next triage session would have read 'contractors never self-approve a spec into a build' and asked for the handoff again regardless of what was agreed on a call (the instruction-layer-drift class). Two sentences re-gated in skills/triage-intake/SKILL.md: the operator-aware blockquote now lists may_build_own_spec and states the two authorities separately instead of one implying the other (may_ship: false spells out what it withholds — version bump, CHANGELOG, release, promote, self-merge — and binds regardless of the build grant); the 'Writing the spec' delivery rule moves off may_ship onto may_build_own_spec, so a granted profile lands its spec in specs_dir ready to build REGARDLESS of may_ship with the PR as the review point, while an ungranted profile keeps the previous hand-it-over behaviour verbatim. Deliberate deviation from the spec: the granted branch fires on may_build_own_spec true OR may_ship true — re-gating on the new key alone would have regressed M's own flow, because his overlay predates the key and would have fallen through to the committed false, telling the maintainer to hand his own specs over. Explicitly NOT changed: 'Routing work out' (contributor packets + the cr1 BACKLOG.md) stays gated on may_ship because routing work OUT to other people is genuinely a ship-operator function and a contractor does not route work to themselves; the three may_ship references in references/spec-templates.md; the Writer contract's ship/promote line; cr-test's tier-5 may_ship (a different concept); allowed_targets, which stays ['synthetic'] — this grants build authority, not real-workspace access; may_promote. The triage-intake frontmatter description is byte-identical, so zero trigger changes and no G11 budget impact — body text only. Guard 2 pins may_build_own_spec == TRUE, which runs the opposite direction from its two neighbours on purpose: it is not a safety fence but a do-not-silently-take-it-away fence, because a revert to false sends every contractor back to the pre-build handoff with no error and no clue why. The real safety fences (may_ship, may_promote, allowed_targets, workspace_root, scrub_roster) still pin the locked values and are untouched. Mutation-verified both ways against the shipped value (reverted to false: 1 failed / 49 passed; assertion then removed with the bad value still in place: 49 passed, proving only the fence caught it). Guard 3 gains three instruction-layer fences on the new delivery rule, which can fail in BOTH directions — narrowed back to may_ship (the handoff silently returns) or widened to no gate (every profile self-approves its own specs); mutation-verified 3 red on drift-back, 1 red on a deleted false-branch, 1 red on a deleted does-not-grant-ship-authority sentence, and green once the fences themselves are removed. Battery 50 passed / 9 skipped. README gains a plain-English What-you-can-and-cannot-do table covering all four authority keys and what each ships as, and setup step 3 now says explicitly that there is nothing to create or turn on — under the spec original overlay-only design nothing would have told Eric the key existed, since the docs said only M keeps an overlay. CLAUDE.md carries a three-row authority table and the honest note that these keys are a coordination contract, not a security boundary — the boundary is GitHub access (read-only on cr1, fork to PR, M merges). Accepted tradeoff: Eric now rules his own §0 AWAIT rows, so a rejected APPROACH at PR time wastes the whole build; the agreed middle ground is a one-line heads-up on architecture-shaping calls, no gate. Same-class sweep: nine SKILL.md files carried the parenthetical only-M-has-one claim about config/operator.local.json, false the moment a contractor keeps an overlay; swept to not-every-operator-has-one across bug-regression-suite, capture-for-code, cr-skill-builder, cr-test, cross-skill-interaction-test, scale-stress-test, ship-readiness-gate, smoke-watch and triage-intake. Deliberately excluded and verified unchanged: operator.json _comment_chalette_clone (that one is about a chalette030 clone and is still true) and this description field (a historical chain — history is not rewritten to match the present). Zero trigger changes proven not asserted: all nine frontmatter descriptions compared byte-for-byte against HEAD, 9 same / 0 changed. Skill count unchanged (15). PRIOR HISTORY: Chalette internal dev & QA toolkit for Command Room. v0.4.1 (2026-07-27) — VCRRETIRE: verify-cr-release retired; tier 5 becomes the dogfood ritual, walked by hand. M's ruling (2026-07-25): dogfood-before-promote plus BIG-TEST carry the attended layer, so the paste-back orchestrator's state tracking, prompt-rotation templates, phase-decision gates, and verdict-doc generation are ceremony no longer run. What the skill OWNED was kept, not deleted — three reference docs moved to their real owners with git mv so history follows the file: VERIFICATION_PLAN.md to cr-test/references/ (cr-test owns tier 5, and the plan was always a repo-level asset — line 3 always said 'the plan Eric maintains'), response-classifier.md and findings-log-format.md to bug-regression-suite/references/ (that skill fires prompts and classifies responses — step 3 of its own procedure). Both relocated shared docs gained a 'shared asset — sweep the citers before moving' header so the next retirement does not re-orphan them. Tier 5 is now stated as explicitly TWO halves, and cr-test refuses to call it covered on dogfood alone: freeform dogfood runs on a mature real workspace and therefore CANNOT reach virgin-workspace onboarding, honest empty states, the Phase-3 destructive probes, late-fire behavior, or the fresh-runtime loader canary — only the structured plan against a fresh, empty workspace does. CLAUDE.md and README.md grew a Track C to match; the two-track framing had no slot for the plan. Orphaned triggers re-homed: 'verify cr release' / 'run verification suite' alias 'cr test --attended', 'pre-ship check' aliases 'cr test --ship' (no collision with ship-readiness-gate's own 'pre-promote check'); 'continue verification' / 'resume verification' are deliberately DROPPED — they resumed a stateful session that no longer exists, and re-homing them would promise a resumption nothing provides. The two DOES-NOT-FIRE fences that pointed at the dead skill now name where the phrases actually go; left as-was they would have told those skills not to fire on phrases NO skill owned. ship-readiness-gate's ~80/20 coverage claim was CORRECTED rather than quietly dropped: the 20% is still addressable at the same attended tier but is no longer enforced — nothing tracks position through the plan, auto-classifies responses, or emits a verdict artifact — so the gate now carries two consequences: never infer the attended tier from a PROMOTE, and make the operator state what was actually walked ('attended: dogfood only, plan not walked' is a legitimate verdict-doc line). Silence is not coverage. Skill count 16 -> 15. PRIOR HISTORY: Chalette internal dev & QA toolkit for Command Room. v0.4.0 (2026-07-24) — TI2: triage-intake gains a route-work-out mode. On a may_ship operator profile ONLY, an item whose triage verdict is SPEC and which passes the five-clause contributor-suitability test (target repo is cr1; fully specifiable from repo contents; buildable and testable against the battery + synthetic fixtures alone; zero client/org/person names needed anywhere including PR text; zero ship authority) now yields two additional outputs: a self-contained packet at <specs_dir>/packets/PACKET_<TAG>.md that a cold fork contributor can execute without the maintainer online (handoff header, a spec body shaped per cr1's checked-in templates/TEMPLATE_SPEC.md with §0 already ruled, kickoff prompt, acceptance incl. the scrub AC verbatim, and an explicit PR-description-requirements block carrying the TEMPLATE_BUILD_REPORT slots), and one scrubbed READY row staged onto a repo-root BACKLOG.md in the cr1 clone that the contributor can read from their fork. Both outbound surfaces pass a FAIL-CLOSED scrub gate first: the new scrub_roster operator key (committed default null, real value overlay-only) is grepped against the full outbound text, and a null/unreadable roster REFUSES both writes with an explicit reason line rather than emitting unscrubbed text — the org-name-leak class cannot ride cr1's G9 alone, whose first-name dictionary cannot know real ORG names. BACKLOG writes are STAGE-AND-SHOW: git add + show the staged diff in the closing decision table, then stop — a triage session ends with zero new commits in the cr1 clone, and the maintainer pushes in his own ship window. The closing decision table gains an Eric? column. Zero trigger changes: the frontmatter description is byte-identical to v0.3.1, both features are inert behind the may_ship gate on a contractor profile, and INTAKE1 F1/F5 are untouched. Skill count unchanged (16). PRIOR HISTORY: Chalette internal dev & QA toolkit for Command Room. v0.3.1 (2026-07-24) — MAINT2: maintenance batch. (1) FIX: the operator-profile resolution pattern no longer silently no-ops under Git Bash on Windows (SHIP_RECORD_CONSOL2 finding 3, pattern-wide across all 11 reading skills). The bash blocks built the plugin root from ${BASH_SOURCE[0]} — empty when an agent runs a SKILL.md block through a Bash tool — and from pwd, which yields an MSYS path (/c/Users/...) that native python.exe resolves to C:\c\Users\..., so BOTH config reads missed, the merged profile came back empty, and every skill fell through to its synthetic default with no error: an operator granted allowed_targets [real] silently ran synthetic. The canonical preamble now searches for config/operator.json (with a $CHALETTE_DEV_ROOT escape hatch, never a hardcoded machine path), converts with cygpath -m, and FAILS LOUD on an unreadable root or profile; the python-form skills carry the same loud fence plus the native-path contract for SKILL_PLUGIN_ROOT. Guard 2 gains Fence 4 (+29 tests, 24 -> 53; 51 after the two retirements drop their quick_validate cases): the shipped preamble is EXECUTED out of each SKILL.md and asserted to read a non-empty profile, mutation-verified both ways. (2) RETIRED compare-canonical-vs-freelance — its niche (validating the v3.13.8 §3.6 canonical-vs-freelance widget ladder per skill) is closed; the freelance fallback it diffed against no longer exists, and synthetic invariant I2 (no_freelance_render) asserts the property the diff was inferring; ship-readiness-gate's coverage claims were corrected rather than inherited (Bug #48 action-label drift is cr1's CanonicalActionError validator in the unit tier, not this gate). (3) FOLDED run-command-room-tests into cr-test — it never had a delegating caller, and its hardcoded five suites were long superseded by tests/run_all.py's call-time discovery; its trigger phrases ('internal: run plugin tests', 'run command room tests', 'command room health check', 'verify plugin code') are now aliases for 'cr test --quick' in cr-test's description. Skill count 18 -> 16. PRIOR HISTORY: Chalette internal dev & QA toolkit for Command Room. v0.3.0 (2026-07-24) — CONSOL1: chalette-dev becomes the SINGLE canonical home of the shared QA/dev toolkit; the duplicate copies were removed from the private chalette plugin (which drifted). The 18 skills were reconciled to their canonical, operator-fenced form (newest-wins WITH fence preservation): operator profile gains chalette_clone / specs_dir / parking_doc keys plus a gitignored config/operator.local.json overlay — M's real-workspace profile lives ONLY in that overlay; the committed operator.json stays the contractor-safe default. ship-readiness-gate rebuilt on the operator pattern (default synthetic; real only when allowed_targets grants it); synthetic-workspace-runtime-test re-adds the event_gate_routed invariant (D6); triage-intake carries INTAKE1 F5 (resurrection guard, ported from chalette030) + F4 (chalette_clone, operator-aware) + specs_dir/parking_doc/may_ship-gated delivery; capture-for-code scopes its placeholder-names rule to non-real operators (F7); all real-path and M-identity leaks fenced. Two structural guards: scripts/check_toolkit_overlap.py (Guard 1 — fails if the toolkit re-duplicates into chalette) and tests/test_operator_fences.py (Guard 2 — fails if the committed operator.json drifts from contractor-safe, or if operator.local.json is tracked), both run in .github/workflows/toolkit-guard.yml (overlap check token-gated so forks stay green). quick_validate hygiene: template_version key removed from regenerate-skill / skill-generator / voice-test; regenerate-skill + skill-generator descriptions shrunk to the <=980 doctrine. Skill count unchanged (18). PRIOR HISTORY: Chalette internal dev & QA toolkit for Command Room. v0.2.1 (2026-07-24): FASTFOLLOW1 — post-review fixes. Intake pair (INTAKE1): capture-for-code duplicate-append is now restricted to matches in new/ (a match in needs-input/ or speced/ gets a fresh pointer file in new/ instead, preserving the single-writer rule), specs/ added to the first-capture folder bootstrap, and the confirm-line example points at the real ~/cr-intake/new/ queue root. cr-skill-builder v3 text fixes (SB1, kept byte-synced with chalette030): Gate-3 event-write wording corrected (a direct atomic_append_jsonl on the events path is gated, not banned), stale 'Gate 17' runtime-exercise heading corrected to Gate 13, the python-eaten-escapes gotcha tagged '(instruction-layer)', and stale Desktop/Claude output/workspace paths repointed to Penelopes Brain. skill-creator '20-gate' reference swept to '27-gate' to match chalette030. Removed bug-regression-suite/references/cr-investigation-2026-05-30/ + discovery-log-2026-05-29.md (real-name audit residue; deletion-forward, git-history purge pending M ruling). Skill count unchanged (18). v0.2.0 (2026-07-23): +2 skills — the intake pair: capture-for-code (one-minute structured capture of a bug/idea/skill-want into a local Maildir-style queue at operator.json intake_root, default ~/cr-intake; folder=status, single-writer, hypotheses always UNVERIFIED-labeled, placeholder names only) + triage-intake (verify each capture against the cr1 clone — graduated L1 read-trace / L2 test slice / L3 synthetic-fixture repro, same-class sweep, verdicts CONFIRMED / COULD-NOT-REPRODUCE / NOT-A-BUG — then emit a sized build spec, bug ≤1pg or feature ≤3pg with §0 recommended-default decisions, delivered to M via PR; contractors never self-approve specs into builds, synthetic targets only per allowed_targets). operator.json gains intake_root. Skill count 16→18. v0.1.3 (2026-07-15): bug-regression-suite catalog +1 entry — Bug #105 (_pid_alive fired a real Ctrl+C on Windows; os.kill(pid,0) == CTRL_C_EVENT, blocked the Windows battery outright and defeated multi_write_context mutual exclusion under Cowork's no-console path; cr1 ae399e8 / PR #30). First code-level catalog entry: the battery is the repro, not a prompt fire. NOTE: this diverges the catalog from the private chalette plugin (v0.8.10) until M mirrors it — the byte-identical invariant is intentionally broken here and needs a sync. v0.1.2 (2026-07-14): bug-regression-suite catalog +3 integration-2026-07 entries (F-15 widget-transport instruction gap, F-08 no-email inference ban, F-12 apply-choices non-Gmail substrate writes), Bug #104 update (delegation confirmed live; EW2+T pass criteria), instruction-layer Methodology note — catalog stays byte-identical with the private chalette plugin (v0.8.10). 16 skills extracted from the private chalette plugin (v0.8.8, 2026-07-13): release verification (verify-cr-release, ship-readiness-gate, synthetic-workspace-runtime-test, compare-canonical-vs-freelance), test batteries (cr-test, run-command-room-tests, bug-regression-suite, cross-skill-interaction-test, scale-stress-test, smoke-watch), skill building (cr-skill-builder, skill-creator, skill-generator, regenerate-skill, voice-test), and preview-command-room-widget. Operator-aware: reads config/operator.json for identity, paths, and permitted test targets — non-M operators always test against synthetic fixtures, never a real workspace. Shipping/promote (ship-cr-plugin) deliberately NOT included — releases stay with M.
