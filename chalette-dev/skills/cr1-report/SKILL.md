---
name: "cr1-report"
description: "Use when Matthew or Erick wants something that broke, or an idea, turned into a GitHub issue on chaletteholdings/cr1 (Command Room 1) from the chat where it came up: 'report this', 'file a bug', 'feature request', 'spec it', 'send it to build'. Does NOT fire on 'scrub this' or 'scrub the repo' (cr1-scrub), 'what needs me' or 'test #N' (cr1-test), or 'what's pending to build' (cr1-desk)."
---

# cr1 report

Turns what just happened in this chat into one clean GitHub issue, so Matthew spends a minute on it and whoever builds the fix gets everything they need. **A report is an issue, never a branch or a pull request.** The issue is also the handoff to Claude Code: cr1-build, a project skill inside the cr1 repo, builds from the issue.

The repo is `chaletteholdings/cr1`, branch `main`. Its own rules are `ISSUES.md`, `CONTRIBUTING.md` and `DEVELOPMENT.md` at the repo root. This skill follows them.

It also owns **the scrub**: the check that keeps client names, personal details and money figures out of the repo. It uses the cr1-scrub skill for that; "scrub this" or "scrub the repo" goes straight to cr1-scrub.

## Who is running this

These skills are shared by Matthew and Erick (the chalette-dev plugin). Work out who is running them in this order and stop at the first answer:

1. **The local profile.** `config/operator.local.json` in this plugin, when present: its `operator` wins (`"m"` is Matthew). Only Matthew keeps one, on his own computer.
2. **The GitHub account.** Run `gh api user --jq .login`. `chaletteholdings` is Matthew; `erick559` is Erick; any other account is treated as Erick. Web and phone chats load a fresh copy of the plugin with no local profile, so this is how they know who is there.
3. **The shared default.** `operator` in `config/operator.json` (Erick).

Say who in one line in the first reply ("Running as Matthew, from the GitHub account."), so a wrong guess shows at once. If the person says otherwise, their word stands for the rest of the chat. If none of the three can be read, never assume: say `FATAL: operator profile unreadable` in one line, then ask once, "Matthew or Erick?", and go on with the answer.

- **Matthew (`m`):** everything below as written. He confirms what gets filed, decides what is ready to build, merges, and closes an issue on a passing test.
- **Erick (anyone else):** the same steps, with Matthew's decisions turned into proposals. File it with the label `question` and the line "Proposed by Erick, Matthew to confirm." Never close an issue: post the test result and tag Matthew. Never post a build brief as decided; post it as "Proposed by Erick, Matthew to confirm."
- Where the text says "Matthew" as the person you are talking to, talk to whoever is running it. Where it cites a ruling ("Matthew, 2026-10-04"), the ruling stands for both.

## 1. Decide what it is

- **Bug:** something promised, or that used to work, does not. Label `bug`.
- **Feature request:** Matthew wants new or different behaviour ("I want X", "spec it", "send it to build"). Label `enhancement`.
- **Scrub only** ("scrub this", "scrub the repo", "privacy check"): that is cr1-scrub, not this skill.
- One problem or one feature per issue. If the chat shows two, file two issues and link them.
- Ask only if it truly could be either. Otherwise decide and say which in the confirmation line.

## 2. Gather (without asking Matthew for what you can see)

