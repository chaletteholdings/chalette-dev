---
name: "cr1-test"
description: "Use when Matthew, Erick or Isabella wants to test a Command Room 1 fix that is waiting on a test: 'what needs me', 'what do I need to test', 'test #N', 'verify the fix', 'UAT'. Gives a short script of what to type and what to look for, then records pass, flaky or fail on the GitHub issue in chaletteholdings/cr1. Also Matthew's sign-off on a team member's pass: 'what needs my sign-off', 'check the pass on #N', 'close all that hold'. Also 'backlog review': lists backlog tickets over 30 days old to close in one word. Does NOT fire on 'report this' (cr1-report) or 'what's pending to build' (cr1-desk)."
---

# cr1 test

A fix is built with cr1-build, checked by a fresh reviewer, and merged by Matthew. Then, for a `critical` fix only, a person confirms it in the real product: Matthew, or a team member (Erick, Isabella) whose pass Claude checks and Matthew signs off before it closes (section 6). Every other merged fix is tested by use and closed by its builder on merge (owner ruling, 2026-11-06); a problem found in use is filed with "report this". This skill makes the confirming fast: it tells the tester where to go, what to type and what a pass looks like, then writes the result back in the repo's fixed shape. A failed test gets the same complete write-up as a bug filed with cr1-report, so whoever builds the next attempt never has to ask what happened. Rules: sections 7 and 12 of `ISSUES.md` at the root of `chaletteholdings/cr1`.

## Who is running this

These skills are shared by the team (the chalette-dev plugin). Work out who is running them in this order and stop at the first answer:

1. **The local profile.** `config/operator.local.json` in this plugin, when present: its `operator` wins (`"m"` is Matthew). Only Matthew keeps one, on his own computer.
2. **The GitHub account.** Run `gh api user --jq .login`. `chaletteholdings` is Matthew; `erick559` is Erick; any other account is another team member, who gets Erick's steps under their own name. Web and phone chats load a fresh copy of the plugin with no local profile, so this is how they know who is there.
3. **The shared default.** `operator` in `config/operator.json` (Erick).

Say who in one line in the first reply ("Running as Matthew, from the GitHub account."), so a wrong guess shows at once. If the person says otherwise, their word stands for the rest of the chat. If none of the three can be read, never assume: say `FATAL: operator profile unreadable` in one line, then ask once, "Matthew, Erick, or someone else on the team?", and go on with the answer.

- **Matthew (`m`):** everything below as written. He confirms what gets filed, decides what is ready to build, merges, and closes an issue on a passing test.
- **Erick, or any other team member:** the same steps, with Matthew's decisions turned into proposals. File it with the label `question` and the line "Proposed by <their name>, Matthew to confirm." (<their name> comes from `gh api user --jq '.name // .login'`.) Never close an issue: post the test result and tag Matthew. Never post a build brief as decided; post it as "Proposed by <their name>, Matthew to confirm."
- Where the text says "Matthew" as the person you are talking to, talk to whoever is running it. Where it cites a ruling ("Matthew, 2026-10-04"), the ruling stands for everyone.

## 1. "What needs me" (the queue)

List open issues waiting on a person's test. A test is owed only on a `critical` fix (owner ruling, 2026-11-06; the label is set by cr1-report at filing, and the issue's first line names the test it met):
- labels `critical` and `needs UAT` together: `gh api "repos/chaletteholdings/cr1/issues?state=open&labels=critical,needs%20UAT&per_page=100"`
- plus any open `critical` issue whose latest fix comment starts **Please verify the fix** and has no later UAT result. Read comments with `gh api repos/chaletteholdings/cr1/issues/N/comments`.

An open issue that carries `needs UAT` without `critical` is not in the queue and is not owed a test. Do not list it as work. Count those in one closing line, "<n> merged fixes carry needs UAT without critical; say *sort them*", and on "sort them" read each against the four tests in cr1-report section 1a: one that meets a test gets `critical` and its Critical line in a comment and joins the queue; the rest close on the builder's verification with the comment "Closed on merge: not critical (ISSUES.md section 7, owner ruling 2026-11-06). Refile from use with *report this* if it comes back." and `needs UAT` removed. Matthew closes; a team member proposes the sort in a comment and tags him.

