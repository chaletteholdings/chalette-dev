---
name: "cr2-test"
description: "Use when Matthew or Erick wants to test a Command Room 2 fix that is waiting on them: 'what needs me', 'what do I need to test', 'test #N', 'verify the fix', 'UAT'. Gives a short script of what to type and what to look for, then records pass, flaky or fail on the GitHub issue. Does NOT fire on 'report this' (cr2-report) or 'what's pending to build' (cr2-desk)."
---

# cr2 test

Louis fixes. Matthew confirms in the real product. This skill makes the confirming fast: it tells Matthew where to go, what to type and what a pass looks like, then writes the result back in the repo's fixed shape. A failed test gets the same complete write-up as a bug filed with cr2-report, so Louis never has to ask what happened. Rules: sections 7 and 12 of `00_docs/github-issue-discipline.md` in `ChaletteHQ/cr2`.

## Who is running this

These skills are shared by Matthew and Erick (the chalette-dev plugin). Work out who is running them in this order and stop at the first answer:

1. **The local profile.** `config/operator.local.json` in this plugin, when present: its `operator` wins (`"m"` is Matthew). Only Matthew keeps one, on his own computer.
2. **The GitHub account.** Run `gh api user --jq .login`. `chaletteholdings` is Matthew; `erick559` is Erick; any other account is treated as Erick. Web and phone chats load a fresh copy of the plugin with no local profile, so this is how they know who is there.
3. **The shared default.** `operator` in `config/operator.json` (Erick).

Say who in one line in the first reply ("Running as Matthew, from the GitHub account."), so a wrong guess shows at once. If the person says otherwise, their word stands for the rest of the chat. If none of the three can be read, never assume: say `FATAL: operator profile unreadable` in one line, then ask once, "Matthew or Erick?", and go on with the answer.

- **Matthew (`m`):** everything below as written. He decides the route (`core` or `labs`), confirms what gets filed, and closes an issue on a passing test.
- **Erick (anyone else):** the same steps, with Matthew's decisions turned into proposals. Suggest a route but file it with the label `question` and the line "Route proposed by Erick, Matthew to confirm." Never close an issue: post the test result and tag Matthew. Never post a build brief as decided; post it as "Proposed by Erick, Matthew to confirm."
- Where the text says "Matthew" as the person you are talking to, talk to whoever is running it. Where it cites a ruling ("Matthew, 2026-10-04"), the ruling stands for both.

## 1. "What needs me" (the queue)

List open issues waiting on Matthew:
- label `needs UAT`: `gh api "repos/ChaletteHQ/cr2/issues?state=open&labels=needs%20UAT&per_page=100"`
- plus any open issue whose latest comment from Louis (GitHub `GiggleSamurai`) starts **Please verify the fix** and has no later UAT result. Read comments with `gh api repos/ChaletteHQ/cr2/issues/N/comments`.

