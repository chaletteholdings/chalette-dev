# CR1 trains on two computers: playbook

Written 2026-10-28, from train 4 (the first train run on the PC and the Mac together). Read this before any train that uses both machines, and point the train brief at it.

## What train 4 showed

Two computers work. The Mac built 10 of the 20 fixes and runs the quick test battery about three times faster than the PC (96 s against 300 s for the same 709 suites). Most of the lost time came from setting the Mac up during the night instead of before it, and from problems that would have hit a one-machine train too.

## The day before (setup, not train time)

- [ ] **Set up and check the Mac in daylight.** On train 4, the setup check, the installs and pasting the brief across took about an hour of the night. The Mac uses `~/repos/.cr1venv` (Python 3.12 through uv), the terms list at `~/repos/.terms.txt`, and its own clone of cr1.
- [ ] **Fix cr1#524 first, or plan around it.** The privacy check that runs on every commit never runs on Mac or Linux (the hook file is not executable), so Mac builders have to scrub by hand.
- [ ] **Record a Mac test baseline on main at the start.** About fifteen suites fail only on the Mac (G44, docs1, doorjson1, scrub_hook, orch1, and some environment suites). Mac builds are compared against Mac main, never against the PC. The Windows CI shards stay the merge gate.
- [ ] **Put the Mac's brief in a shared file both machines read.** The PC session could not talk to the Mac chat directly, so every handoff went through Matthew. Save the brief somewhere the Mac can open (the workspace folder or the repo) and give the Mac one line: read that file.
- [ ] **Decide the branch-update method before the train starts.** See the next section.

## Who does what

| Machine | Job |
|---|---|
| Mac | All builds and their quick tests. It is faster, and builds are where the queue waits. |
| PC | The coordinator: merging one pull request at a time, the full batteries, and posting to GitHub. |

On train 4 it ran the other way for half the night. PC builders waited on the PC's single battery lock while the Mac was partly idle.

## Rules that held

- **Update branches by merging main into them, not by rebasing.** Auto mode started refusing force-push partway through train 4, on both machines, after it had worked earlier. The Mac's branches were stuck for hours. What worked: merge `origin/main` into the branch, push normally, re-test, then squash-merge, so main still gets one commit per pull request. Whether this becomes the standard, or force-push is allowed for train branches, is Matthew's call. Until he rules, use the merge method so the night does not depend on a permission that can change.
- **One merge loop, on one machine.** Two merge loops ran at once once on train 4. That breaks the one-at-a-time rule.
- **A failed check gets one automatic re-run before merging stops.** Flaky checks (cr1#542, cr1#548) stopped merging for four hours overnight because nobody was awake to press re-run. *Not yet in the scripts; add it before the next train.*
- **A cancelled main run is not a red one.** It was replaced by a newer push. The merge script skips cancelled runs.
- **Generated files count as overlap only when they actually collide.** That means the pull request touches a generated file, or main regenerated one and the pull request adds files. The generated files: `instruction_layer_names.py`, `ORCH_MIGRATION_CENSUS`, `MODULE_INDEX`, `SKILLS_INDEX`, `specs/INDEX`, `handoffs/INDEX`, `WORKSPACE_ACCESS.md`, `SCHEDULER_DISCOVERY.md`.
- **Never name a client contact in GitHub text.** On train 4 a comment named one. The auto-mode check caught it; the scrub did not, because first names outside the book are not on the terms list.

## Watching for a stall

The session restarted around 07:05 and nothing noticed until 09:25. The running log (`ledger.txt`) made catching up quick, but nothing raises an alarm when the coordinator stops. Before the next long train, add a check-in that looks at the log's last line and says so if it is more than about 30 minutes old. *Not built yet.*

## The merge scripts

Saved beside this file in `docs/trains/`:

- `merge_pr.sh <PR> <issue> [squash]` checks five things in order: three green quick-check shards on the pull request; the newest finished main run is green (cancelled runs skipped); the branch is on the tip of main or has no overlap; the scrub is clean on added lines and commit messages. If all pass, it squash-merges. It then posts the Please verify comment from `v/<issue>.md`, adds `needs UAT`, and writes a line to the log.
- `wait_merge.sh <PR> <issue>` waits for the shards, then calls `merge_pr.sh`.

Both need `TRAIN_DIR` set to the train's scratch folder. That folder holds `terms.txt`, the `v/` comment texts and `ledger.txt`. They expect the cr1 clone at `~/repos/cr1-canonical` and the scrub tool in the chalette-dev clone. They are Git Bash scripts written on the PC and have not been run from this copy yet.

## Still open from train 4

- Matthew's ruling on merge-update against force-push for train branches.
- cr1#524 (the Mac privacy check) and the Mac-only failing suites.
- The automatic re-run and the stall check above.