Before listing an issue, read its later comments. If an automated validation (Erick's sessions post "Confirmed on <version>" comments) already shows the fix **failing** on that version or a later one, don't spend Matthew's time on it. Mark it "already failing per #N comment, back to build", and offer to remove `needs UAT` with a one-line comment pointing at that evidence.

Show the queue oldest first, one line each: `#N title · fixed in <version or commit> · ~<minutes> · <test folder / real folder / any chat>`. Ask which to run, or start the top one if Matthew says "go".

- **For Matthew,** open with the sign-off count when there is one: "<n> passes waiting for your sign-off, oldest <n> days: say *what needs my sign-off*." Clearing those is the fastest way to move the board. Mark an issue a team member has claimed `(being tested by <name>)`, so he does not test it twice.
- **For a team member,** leave out any issue assigned to someone else (they are testing it) and any test that only Matthew's real folder can show (list those last as "Matthew only", one line, not runnable here).

## 2. Prepare one test

1. Read the issue body, its acceptance check, and the fix comment (version or commit, what changed, what it asks to check). **A team member claims it first:** assign the issue to them, `gh api -X POST repos/chaletteholdings/cr1/issues/N/assignees -f "assignees[]=<their login>"`, so nobody else tests it at the same time. If they stop without a result, release it: the same call with `-X DELETE`.
2. **Version gate: the fix must be in what is installed.** First find the fix's merge: the pull request that references the issue, and its merge commit (`gh api repos/chaletteholdings/cr1/pulls/<PR> -q .merge_commit_sha`). Then find the installed plugin: the `plugin.json` whose `"name"` is `command-room` under `~/.claude/plugins`, `/root/.claude/plugins` or `/mnt/skills/plugins`. There are two kinds:
   - **The staging plugin `cr`** (from the `commandroom1` marketplace, added as `chaletteholdings/cr1`; it sits under a `commandroom1` folder). Matthew and the team test on it. It follows `main` by commit, so its installed commit must be at or after the fix's merge. Read the commit from the `cr@commandroom1` entry (`gitCommitSha`) in `installed_plugins.json` beside the plugins folder, then run `gh api repos/chaletteholdings/cr1/compare/<merge commit>...<installed commit> -q .status`. `ahead` or `identical` means the fix is in; `behind` or `diverged` means it is not.
   - **The `command-room` plugin clients and Matthew run.** It gets changes only when Matthew promotes a release, so the fix is in only if a released version at or below the installed one contains it. Search the CHANGELOG on `main` for the issue number: `gh api repos/chaletteholdings/cr1/contents/command-room/CHANGELOG.md -H "Accept: application/vnd.github.raw" | grep -n "cr1/issues/N)"` (each entry links its issue that way) and read which version's section it sits under. If no release lists it, it cannot be tested on `command-room` yet: test on `cr`, or wait for the release.
   If the fix is not in, stop. Tell Matthew to update the plugin in the Claude app and start a fresh chat, then check again. Note the version (or the `cr` commit) and the `main` commit; a fail report needs both.
3. **Pick the folder.** **A team member always tests in their own real folder** (owner ruling, 2026-11-01, extending cr1#448): real meetings, mail and records are what the fix has to work on, and a test copy hides the bugs that only real data shows. Never a client's folder, never a sample brain. Before any step that converts, moves, deletes or rewrites files, resets settings, or runs Maintenance, have them back up what that step touches (copy the files or the folder aside) and say how to put it back; test entries a step adds (a sample decision, objective or note) are named as samples and removed after the run. A test that only Matthew's real folder can show is his: say so and stop.
   **For Matthew,** use a test folder (a synthetic or copied test brain) for anything that converts, moves, deletes or rewrites files, or that runs Maintenance against a book, and the real folder when the bug can only show there; never run a destructive step on his real folder without his explicit yes in this chat.
4. **Decide where it runs.** Most tests run in a **new chat** (the product's real path), not in this one, because this chat now carries extra skills and context. Script-level checks (a command, a file's contents) can run here; say which.

## 3. Give Matthew the script

Keep it to what he does and what he looks at. Shape:

```
Test #N on <version> · about <n> minutes
What was fixed: <one plain line>
Setup: <new chat / your own folder attached / nothing> · Back up first: <what, or none>

Step 1. The original failure, 3 runs
Given: <setup in plain words: a fresh chat, your own folder attached>
When you type:
    <exact text, in a code block so it copies cleanly>
Then: <what the answer should do, in business words>
Pass if: <X is there> and <Y is not>   (yes or no, never a score)
Evidence: paste <the line> / screenshot <the widget>
Do it 3 times, each in a new chat. Tell me how many of 3 passed.

Step 2. A nearby case the fix comment named
...

Step 3. Nothing else broke
When you type: <a prompt from a related closed issue>
Pass if: it still works as it did.

Step 4. The wrong skill does not answer
When you type: <a near-miss phrase that belongs to a different skill>
Pass if: <that other skill answers, not this one>

After every run: the test log
Right after the test prompt's reply, paste this into the SAME test chat as its next message:
    <the test-log prompt below, verbatim>
Then copy both replies (the answer and the log) back into this chat.

When done, paste the answers and the logs here, and say "pass" or "fail" if you already know.
Only type the test prompts and the log prompt in a test chat: never "post it", "run maintenance" or "report this" unless a step says so.
```

**The test-log prompt.** Every script ends with it, in its own code block so it copies cleanly, every time, without being asked (Matthew, 2026-10-15). It is the only way to see what a test chat did behind its answer: which script ran, where, and what failed quietly. An earlier test on the retired product showed why: the answer was right in 3 of 3 runs while the fix's own path never ran, and only the run log gave it away.

```
For a test log, list exactly what you just did, in order: each skill you loaded, each script or command you ran (name and whether it ran in this chat or on my computer), each connector you called, every file you read or wrote or filed as a proposal (path only), any error or warning word for word, and whether anything was saved, queued for Maintenance, or not saved. Facts only, no summary of the findings, no client names.
```

If an earlier test chat is still open and its log was never taken, ask for it there before posting.

Rules for a good script:
- Every step has an exact thing to type or click and an observable result. Never "check that it works".
- Test the original failure first: the exact action from the issue's steps. Then one nearby case the fix comment named.
- **Run the original failure 3 times, each in a fresh chat.** Command Room is an AI product, so one good run proves little. 3 of 3 is a pass, 1 or 2 of 3 is **partial (flaky)**, 0 of 3 is a fail. For a step that changes files, put the backup back between runs, or run it once and say so in the result.
- Every check is a yes/no about the answer ("the brief names three meetings and no client names"), never a score. Name the evidence for each.
- Add one **regression** step (a related closed issue still works) and one **near-miss** step (a phrase that must go to a different skill). Fixes often break a neighbour.
- For a risky fix (conversion, Maintenance, anything that moves or deletes files), you may add one optional 5-minute look-around: "Explore <surface> in your folder to find anything wrong or missing." Anything found becomes a new issue through cr1-report, not part of this verdict.
- Every script ends with the test-log prompt, verbatim, for every run. It is never optional and never left for Matthew to ask for.
- Three to six steps. Over ten minutes, split it into two tests.
- If a step needs proof, name it ("paste the line that starts `Saved.`", or "screenshot the widget" for anything visual).
- Say what not to do when a wrong move would spoil the test ("don't say 'run maintenance' yet").

## 4. Record the result

**Evidence before verdict.** Before posting a pass, quote what was seen (the pasted line, or the screenshot's name) against each pass criterion. No evidence for a criterion means that criterion is not passed.

**Judge the path, not only the answer.** Read each run's test log against the fix comment: did the script or route it changed actually run? A right answer reached by a workaround (the model reading files by hand because the fix's own path failed) is **partial**, never a pass. Check the log's claims against the book's own records, where reachable. A run with no test log is posted as "no test log" in its row, never silently counted as a pass.

Scrub every result before posting with the **cr1-scrub** skill. Post with `gh api repos/chaletteholdings/cr1/issues/N/comments -F body=@<scratch>/uat.md`.

### Pass

```
**UAT pass** on <version or cr commit> (`<commit>`) · **3 of 3 runs**
Where: <new chat / this chat> · <desktop/web/phone> · <test folder / real folder, no names>
Model: <Opus / Sonnet / Haiku, as shown in the app> · Surface: <chat / Claude Code / scheduled task>
Steps: 1. ... 2. ...
Result: <for each pass criterion, what was seen>
Regression check: <pass / not run> · Near-miss check: <pass / not run>
Deviations from the script: <none / what was different>
Evidence:
<details><summary>Chat log</summary>

1. **Matthew:** "..."
2. **Claude:** ...
</details>
```

**Matthew's own pass:** Matthew closes on a pass (his ruling, 2026-10-04). Close it: `gh api -X PATCH repos/chaletteholdings/cr1/issues/N -f state=closed -f state_reason=completed`. Remove the label: `gh api -X DELETE "repos/chaletteholdings/cr1/issues/N/labels/needs%20UAT"`.

**A team member's pass:** never close. Put `Tested by <their name>` on the first line after the header, and end the comment with `@chaletteholdings ready for your sign-off.` Then swap the labels: remove `needs UAT` (the call above) and add `ready to close`, `gh api repos/chaletteholdings/cr1/issues/N/labels -f "labels[]=ready to close"`. The issue stays assigned to them, so the record shows who tested it. Matthew signs off in section 6 (his ruling, 2026-10-26, cr1#448).

### Fail or partial: a full report, every time

A failed or partial test is a bug report on the fix, so it carries everything cr1-report puts in a bug. Nothing is left for whoever builds the fix to ask.

**Get the evidence first.** The failure usually happened in the separate test chat, so ask Matthew for one of these:
- paste the reply he got (and any error) and that chat's test log here; build the chat log below from the test log;
- or say "report this" in the test chat. cr1-report finds this open issue and comments there with that chat's log. Then post only the UAT header and step results below, and link that comment.

For anything visual, give the exact error text and describe what the screen shows by its shape. A screenshot from a real folder is never attached (ISSUES.md section 0); only Matthew may add one taken on a test folder. Add `needs evidence` until the text or his screenshot is on the issue.

**Post this shape:**

```
**UAT fail** (or **UAT partial (flaky)**) on <installed version or cr commit> (`<main commit>`) · **<n> of 3 runs passed**

**What happened:** one line
**Impact:** who is affected and how badly
**Expected:** <from the acceptance check and the fix comment>
**Actual:** <what was seen; error text verbatim>
**Steps to reproduce** (exactly as run)
1. <setup: new chat, folder attached or connector, test or real folder>
2. typed: "<exact text>"
3. ...
**Step results:** step 1 pass · step 2 fail · step 3 not run (blocked by 2)
**Where:** command-room <installed version> or cr at <commit> (main is <version>) · chat or scheduled task · desktop, web or phone · folder attached or connector · test or real folder
**Model:** <as shown in the app> · **Deviations from the script:** <none / what>
**Reproduced?** yes, by Matthew on <version>, <n> of <n> tries
**Against the fix comment:** <which of the claimed changes held, which did not>
**Acceptance check:** <restated, unchanged unless Matthew changed it>

<details>
<summary>Chat log</summary>

1. **Matthew:** "exact words typed"
2. **Claude:** ran <skill or script or connector call>, read or wrote <file kind>, answered: "<short quote or summary>"
3. **Error:** `verbatim error text`
...
</details>

**Screenshot:** <attached / not needed (not visual) / needed: Matthew to add>
**Suspected cause (not verified):** only if there is a real clue; keep it apart from the facts
```

Chat log rules (the same as cr1-report): one line per turn, high level, what was typed verbatim, what Claude did, what it answered, errors verbatim. No internal reasoning, no long tool output, no file contents. About 5 to 20 lines.

Then leave the issue open and remove `needs UAT`: `gh api -X DELETE "repos/chaletteholdings/cr1/issues/N/labels/needs%20UAT"`.

### Other outcomes

- **Not tested, blocked by something specific** (wrong version, a broken prerequisite, no folder attached): post one line, "Not tested: <reason>", and add the `blocked` label, so the issue shows why it is stuck.
- **Not tested, no time:** say so in one line and post nothing. Silence never counts as a pass.
- **A new, different problem** found while testing gets its own issue through **cr1-report**, linked here, not a paragraph in this comment.

REST only (GraphQL is blocked). If `gh` can't reach the repo in a cloud session, attach it with the add_repo tool (`chaletteholdings`, `cr1`) and retry once.

## 5. Reply

One line per test: `#N pass, closed` (Matthew), `#N pass, waiting for Matthew's sign-off` (a team member) or `#N fail, full report posted, back to build`, plus the next item in the queue and its estimated minutes.

## 6. Matthew's sign-off on a team member's pass

Matthew only, and here a person's word is not enough. Before reading the queue or closing anything, check the account: `gh api user --jq .login` must be `chaletteholdings`, or a local profile (`config/operator.local.json`) must say `m`. Otherwise, even if the person says they are Matthew, answer one line, "Only Matthew signs off, from his own account; your pass is waiting for him.", and stop. Matthew is not technical, so he is not asked to read a test. Claude reads it for him, fresh, and he decides on one line per issue.

**The queue** ("what needs my sign-off"): `gh api "repos/chaletteholdings/cr1/issues?state=open&labels=ready%20to%20close&per_page=100"`, oldest pass first. "check the pass on #N" runs the same check on one issue.

**The check.** For each issue, read the issue, the fix comment and the latest **UAT pass** comment from GitHub, not from memory or the tester's summary. It **holds** only when all six are true:
1. **Right build.** The version or `cr` commit in the pass contains the fix's merge (the compare call in section 2, step 2).
2. **Three runs.** 3 of 3, each in a fresh chat.
3. **A log for every run,** and each log shows the fix's own path ran (section 4, "Judge the path").
4. **Evidence for every pass criterion:** a quoted line or a named screenshot against each one in the script or acceptance check.
5. **Neighbours checked.** The regression and near-miss steps passed, or the comment says why they were not run.
6. **Clean.** Scan the pass comment with cr1-scrub. A client, personal or money hit stops everything for that issue: tell Matthew, and do not edit or delete the comment (that is his decision). `ready to close` stays on until he decides.

**Show it** as one line each, what was fixed in plain words first:
`#N <what was fixed> · tested by <name> on <version> · holds` or `· does not hold: <the first failed check, in plain words>`. Mark any pass waiting more than three days `(waiting <n> days)` and put those on top.

**Close only on Matthew's word in this chat:** "close 152 and 153", "close all that hold", or a plain yes to the list just shown (it covers the ones marked holds, nothing else). For each:
- comment `**Signed off by Matthew** on <date>. Checked: right build, 3 of 3 runs with logs, evidence for every criterion, neighbours checked, scrub clean. Pass by <name>: <link to the pass comment>.`
- remove `ready to close`: `gh api -X DELETE "repos/chaletteholdings/cr1/issues/N/labels/ready%20to%20close"`
- close: `gh api -X PATCH repos/chaletteholdings/cr1/issues/N -f state=closed -f state_reason=completed`

**Does not hold.** Post `**Sign-off check: does not hold.** <the reason>.` and remove `ready to close`. Then:
- a gap in the test (wrong build, fewer than 3 runs, a missing log or missing evidence): add `needs UAT` back, unassign the tester, and tag them so they can rerun it;
- a failure the evidence shows: the fix goes back to build, as a fail does (section 4). Leave `needs UAT` off.

**Reply** one line per issue: `#N closed` or `#N back to <name> for a retest: <reason>` or `#N back to build: <reason>`.

## 7. Backlog review

Fires on "backlog review", "review the backlog", "what's in the backlog". A `backlog` ticket was filed on the owner's word although it met none of the four tests (cr1-report section 1a), so nobody tests it and nothing is scheduled for it. After 30 days without being refiled from use, it goes.

1. List them: `gh api "repos/chaletteholdings/cr1/issues?state=open&labels=backlog&per_page=100"`, keep those whose `created_at` is more than 30 days before today, oldest first. One line each: `#N <title> · filed <n> days ago · by <login>`. Count the younger ones in one line ("and <n> more under 30 days, not due"). An issue with both `backlog` and `critical` is a filing error: say so, and sort it with cr1-report section 1a before anything else.
2. Then one line: "Say *close them* to close all <n>, or *close N and M*." No explanations unless asked; "explain #N" gives the four lines from cr1-desk.
3. **Matthew's word closes.** On "close them" or a list of numbers, for each: comment `Closed at backlog review on <date>: over 30 days in backlog, not refiled from use. Say *report this* if it comes back.`, then `gh api -X PATCH repos/chaletteholdings/cr1/issues/N -f state=closed -f state_reason=not_planned`. Reply one line per issue, `#N closed`, and the count left in backlog.
4. **A team member** runs the same review but can never close: post the list as one comment on the oldest ticket, "Backlog review by <their name>: these are over 30 days. @chaletteholdings close or keep.", and reply with the count. Matthew closes from his own chat.
5. "Keep #N" leaves it open and adds nothing; the next review shows it again. A ticket Matthew wants built instead is re-judged with cr1-report section 1a and gets `critical` with its line, or stays `backlog` and is built on his word alone.