Before listing an issue, read its later comments. If an automated validation (Erick's sessions post "Confirmed on <version>" comments) already shows the fix **failing** on that version or a later one, don't spend Matthew's time on it. Mark it "already failing per #N comment, back to Louis", and offer to remove `needs UAT` with a one-line comment pointing at that evidence.

Show the queue oldest first, one line each: `#N title · fixed in <version> · ~<minutes> · <test folder / real folder / any chat>`. Ask which to run, or start the top one if Matthew says "go".

## 2. Prepare one test

1. Read the issue body, its acceptance check, and Louis's fix comment (version, commit, what changed, what he asks to check).
2. **Version gate.** Read the installed cr2 plugin's version: the `plugin.json` whose `"name"` is `cr2` under `~/.claude/plugins`, `/root/.claude/plugins` or `/mnt/skills/plugins`. If it is older than the fix, stop. Tell Matthew to update the cr2 plugin in the Claude app and start a fresh chat, then check again. Note the version and the `main` commit; a fail report needs both.
3. **Pick the folder.** Use a test folder (a synthetic or copied test brain) for anything that converts, moves, deletes or rewrites files, or that runs Maintenance against a book. Use the real folder only when the bug can only show there, and say so up front. Never run a destructive step on the real folder without Matthew's explicit yes in this chat.
4. **Decide where it runs.** Most tests run in a **new chat** (the product's real path), not in this one, because this chat now carries extra skills and context. Script-level checks (a command, a file's contents) can run here; say which.

## 3. Give Matthew the script

Keep it to what he does and what he looks at. Shape:

```
Test #N on <version> · about <n> minutes
What was fixed: <one plain line>
Setup: <new chat / attach TEST folder / nothing>

Step 1. The original failure, 3 runs
Given: <setup in plain words: a fresh chat, the test folder attached>
When you type:
    <exact text, in a code block so it copies cleanly>
Then: <what the answer should do, in business words>
Pass if: <X is there> and <Y is not>   (yes or no, never a score)
Evidence: paste <the line> / screenshot <the widget>
Do it 3 times, each in a new chat. Tell me how many of 3 passed.

Step 2. A nearby case Louis named
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

**The test-log prompt.** Every script ends with it, in its own code block so it copies cleanly, every time, without being asked (Matthew, 2026-10-15). It is the only way to see what a test chat did behind its answer: which script ran, where, and what failed quietly. The 0.8.109 test of #169 showed why: the answer was right in 3 of 3 runs while the fix's own path never ran, and only the run log gave it away.

```
For a test log, list exactly what you just did, in order: each skill you loaded, each script or command you ran (name and whether it ran in this chat or on my computer), each connector you called, every file you read or wrote or filed as a proposal (path only), any error or warning word for word, and whether anything was saved, queued for Maintenance, or not saved. Facts only, no summary of the findings, no client names.
```

If an earlier test chat is still open and its log was never taken, ask for it there before posting.

Rules for a good script:
- Every step has an exact thing to type or click and an observable result. Never "check that it works".
- Test the original failure first: the exact action from the issue's steps. Then one nearby case Louis named.
- **Run the original failure 3 times, each in a fresh chat.** Command Room is an AI product, so one good run proves little. 3 of 3 is a pass, 1 or 2 of 3 is **partial (flaky)**, 0 of 3 is a fail. For a step that changes files, reset the test folder between runs, or run it once and say so in the result.
- Every check is a yes/no about the answer ("the brief names three meetings and no client names"), never a score. Name the evidence for each.
- Add one **regression** step (a related closed issue still works) and one **near-miss** step (a phrase that must go to a different skill). Fixes often break a neighbour.
- For a risky fix (conversion, Maintenance, anything that moves or deletes files), you may add one optional 5-minute look-around: "Explore <surface> with the test folder to find anything wrong or missing." Anything found becomes a new issue through cr2-report, not part of this verdict.
- Every script ends with the test-log prompt, verbatim, for every run. It is never optional and never left for Matthew to ask for.
- Three to six steps. Over ten minutes, split it into two tests.
- If a step needs proof, name it ("paste the line that starts `Saved.`", or "screenshot the widget" for anything visual).
- Say what not to do when a wrong move would spoil the test ("don't say 'run maintenance' yet").

## 4. Record the result

**Evidence before verdict.** Before posting a pass, quote what was seen (the pasted line, or the screenshot's name) against each pass criterion. No evidence for a criterion means that criterion is not passed.

**Judge the path, not only the answer.** Read each run's test log against Louis's fix comment: did the script or route he changed actually run? A right answer reached by a workaround (the model reading files by hand because the fix's own path failed) is **partial**, never a pass. Where the folder is reachable, check the log's claims against the book's run log (`_hq/_system/runs/`). A run with no test log is posted as "no test log" in its row, never silently counted as a pass.

Scrub every result before posting with the **cr2-scrub** skill. Post with `gh api repos/ChaletteHQ/cr2/issues/N/comments -F body=@<scratch>/uat.md`.

### Pass

```
**UAT pass** on <version> (`<commit>`) · **3 of 3 runs**
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

Matthew closes on a pass (his ruling, 2026-10-04). Close it: `gh api -X PATCH repos/ChaletteHQ/cr2/issues/N -f state=closed -f state_reason=completed`. Remove the label: `gh api -X DELETE "repos/ChaletteHQ/cr2/issues/N/labels/needs%20UAT"`.

### Fail or partial: a full report, every time

A failed or partial test is a bug report on the fix, so it carries everything cr2-report puts in a bug. Nothing is left for Louis to ask.

**Get the evidence first.** The failure usually happened in the separate test chat, so ask Matthew for one of these:
- paste the reply he got (and any error) and that chat's test log here; build the chat log below from the test log;
- or say "report this" in the test chat. cr2-report finds this open issue and comments there with that chat's log. Then post only the UAT header and step results below, and link that comment.

For anything visual, ask for a full-window screenshot (Windows: Win+Shift+S, window mode, names covered), and add `needs evidence` until he says it's attached.

**Post this shape:**

```
@GiggleSamurai **UAT fail** (or **UAT partial (flaky)**) on <installed version> (`<main commit>`) · **<n> of 3 runs passed**

**What happened:** one line
**Impact:** who is affected and how badly
**Expected:** <from the acceptance check and your fix comment>
**Actual:** <what was seen; error text verbatim>
**Steps to reproduce** (exactly as run)
1. <setup: new chat, folder attached or connector, test or real folder>
2. typed: "<exact text>"
3. ...
**Step results:** step 1 pass · step 2 fail · step 3 not run (blocked by 2)
**Where:** cr2 <installed version> (main is <version>) · chat or scheduled task · desktop, web or phone · folder attached or connector · test or real folder
**Model:** <as shown in the app> · **Deviations from the script:** <none / what>
**Reproduced?** yes, by Matthew on <version>, <n> of <n> tries
**Against your fix comment:** <which of the claimed changes held, which did not>
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

Chat log rules (the same as cr2-report): one line per turn, high level, what was typed verbatim, what Claude did, what it answered, errors verbatim. No internal reasoning, no long tool output, no file contents. About 5 to 20 lines.

Then leave the issue open and remove `needs UAT`: `gh api -X DELETE "repos/ChaletteHQ/cr2/issues/N/labels/needs%20UAT"`.

### Other outcomes

- **Not tested, blocked by something specific** (wrong version, a broken prerequisite, no test folder): post one line, "Not tested: <reason>", and add the `blocked` label, so the issue shows why it is stuck.
- **Not tested, no time:** say so in one line and post nothing. Silence never counts as a pass.
- **A new, different problem** found while testing gets its own issue through **cr2-report**, linked here, not a paragraph in this comment.

REST only (GraphQL is blocked). If `gh` can't reach the repo in a cloud session, attach it with the add_repo tool (`ChaletteHQ`, `cr2`) and retry once.

## 5. Reply

One line per test: `#N pass, closed` or `#N fail, full report posted, back to Louis`, plus the next item in the queue and its estimated minutes.