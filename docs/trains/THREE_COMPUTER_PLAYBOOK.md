# How the three computers work together

Base rules for building Command Room 1 (cr1). Ruled by Matthew on 2026-11-11, after the Nov 11 call with Ana, and moved here from the owner's workspace the same week. This is the train playbook: every coordinator and builder chat reads this copy from git. It replaces [TWO_MACHINE_PLAYBOOK.md](TWO_MACHINE_PLAYBOOK.md) (2026-10-28), which is kept for history. The chat prompts are in [CHAT_PROMPTS.md](CHAT_PROMPTS.md); the merge scripts are beside this file.

Records on cr1: the control issue is cr1#1051, the merge-gate ruling is cr1#1041, and the parent programme is cr1#1009. A change to these rules is Matthew's call; it lands here by pull request and is noted on cr1#1051.

## The idea in one paragraph

Each computer has one job. The Mac is the checker: it does everything GitHub's checks used to do, and it never builds. The office PC is the desk: one chat hands out work and merges finished work, and a second chat builds. The home PC only builds. All work goes through one list on GitHub, so any chat can see what is happening, and no work is lost if a computer turns off. Ana owns the checker. Matthew owns the work list and the rulings.

## Settled on the Nov 11 call with Ana

These are decided. The rules below follow them.

- **The Mac replaces GitHub's checks entirely**, including the ones that used to run on Windows. Nobody builds on the Mac. Matthew confirmed both, and Ana agreed.
- **The PCs keep running their own tests before every pull request.** Ana's reasons: it is faster, and it doesn't overload the Mac. The Mac then checks on top of that, the way GitHub did.
- **When the tests run:**
  - The quick check runs on every pull request and blocks the merge.
  - The full battery runs once every 5 merges. A red result stops merging, and a fix starts automatically.
  - The full battery runs before every promote to Command Room Internal, with a quick or force override for Matthew.
  - Promotes from Internal to clients go out with no further battery.
- **Retired:** the nightly battery, the sandbox VM check, and the list of risky files. In place of the list, failures from the every-5 battery are logged by area, so a targeted check can be rebuilt later.
- **When main goes red between the every-5 runs:** file an issue and a fix, and keep merging work that doesn't touch the broken area. This was Ana's pick (option 4).
- **Reruns and reviews:** a red result is re-run once before it counts. Stacked lanes are kept for dependent work. A fresh reviewer looks at every pull request, once.
- **Ana owns the battery, the quick check and the dev skills.** She can change them without waiting for approval, and she checks with Matthew only where his call is needed.
- **Still open with Ana:**
  - How to run several test runs on the Mac at once. Today the battery allows only one at a time, and the Mac has 16 GB.
  - Moving every machine to one Python version.
  - Whether cr1 goes back under the ChaletteHQ organisation, so access to it can be controlled. Ana: sensible, not urgent.

## The merge gates (cr1#1041, ruled 2026-11-11)

These replace train gates 1, 2, 3 and 5 of the 2026-11-09 ruling and the 2026-11-03 "merge on CI, the nightly is the battery" ruling. Where `cr1-build`, `ISSUES.md` or `DEVELOPMENT.md` in cr1 still says otherwise, this list wins until cr1#1041 lands there.

1. **CI runs on the Mac.** The two Mac runners (`cr1-mac` for tests, `cr1-mac-light` for the small API-only workflows) run the quick check, the full battery and the small workflows. No job is left on GitHub's hosted runners. Builders still run their own tests on the PCs.
2. **Full battery once every 5 merges to main,** not per pull request. A new red, after one re-run of the failing suite, stops merging, an issue is filed and a fix build starts at once, ahead of everything else. A red already known at the previous run does not stop merging.
3. **No path list.** `needs_full_battery.py` retires. Every failure in an every-5 run is logged as a comment on cr1#1041: date, commit range, suite, culprit pull request, files touched, area, kind (time limit, pin or golden, real bug). The list or a per-area check gets rebuilt from that log later.
4. **Promote:** a full battery by default. Two overrides, each with a reason that goes in the changelog: `--quick "<reason>"` and `--force "<reason>"` (no battery). The office PC's full battery is the Windows check before each release to Command Room Internal.
5. **Red main between every-5 runs does not stop everything.** It files an issue, and pull requests that do not touch the broken area keep merging. Revert-first is retired.
6. **Stacked lanes** stay allowed for dependent work.
7. **One review round.** A fresh reviewer on every pull request, once. Second-round findings go to a follow-up issue and do not hold the merge.
8. **A suite that times out is re-run once** before it counts as red. This one stays from the 2026-11-09 ruling.