- **The chat log:** this conversation is the evidence, so run the skill in the chat where the problem happened. If it happened in another chat, ask Matthew to say "report this" there, or to paste that chat's key turns here.
- **Version:** read `version` from the installed plugin's `.claude-plugin/plugin.json`. Search for a `plugin.json` whose `"name"` is `command-room` under `~/.claude/plugins`, `/root/.claude/plugins` or `/mnt/skills/plugins`. If it sits under a `commandroom1` folder, it is Matthew's staging plugin `cr`, which follows `main` by commit: note its commit too (the `gitCommitSha` of `cr@commandroom1` in `installed_plugins.json` beside the plugins folder). Note the current `main` version too: `gh api repos/chaletteholdings/cr1/contents/command-room/.claude-plugin/plugin.json -q .content | base64 -d`. If you can't find it, write "unknown".
- **Where:** chat or scheduled task; desktop, web or phone; folder attached directly or through the connector; test folder or real folder (never its contents).
- **Error text,** verbatim, plus the failing tool output if there was one (trimmed to the lines that matter).
- **Last version that worked / first version that broke,** if the chat or the owner knows. Otherwise "unknown". This narrows the search to one release.
- **Severity,** from two questions you can usually answer from the chat (ask only if you can't):
  1. Is work blocked, or is an answer silently wrong (wrong client data, something lost or misfiled)?
  2. Is there a workaround?
  - **S1:** blocked or silently wrong, and no workaround. Data lost or misfiled is always S1.
  - **S2:** broken, but there is a workaround.
  - **S3:** annoying, slow or cosmetic.
  Severity goes in the body. Priority is Matthew's call.

## 3. Check for an existing issue

List open and recent issues and match by title and area: `gh api "repos/chaletteholdings/cr1/issues?state=all&per_page=100&page=1" -q '.[]|select(.pull_request|not)|"\(.number) [\(.state)] \(.title)"'` (page 2 if needed). Read the body of any close match. The search endpoint is blocked in cloud sessions, so use this list.
- If the same problem or feature is already open, **comment there** with the new evidence (same chat log format) instead of opening a twin. Similar symptoms do not prove the same cause; if unsure, open a new issue and link the old one.
- If it was closed and is back, comment on it and say it came back on version X. Matthew reopens it; Erick asks him to in the comment.

## 4. Write it

**Where every fact came from.** AI-written bug reports are known to invent steps and details. So every line in the body is one of three kinds, and says which when it isn't obvious:
- **Owner said:** what the owner typed or told you.
- **Claude saw:** a tool result, error, file or screenshot in this chat.
- **Claude's guess:** anything inferred. Guesses go only under "Suspected cause" or "For whoever fixes it".
Steps that nobody re-ran are written as "Owner's account, not reproduced."

Title: `[Area] what fails, in plain words` for a bug, `[Area] what the owner can do` for a feature. Area is the skill or surface, named as in `command-room/skills/` in plain words: `[Morning briefing]`, `[Inbox triage]`, `[Meeting notes]`, `[Commitments]`, `[Maintenance]`, `[Email writer]`, `[Widgets]`, `[Onboarding]` and so on.

**Bug body:**
```
**What happened:** one line
**Impact:** who is affected and how badly
**Expected:**
**Actual:** (error text verbatim)
**Steps to reproduce**
1. ...
**Severity:** S1 / S2 / S3 (blocked or silently wrong? workaround?)
**Where:** plugin <command-room version, or cr at commit> (main is <version>) · chat or scheduled task · desktop, web or phone · folder attached or connector · test or real folder
**Last worked:** <version or unknown> · **First broke:** <version or unknown>
**Reproduced?** seen once by Matthew / seen N times / not yet reproduced
**Acceptance check:** what will be true when this is fixed

**For whoever fixes it**
- **Trigger:** the exact prompt, and the folder state it ran on (test or real, attached or connector)
- **Likely skill or area:** <name> (a guess)
- **Suggested fix:** <one line> (a guess, not verified)

<details>
<summary>Chat log</summary>

1. **Matthew:** "exact words typed"
2. **Claude:** ran <skill or script or connector call>, read or wrote <file kind>, answered: "<short quote or summary>"
3. **Error:** `verbatim error text`
...
</details>

**Screenshot:** <attached / not needed (not visual) / needed: Matthew to add>
**Suspected cause (not verified):** only if there is a real clue; keep it apart from the facts

_Drafted by Claude from chat; confirmed by <Matthew or Erick> on <date>; reproduced: yes / no._
```

Keep the body short: about 40 lines outside the collapsed chat log. Studies of what helps fixers, human or AI, find that longer reports do worse; the trigger prompt and a suggested fix help most.

Chat log rules: one line per turn, high level. What was typed (verbatim), what Claude did, what it answered, errors verbatim. **No internal reasoning, no long tool output, no file contents.** About 5 to 20 lines. Trim the turns that don't matter.

### 4a. Feature body

```
**Outcome:** what Matthew can do afterwards that he cannot do now
**Why:** the moment it came up (by shape, no names) and what it costs today
**Acceptance check:** how we will know it works (observable steps)
**Priority:** now / next / later, and why
**Not asking for:** limits, so the scope stays small
**Related:** #N

_Drafted by Claude from chat; confirmed by <Matthew or Erick> on <date>._

## Build brief
- **Skill:** new skill <name> / change to skill <name>
- **Triggers:** the exact phrases that start it, and the near misses it must not catch
- **Reads:** what it needs from the book or live sources (people, projects, commitments, mail, calendar)
- **Writes:** nothing / events in the book / a page in the project folder
- **Uses:** the cr1 scripts or contracts it relies on, if known

<details>
<summary>Chat log</summary>
... the turns where the idea took shape ...
</details>
```

Describe the outcome, not the code. Add a "Suggested approach" line only if Matthew gave one.

### 4b. Check the draft against the chat

Before the scrub, read the draft line by line. Every step, error string, number and version must point to a chat-log turn (or a command you ran). Anything that can't is either removed or moved under "Suspected cause", marked as a guess. No citation, no fact.

## 5. Scrub (always, before anything is posted)

Run the scrub (cr1-scrub, section S below) on the title, body and chat log. Replace every client name, real person, family member, real email, phone, money figure and client folder name with a placeholder (`Contact A`, `<client folder>`, `an amount`), and add one line saying so. Screenshots from a real folder are never attached (the owner's rule): use a screenshot taken on a test folder, or give the exact error text instead.

## 6. Confirm, then file

Show Matthew the title plus three lines (what it is, impact or outcome, labels) and ask "File it?". On yes:

```
gh api repos/chaletteholdings/cr1/issues -f title="<title>" -F body=@<scratch>/issue.md -f "labels[]=enhancement" -q .html_url
```

Labels: `bug` or `enhancement`, plus `question` when Erick files it.

- Use REST only. GraphQL (`gh issue create`, `gh pr list`) is blocked in these sessions.
- If `gh` can't reach the repo in a cloud session, attach it with the add_repo tool (`chaletteholdings`, `cr1`) and retry once.
- If there is no GitHub access at all, save the issue to scratch and give Matthew a prefilled link: `https://github.com/chaletteholdings/cr1/issues/new?title=<urlencoded>&labels=enhancement&body=<urlencoded>`. If the body is over about 6,000 characters, give the link with the title only and the body to paste.

**Visual bugs** (a widget, page, artifact, layout, anything you judge by looking): also add the `needs evidence` label. Tell Matthew in one line to reproduce it on a test folder, take a full-window screenshot there (Windows: Win+Shift+S, window mode) and drag it into the issue; if it only shows on the real folder, paste the exact error text instead. When he says it's attached, remove `needs evidence`.

## 7. Reply

One line: `Filed #N: <title>` with the link, then: "To build it, open the cr1 repo in Claude Code and say: build #N." Add the screenshot line if one is needed. No recap.

## Never

- Never open a branch or pull request from this skill. Building happens in Claude Code with cr1-build, from the issue.
- Never post before the scrub passes.
- Never claim something was reproduced or tested when it was only reported.
- Never set a version or write the CHANGELOG. Those are set only at release, by Matthew's ship-cr-plugin flow.

## S. The scrub

Use the **cr1-scrub** skill in this plugin: its Step 1 (name list from the book), Step 2 (scan), Step 3 (judge) and, for "scrub the repo", Step 4 (fix). Its script is `cr1-scrub/scripts/scrub_scan.py`. The rule, the allowed list and the placeholders are written there once, so they never drift apart.
