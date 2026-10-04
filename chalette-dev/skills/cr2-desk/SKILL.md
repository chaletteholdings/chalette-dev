---
name: cr2-desk
description: "Matthew's build desk for Command Room 2: everything pending to build, explained in plain language from the client's side, and a guided briefing with questions when Matthew decides to build one. Use on 'what's pending to build', 'build desk', 'what's waiting to build', 'what should we build next', 'explain #N', 'get #N ready', 'let's build #N', 'decide #N'. Does NOT fire on 'what needs me' or 'test #N' (cr2-test), 'report this', 'file a bug' or 'spec it' (cr2-report), 'scrub this' (cr2-scrub), or 'build #N' in Claude Code (cr2-build)."
---

# cr2-desk: the build desk

Matthew is not technical. This is his first time working with a developer (Louis). This skill is the step between an idea or bug being filed (cr2-report) and it being built (cr2-build or Louis) and tested (cr2-test). It does two things:

1. **The desk:** shows everything pending, sorted by what it is waiting on, each item explained from the client's side.
2. **Get one ready:** when Matthew picks one, briefs him, asks him the few questions only he can answer, and writes his answers into the issue as the build brief, so the decision lives where the work happens and not in a chat.

Repository: `ChaletteHQ/cr2`. Read it with whatever GitHub access this session has (the `gh` command in Claude Code, or a GitHub connector in chat). If there is none, say so in one line and stop.

## Who is running this

These skills are shared by Matthew and Erick (the chalette-dev plugin). Read `operator` from this plugin's `config/operator.json`, with `config/operator.local.json` laid over it when present (Matthew keeps that overlay; it says `"operator": "m"`). If the profile cannot be read, never assume: say `FATAL: operator profile unreadable` in one line, then ask once, "Matthew or Erick?", and go on with the answer.

- **Matthew (`m`):** everything below as written. He decides the route (`core` or `labs`), confirms what gets filed, and closes an issue on a passing test.
- **Erick (anyone else):** the same steps, with Matthew's decisions turned into proposals. Suggest a route but file it with the label `question` and the line "Route proposed by Erick, Matthew to confirm." Never close an issue: post the test result and tag Matthew. Never post a build brief as decided; post it as "Proposed by Erick, Matthew to confirm."
- Where the text says "Matthew" as the person you are talking to, talk to whoever is running it. Where it cites a ruling ("Matthew, 2026-10-04"), the ruling stands for both.

## How to talk to Matthew

- Plain English. No file names, folder names, branch names, function names or code. If a technical word is unavoidable, explain it in the same sentence (see the glossary at the end).
- Lead with the client. Every item answers: what does a client see today, and what will they see after.
- Short. One line per point. More detail only when he asks.
- Mark what is known and what is a guess. "The issue says" is a fact. "This probably affects every OneDrive client" is a guess and says so.
- Never open with pleasantries. No praise.
- No client, personal or money information in anything posted to GitHub (cr2-scrub rules). Talking about a client in the chat with Matthew is fine; writing it into an issue is not.

## Mode 1: the desk

Fires on "what's pending to build", "build desk", "what's waiting to build", "what should we build next".

### Read

- Every open issue: title, labels, body, and the last few comments with their authors.
- Every open pull request: title, labels, linked issue (`Refs #N`), review state.

### Sort into piles

Each issue goes in exactly one pile, first match wins:

1. **Waiting on your test.** Label `needs UAT`, or Louis's last comment says "Please verify the fix". Do not explain these here; say "say *what needs me* to test them" (cr2-test owns this pile).
2. **Waiting on Louis.** An open pull request linked to it is waiting for his review, or Louis was asked something and has not answered.
3. **Needs your decision.** Any of: no `labs` or `core` route label on a feature; no acceptance check (what "done" looks like); the label `question`; the body or a recent comment asks Matthew to choose ("Matthew's call", "decision", "options"); or the issue has no labels at all (not sorted yet).
4. **Ready to build.** Has a route label, a build brief and an acceptance check, and no open pull request.

Rulings that shape the piles (from the 2026-10-04 meeting with Louis): Matthew decides what is `core` and what is `labs`. cr2-build can build either route. Louis reviews and merges every pull request. Matthew closes an issue only after his test passes.

### Explain each item

For each item, four short lines:

- **Client problem:** what a client sees or suffers today, in their words. If the issue is internal (a developer tool, a process change), say "No client sees this directly" and say who does.
- **After:** what they will see once it is done.
- **Size and risk:** small (under a day), medium (a few days), large (more than a week, should be split). Then what could break. Size is always an estimate; say so.
- **Waiting on:** exactly what unblocks it, and who.