Also retired on 2026-11-11 (cr1#433): the nightly battery and the sandbox-VM job.

**Not built yet** (open on cr1#1041, Ana's to design): the automatic every-5 trigger, the automatic fix start, the log format, and what counts as "the broken area". Until then the coordinator does all four by hand: it counts merges, starts the battery on the Mac (`gh workflow run battery.yml --ref main`) when no pull request is waiting for its quick check, and judges the area from the failing suite and the culprit's files.

**Check names.** The required checks are renamed from `windows` to `mac` by cr1#1114. Until main's branch protection lists the `mac` names and that pull request merges, the old names are the ones that gate.

## Who does what

| Computer | Its job | Chats open on it |
|---|---|---|
| **Mac mini** (office) | The checker. Tests every pull request, runs the full battery on main after every 5 merges, and runs the battery before each promote. Never builds, never merges. Looked after by Ana. | None day to day. The test runners work in the background. |
| **Office PC** (32 GB Dell) | Builds. Can also host the coordinator. | **office-1** and **office-2**, plus the **Coordinator** if you open it here |
| **Home PC** (gaming PC) | Builds. Can also host the coordinator. | **home-1** and **home-2**, plus the **Coordinator** if you open it here |

**The coordinator** is one chat that never builds. It keeps the work list, gives out jobs, checks finished work, merges, and writes your daily status. Exactly one runs at a time, on whichever PC you open it.

**Why the coordinator gets its own chat.** A chat in the middle of a build can't answer anyone until that step finishes, and a build fills its memory fast. A coordinator that only coordinates stays quick and remembers the whole night. If a builder chat crashes, coordination carries on.

**Which PC coordinates: either (Matthew, Nov 11).** The location barely matters. The coordinator talks to GitHub, not to the other computers, so it works the same from either PC. Two things matter:

- **Exactly one coordinator at a time.** A second one opened by mistake sees the first one's lease and waits for Matthew to say which stays.
- **Pick the PC most likely to stay on.** The home PC dropped out twice recently (train 5 at 01:30, and during the Nov 11 call), so the office PC is the safer default until that is fixed.

If the coordinator's PC goes quiet for 2 hours, the -1 builder on the other PC covers until it is back.

## The ten rules

1. **One work list.** Every job lives on one cr1 issue, #1051 ("Builder control room"), as a list in priority order. To add, remove or reorder work, tell the coordinator chat, or edit the list yourself. Nothing gets built that isn't on the list.
2. **Claim before building.** A builder posts a claim on the control issue before it starts. Two builders never work on the same job, or on jobs that change the same files. The coordinator keeps dependent jobs in order.
3. **Builders test, then hand off.** A builder runs the quick tests on its own PC, which is now the only Windows check, and gets one review from a fresh reviewer. Then it opens the pull request, posts it on the control issue and messages the coordinator. Builders never merge.
4. **Only the coordinator merges,** one pull request at a time, once the Mac's quick check is green and the review is done. A second round of review findings becomes a new issue and does not hold the merge.
5. **The Mac checks main every 5 merges.** If that run is red, merging stops, and the coordinator starts the fix itself. If main goes red between runs, the coordinator files an issue and keeps merging work outside the broken area. **Until Ana can run several tests on the Mac at once**, the every-5 run makes pull request checks wait behind it for about an hour. The coordinator starts it when no pull request is waiting.
6. **Rulings are yours and are never guessed.** When a job needs your decision, the question goes on that job's issue, and the builder moves to the next job. The coordinator lists every waiting question in your daily status.
7. **One daily status for you.** Each morning, the coordinator posts on the control issue: what merged, what is open, what is stuck, and what needs you. It is written to be read on a phone.
8. **When a computer goes quiet:**
   - **Mac off.** Nothing merges. Builders keep building, and pull requests wait. The coordinator tells you and Ana.
   - **The coordinator's PC off.** The builders on the other PC keep building. After 2 hours of silence, that PC's -1 builder covers as coordinator until the first one is back. A power or internet cut at the office takes out the Mac too, so in that case nothing merges until the office is back.
   - **A builder's PC off.** Its claimed jobs are freed after 6 hours, and the other PC's builders pick them up. The coordinator tells you which chats to reopen.
9. **Who decides what.**
   - **Only Matthew:** rulings, the tests a person has to run (UAT), any promote, changes to these rules, and adding or removing a computer or chat.
   - **Ana:** anything about the Mac, the battery, the quick check or the dev skills. The coordinator never changes those; it sends them to her.
10. **No client information on GitHub, ever.** Every comment, pull request and commit is scrubbed first. Sample names only.

**How many builders.** Four: two on each PC, all building at the same time. Usage is not a limit (Matthew, Nov 11). What limits it now is the work itself:

- **Each PC can run only one test at a time.** A builder spends most of its time writing code and only about 5 minutes testing, so two builders per PC rarely wait on each other. A third would wait more often.
- **The merge desk takes one pull request at a time.**
- **The Mac checks one pull request at a time** until Ana sets it up to run several side by side.
- **Jobs that change the same files can't run in parallel,** and on Nov 11 several trains were held for that reason.

So past four builders, extra chats mostly queue. Add a fifth only if the coordinator's status keeps showing more ready jobs than free builders.

**Why the Mac doesn't build too.** It is the computer everyone else waits on. Every build on it would slow the checks for all four builders, and this was settled with Ana.

**Starting the chats (Matthew, Nov 11).** For now, Matthew opens every chat by hand, at the computer or from his phone through Remote Control. Every builder keeps one status line on the control issue, updated every 30 minutes. When a builder's line goes stale for 2 hours, the coordinator tells Matthew which chat to reopen and on which PC. It does the same when more ready jobs are waiting than there are free builders. Inside each builder chat, every job goes to a fresh helper, so a long-running chat never builds on a full memory.

**Later, once Tailscale is set up:** with Tailscale and SSH on all three computers, the coordinator could restart builders itself. One test decides whether it can also open builder chats on the home PC that you can see in the app. Until that test passes, chats are opened by hand.

Chats don't stop on their own. When there is no work, they check again every 30 minutes, so they are ready the moment you add a job.

## Keeping the computers on and reachable

| | Mac mini | Office PC | Home PC |
|---|---|---|---|
| Never sleep when plugged in | Yes | Yes | Yes |
| Turn back on after a power cut | Yes (on and signed in, Matthew, Nov 11) | If the PC's settings allow it | If the PC's settings allow it |
| Claude app opens at sign-in, keep-awake and Remote Control on | Only if a Mac chat is wanted | Yes | Yes |
| Test runners restart by themselves | Yes, set up by Ana | No runner | Its runner retires once the Mac's checks are live |
| After a Windows update restart | n/a | Windows signs back in by itself, then locks | Same |
| Tailscale, on a work account | Already installed | Add | Add |
| Python for cr1 work | 3.12 | 3.12 | 3.12 (this PC defaults to 3.14, so builders call 3.12 directly) |

**Signing back in after updates.** Windows 11 has a setting that signs you back in after an update restart and then locks the screen: Settings, Accounts, Sign-in options, "Use my sign-in info to automatically finish setting up after an update". It closes the gap that took the home PC out on train 5, without leaving either PC open to anyone who walks up. Check it is on, on both PCs. Then set Windows Update's active hours to cover the night as well.

**Tailscale** lets you, and Ana in a terminal only, reach each computer from anywhere, including your phone. Ana recommended a work account rather than your personal email, so that access never touches your personal data.

## Getting there, in order

1. **Ana finishes the Mac as the checker:**
   - Merge cr1 PR #1038.
   - Point main's required checks at the Mac.
   - Make the runners restart by themselves.
   - Turn off sleep and turn on restart after a power cut.
2. **Retire the `home-pc` runner** once the Mac's checks have worked for a day.
3. **Put Tailscale on both PCs and your phone,** under the work account.
4. **Check the update sign-in setting and active hours** on both PCs.
5. **Done 2026-11-11:** the control issue is cr1#1051, with the starting work list.
6. **Open the chats by hand.** The coordinator first, on either PC (office is the safer default), then the two office builders (office-1 and office-2), then the two home builders (home-1 and home-2). Each starts from the prompts in `Chalette_CR1_Builder_Prompt_2026-11-11.md`. Reopen any chat the coordinator reports as missing.
7. **Add a stall alarm:** a small Mac job that raises the alarm if the coordinator has been silent for an hour. The Oct 28 playbook asked for this and it was never built. It is Ana's call, because it runs on the Mac.
8. **Done:** these rules are in chalette-dev (`docs/trains/`), so every computer reads the same copy from git.
9. **Later, so the coordinator can open chats itself:**
   - Put Tailscale on all three computers, under a work account, and let only the office PC reach the other two.
   - Turn on SSH: Remote Login on the Mac, OpenSSH Server on the home PC.
   - Save "home" and "mac" as SSH connections in the Claude app on the office PC.
   - Test once whether the app can open a builder chat on the home PC. If it can, the coordinator opens and restarts builders itself.

## The five decisions (all answered, Nov 11)

1. **Which PC coordinates:** either, one at a time. Office is the safer default while the home PC keeps dropping out.
2. **The coordinator merges without asking,** on a green Mac check plus the review.
3. **Staying signed in:** the Mac is always on and signed in (done). On the PCs, Windows signs back in after updates and then locks. Matthew turns this on later; until then, an update restart stops that PC until someone signs in.
4. **Builders:** two on each PC, all at once. Usage is not a limit.
5. **Windows checks:** the Mac takes every check, and the PCs' own tests are the Windows check (settled with Ana).

## The merge scripts

`merge_pr.sh` and `wait_merge.sh` sit beside this file and are the coordinator's tools. How they work is in the "merge scripts" section of [TWO_MACHINE_PLAYBOOK.md](TWO_MACHINE_PLAYBOOK.md), with one change for gate 5: when main's newest run is red, `merge_pr.sh` stops and asks for an issue. If the pull request is outside the broken area, the coordinator re-runs it with `MAIN_RED_OK=1`.
