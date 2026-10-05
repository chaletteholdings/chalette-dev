---
name: "cr2-test"
description: "Use when Matthew or Erick wants to test a Command Room 2 fix that is waiting on them: 'what needs me', 'what do I need to test', 'test #N', 'verify the fix', 'UAT'. Gives a short script of what to type and what to look for, then records pass, flaky or fail on the GitHub issue. Does NOT fire on 'report this' (cr2-report) or 'what's pending to build' (cr2-desk)."
---

# cr2 test

Louis or Matthew builds. Matthew confirms in the real product, twice: first on his **preview** (`ChaletteHQ/cr2-preview`: Louis's `main` plus Matthew's open pull requests, installed on Matthew's account) before Louis merges, then a short **final check** after the merge (the preview flow, #144). This skill makes the confirming fast: it tells Matthew where to go, what to type and what a pass looks like, then writes the result back in the repo's fixed shape. A failed test gets the same complete write-up as a bug filed with cr2-report, so Louis never has to ask what happened. Rules: sections 7 and 12 of `00_docs/github-issue-discipline.md` in `ChaletteHQ/cr2`.

## Who is running this

These skills are shared by Matthew and Erick (the chalette-dev plugin). Read `operator` from this plugin's `config/operator.json`, with `config/operator.local.json` laid over it when present (Matthew keeps that overlay; it says `"operator": "m"`). If the profile cannot be read, never assume: say `FATAL: operator profile unreadable` in one line, then ask once, "Matthew or Erick?", and go on with the answer.

- **Matthew (`m`):** everything below as written. Every item is `core` by default; he moves one to `labs` himself when he wants to (Matthew, 2026-10-04, #136), so he is never asked for a route. He confirms what gets filed, and closes an issue after his final check passes.
- **Erick (anyone else):** the same steps, with Matthew's decisions turned into proposals. Suggest a route but file it with the label `question` and the line "Route proposed by Erick, Matthew to confirm." Never close an issue: post the test result and tag Matthew. Never post a build brief as decided; post it as "Proposed by Erick, Matthew to confirm."
- Where the text says "Matthew" as the person you are talking to, talk to whoever is running it. Where it cites a ruling ("Matthew, 2026-10-04"), the ruling stands for both.

## How to reply (every reply from this skill)

Matthew is not technical and defers on most calls (#136). Any reply that holds recommendations or decisions has two labelled groups, in this order, and an empty group is left out:

- **I'll handle (you can defer):** strong recommendations and mild calls that Claude makes and carries out.
- **You decide:** only what Matthew should actually think about: a trade-off, a cost, something irreversible, or something only he knows.

Nothing that needs him goes under the first group. End with one **Next:** line saying the single thing to do now.

## 1. "What needs me" (the queue)

There are two kinds of test, shown as two groups:

- **Preview tests:** the fix is in an open pull request (its body says `Refs #N`). Matthew tests it on the preview before Louis merges.
- **Final checks:** the pull request is merged (or Louis fixed it on `main` directly) and the issue is still open, with `preview pass` or `needs UAT`. A short re-run of the original failure on a version that contains the merge.

Find the pull request for an issue with `gh api "repos/ChaletteHQ/cr2/pulls?state=all&per_page=100"` and match `Refs #N` in the body.

List open issues waiting on Matthew:
- label `needs UAT`: `gh api "repos/ChaletteHQ/cr2/issues?state=open&labels=needs%20UAT&per_page=100"`
- label `preview pass` whose pull request is now merged (a final check)
- plus any open issue whose latest comment from Louis (GitHub `GiggleSamurai`) starts **Please verify the fix** and has no later UAT result. Read comments with `gh api repos/ChaletteHQ/cr2/issues/N/comments`.

Before listing an issue, read its later comments. If an automated validation (Erick's sessions post "Confirmed on <version>" comments) already shows the fix **failing** on that version or a later one, don't spend Matthew's time on it. Mark it "already failing per #N comment, back to Louis", and offer to remove `needs UAT` with a one-line comment pointing at that evidence.

Show the queue oldest first, one line each: `#N title · fixed in <version> · ~<minutes> · <test folder / real folder / any chat>`. Ask which to run, or start the top one if Matthew says "go".

## 2. Prepare one test

1. Read the issue body, its acceptance check, and Louis's fix comment (version, commit, what changed, what he asks to check).
2. **Version gate.** Read the installed cr2 plugin's version: the `plugin.json` whose `"name"` is `cr2` under `~/.claude/plugins`, `/root/.claude/plugins` or `/mnt/skills/plugins`. Then read what the preview carries: `gh api repos/ChaletteHQ/cr2-preview/contents/PREVIEW.md -q .content | base64 -d` (its version, the `main` commit, and each included pull request with its commit).
   - **Preview test:** the pull request must be listed under Included at its current head commit, and the installed version must equal the preview's version. If the pull request is missing or older, tell Matthew: in Claude Code on the cr2 repo, say "refresh my preview". If it is under Skipped, say "rebase #N" there. If the installed version is older, tell him to press Update on Command Room in the Claude app and open a new chat.
   - **Final check:** the preview's `main` commit must contain the merge (`gh api repos/ChaletteHQ/cr2/compare/<merge sha>...<preview main sha> -q .status` is `ahead` or `identical`), or Matthew is on the live plugin at the merged version or later. If not, the same refresh and Update steps.
   - Note the version and the commits; a fail report needs them.
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

Before you leave the test chat (a separate, second message; never in the same message as the test prompt, which would change the test)
Send this in the test chat after its answer, and paste the reply back here labelled run 1, 2, 3:
    For a UAT record: list every step you took in this chat, one line each, in order.
    For each: the skill or tool, the exact command or call (shortened if long), and the result in a few words.
    Then quote the first 5 lines of your answer to me. No other commentary.

When done, tell me: "pass", or "fail" and paste the reply you got (or say "report this" in that test chat).
```

Rules for a good script:
- Every step has an exact thing to type or click and an observable result. Never "check that it works".
- Test the original failure first: the exact action from the issue's steps. Then one nearby case Louis named.
- **Run the original failure 3 times, each in a fresh chat.** Command Room is an AI product, so one good run proves little. 3 of 3 is a pass, 1 or 2 of 3 is **partial (flaky)**, 0 of 3 is a fail. For a step that changes files, reset the test folder between runs, or run it once and say so in the result.
- Every check is a yes/no about the answer ("the brief names three meetings and no client names"), never a score. Name the evidence for each.
- Add one **regression** step (a related closed issue still works) and one **near-miss** step (a phrase that must go to a different skill). Fixes often break a neighbour.
- For a risky fix (conversion, Maintenance, anything that moves or deletes files), you may add one optional 5-minute look-around: "Explore <surface> with the test folder to find anything wrong or missing." Anything found becomes a new issue through cr2-report, not part of this verdict.
- Every script ends with the step "Before you leave the test chat" holding the log prompt above in its own copy block, sent as a separate second message (#136).
- A **final check** is short: the original failure once, plus anything the merge or a rebase touched.
- Three to six steps. Over ten minutes, split it into two tests.
- If a step needs proof, name it ("paste the line that starts `Saved.`", or "screenshot the widget" for anything visual).
- Say what not to do when a wrong move would spoil the test ("don't say 'run maintenance' yet").

## 4. Record the result

**Evidence before verdict.** Before posting a pass, quote what was seen (the pasted line, or the screenshot's name) against each pass criterion. No evidence for a criterion means that criterion is not passed.

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

**A pass on the preview** is headed `**UAT pass on preview** <preview version> (PR #M at <head commit>, main <commit>)`. Do not close the issue. Add the `preview pass` label, remove `needs UAT`, and comment on the pull request: "@GiggleSamurai passed Matthew's test on the preview; ready for your review when you see fit." Louis merges when he sees fit.

**A pass on the final check** is headed `**Final check pass** on <version> (main <commit>)`. Matthew closes on it (his ruling, 2026-10-04): `gh api -X PATCH repos/ChaletteHQ/cr2/issues/N -f state=closed -f state_reason=completed`. Remove the labels: `gh api -X DELETE "repos/ChaletteHQ/cr2/issues/N/labels/needs%20UAT"` and the same for `preview%20pass`.

### Fail or partial: a full report, every time

A failed or partial test is a bug report on the fix, so it carries everything cr2-report puts in a bug. Nothing is left for Louis to ask.

**Get the evidence first.** The failure usually happened in the separate test chat, so ask Matthew for one of these:
- paste the reply he got (and any error) here;
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

Who gets it back: if the pull request is Matthew's own (built with cr2-build), tag no one in the header; the fix goes back to the builder: "In Claude Code say *build #N*: it adds the fix to the same pull request and refreshes your preview." If it is Louis's fix, tag `@GiggleSamurai` as above.

### Other outcomes

- **Not tested, blocked by something specific** (wrong version, a broken prerequisite, no test folder): post one line, "Not tested: <reason>", and add the `blocked` label, so the issue shows why it is stuck.
- **Not tested, no time:** say so in one line and post nothing. Silence never counts as a pass.
- **A new, different problem** found while testing gets its own issue through **cr2-report**, linked here, not a paragraph in this comment.

REST only (GraphQL is blocked). If `gh` can't reach the repo in a cloud session, attach it with the add_repo tool (`ChaletteHQ`, `cr2`) and retry once.

## 5. Reply

One line per test: `#N passed on the preview, waiting on Louis to merge`, `#N final check passed, closed`, or `#N fail, full report posted, back to <the builder>`. Then:

`Next: <the next item in the queue and its estimated minutes>`, or, after a fail on Matthew's own pull request, `Next: in Claude Code on the cr2 repo, say "build #N" to fix it on the same pull request.`