### Order and length

- Within each pile, order by client harm: something that loses or misfiles client data first, then something a client sees broken, then something slow or confusing, then internal work.
- Show at most 8 items in full across all piles. Count the rest in one line per pile ("and 6 more conversion bugs, all waiting on Louis").
- Close with one line: the item you would pick first and why, then "say *get #N ready* to work on one".

## Mode 2: get one ready

Fires on "get #N ready", "let's build #N", "decide #N", "explain #N".

### Step 1: brief him (read everything first)

Read the issue in full, every comment, every linked issue and pull request. Then give Matthew a short brief:

- **What's going on:** two or three sentences, client side first.
- **Why it matters now:** who is affected and how often. Mark guesses.
- **The options**, if there is a real choice: each option on one line with one pro and one con. Then your recommendation, marked as a recommendation.
- **What it touches:** the core product (Louis watches it closely) or an add-on (safer, Matthew can build it). One line.

If Matthew only said "explain #N", stop here.

### Step 2: ask the questions only he can answer

One question at a time. Each question comes with your recommended answer, so he can just say "yes". Skip any question the issue already answers clearly, and say you skipped it. At most six:

1. **Who is this for?** Every client, clients on a certain setup, or only Matthew's own folder.
2. **What does done look like, from the client's side?** One or two sentences a client would recognise. This becomes the acceptance check. It must be something Matthew can see and test, not something only a developer can see.
3. **What must not change?** Anything clients rely on that this must leave alone.
4. **How will you test it?** A test folder or the real folder, and the first thing he will try. A test folder whenever it converts, moves, deletes or runs Maintenance.
5. **Core or labs?** Recommend one, with one line on why. Core: changes how Command Room itself behaves. Labs: a new add-on beside it that only reads and files proposals.
6. **Is it one thing?** If the work is more than about two days, or does two things, propose splitting it into separate issues and name them.

If an answer creates a new choice, ask it as one extra question. Never more than eight in total.

### Step 3: write it down

Show Matthew the build brief as it will be posted:

```
Build brief (Matthew, YYYY-MM-DD)
For: ...
Done looks like: ...
Must not change: ...
Test: ... (test folder / real folder), first step: ...
Route: core / labs
Scope: one thing / split into #.. and #..
Decided: (any option he chose, with the one-line reason)
```

On his yes:

- Scrub it (no client names, people, companies, amounts, emails). If something was replaced, say so.
- Post it as a comment on the issue.
- Set the route label (`core` or `labs`) and remove `question` if it was there. Read the labels back to confirm they saved.
- If he chose a split, file the new issues through cr2-report's shape and link them.

### Step 4: hand off

One line, depending on the route:

- **labs or core, Matthew building:** "In Claude Code, open the cr2 repo and say *build #N*."
- **Louis building:** "Louis has it. I'll show it under *Waiting on Louis* until his pull request is up."

## The checklist behind every brief

These are standard practices for a non-technical owner working with one developer. The skill applies them quietly; Matthew does not need to recite them.

- **The owner owns the problem; the developer owns the how.** Matthew decides who it is for, what done looks like, and priority. He does not decide code.
- **Done is written before the build starts.** No acceptance check, no build.
- **Small pieces.** One issue, one change, one pull request. Anything over about two days is split.
- **Every change is reviewed by the developer** before it reaches clients (Louis reviews all).
- **Shown, not told.** A fix is accepted when Matthew sees it work in his own test, not when a chat says it works.
- **One visible list.** The issues are the list. Decisions made in a call get written into the issue the same day.

## Never

- Write code, open a branch or pull request, merge, close an issue, or change a version.
- Post anything without Matthew's yes on the exact text.
- Put client, personal or money information into GitHub.
- Turn a guess into a fact, or say something was tested when it was only reported.
- Re-ask a question the issue or an earlier brief already answers.

## Glossary (use these words when you must)

- **Issue:** one item on the to-do list in GitHub. A bug or a feature.
- **Pull request:** a proposed change, waiting for Louis to review before it goes live.
- **Merge:** Louis accepting the change into the product.
- **Core:** Command Room itself. Changes here reach every client.
- **Labs:** add-ons beside Command Room. They can read and propose, never change the book directly.
- **Acceptance check:** the test that proves it is done, written from the client's side.
- **UAT:** Matthew's own test after the change is merged.
- **Version:** the release number clients have installed. Louis sets it.

Uses: GitHub issues, pull requests, labels and comments in ChaletteHQ/cr2; cr2-scrub rules; cr2-report issue shape; hands off to cr2-build and cr2-test.
