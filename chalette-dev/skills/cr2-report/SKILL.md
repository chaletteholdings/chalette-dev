---
name: "cr2-report"
description: "Use when Matthew or Erick wants something that broke, or an idea, turned into a GitHub issue on ChaletteHQ/cr2 from the chat where it came up: 'report this', 'file a bug', 'log this for Louis', 'feature request', 'spec it', 'send it to build'. Does NOT fire on 'scrub this' or 'scrub the repo' (cr2-scrub), 'what needs me' or 'test #N' (cr2-test), or 'what's pending to build' (cr2-desk)."
---

# cr2 report

Turns what just happened in this chat into one clean GitHub issue, so Matthew spends a minute on it and Louis (also spelled Lewis) gets everything he needs. **A report is an issue, never a branch or a pull request.** The issue is also the handoff to Claude Code: cr2-build builds from an issue that carries a route label, `core` or `labs`.

The repo's own rules are `00_docs/github-issue-discipline.md` and `06_labs/README.md` in `ChaletteHQ/cr2`. This skill follows them.

It also owns **the scrub**: the check that keeps client names, personal details and money figures out of the repo. It uses the cr2-scrub skill for that; "scrub this" or "scrub the repo" goes straight to cr2-scrub.

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

## 1. Decide what it is

- **Bug:** something promised, or that used to work, does not. Label `bug`, plus a route (step 4b).
- **Feature request:** Matthew wants new or different behaviour ("I want X", "spec it", "send it to build"). Label `enhancement`, plus a route (step 4b).
- **Scrub only** ("scrub this", "scrub the repo", "privacy check"): that is cr2-scrub, not this skill.
- One problem or one feature per issue. If the chat shows two, file two issues and link them.
- **One place for everything:** every issue goes on `ChaletteHQ/cr2`, including issues about these dev skills. No other repo gets issues.
- Ask only if it truly could be either. Otherwise decide and say which in the confirmation line.

## 2. Gather (without asking Matthew for what you can see)

- **The chat log:** this conversation is the evidence, so run the skill in the chat where the problem happened. If it happened in another chat, ask Matthew to say "report this" there, or to paste that chat's key turns here.
- **Version:** read `version` from the installed plugin's `.claude-plugin/plugin.json`. Search for a `plugin.json` whose `"name"` is `cr2` (and `cr2-labs` if the problem is in a labs skill) under `~/.claude/plugins`, `/root/.claude/plugins` or `/mnt/skills/plugins`. Note the current `main` version too: `gh api repos/ChaletteHQ/cr2/contents/02_product/.claude-plugin/plugin.json -q .content | base64 -d`. If you can't find it, write "unknown".
- **Where:** chat or scheduled task; desktop, web or phone; folder attached directly or through the connector; test folder or real folder (never its contents).
- **Error text,** verbatim, plus the failing tool output if there was one (trimmed to the lines that matter).
- **Last version that worked / first version that broke,** if the chat or the owner knows. Otherwise "unknown". This narrows the search to one release.
- **Severity,** from two questions you can usually answer from the chat (ask only if you can't):
  1. Is work blocked, or is an answer silently wrong (wrong client data, something lost or misfiled)?
  2. Is there a workaround?
  - **S1:** blocked or silently wrong, and no workaround. Data lost or misfiled is always S1.
  - **S2:** broken, but there is a workaround.
  - **S3:** annoying, slow or cosmetic.
  Severity goes in the body. Priority is Louis's call.

## 3. Check for an existing issue

List open and recent issues and match by title and area: `gh api "repos/ChaletteHQ/cr2/issues?state=all&per_page=100&page=1" -q '.[]|select(.pull_request|not)|"\(.number) [\(.state)] \(.title)"'` (page 2 if needed). Read the body of any close match. The search endpoint is blocked in cloud sessions, so use this list.
- If the same problem or feature is already open, **comment there** with the new evidence (same chat log format) instead of opening a twin. Similar symptoms do not prove the same cause; if unsure, open a new issue and link the old one.
- If it was closed and is back, comment on it and say it came back on version X. Louis reopens.

## 4. Write it

**Where every fact came from.** AI-written bug reports are known to invent steps and details. So every line in the body is one of three kinds, and says which when it isn't obvious:
- **Owner said:** what the owner typed or told you.
- **Claude saw:** a tool result, error, file or screenshot in this chat.
- **Claude's guess:** anything inferred. Guesses go only under "Suspected cause" or "For whoever fixes it".
Steps that nobody re-ran are written as "Owner's account, not reproduced."

Title: `[Area] what fails, in plain words` for a bug, `[Area] what the owner can do` for a feature. Area is the skill or surface: `[Let's work]`, `[Maintenance]`, `[Morning Brief]`, `[Conversion]`, `[Email writer]`, `[Labs]` and so on.

**Bug body:**
```
**What happened:** one line
**Impact:** who is affected and how badly
**Expected:**
**Actual:** (error text verbatim)
**Steps to reproduce**
1. ...
**Severity:** S1 / S2 / S3 (blocked or silently wrong? workaround?)
**Where:** plugin <version> (main is <version>) · chat or scheduled task · desktop, web or phone · folder attached or connector · test or real folder
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

Chat log rules (Louis's ask): one line per turn, high level. What was typed (verbatim), what Claude did, what it answered, errors verbatim. **No internal reasoning, no long tool output, no file contents.** About 5 to 20 lines. Trim the turns that don't matter.

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
- **Route:** core (default) / labs only if Matthew said so for this item
- **Skill:** new skill <name> / change to labs skill <name> / change to cr2 skill <name>
- **Triggers:** the exact phrases that start it, and the near misses it must not catch
- **Reads:** what it needs from the book or live sources (people, projects, plate, mail, calendar)
- **Writes:** nothing / an intake drop with <kind of rows> / a page in the project folder
- **Uses:** the cr2 scripts or contracts it relies on, if known

<details>
<summary>Chat log</summary>
... the turns where the idea took shape ...
</details>
```

Describe the outcome, not the code. Add a "Suggested approach" line only if Matthew gave one.

### 4b. Route: core by default

Matthew's ruling (2026-10-04, #136): everything is filed `core` unless he has said labs for this item. He moves items to labs himself. Never ask him for a route. The confirmation line says "core (default)".
- File `labs` only when Matthew said labs for this item in this chat.
- For Erick, the route is still a proposal: add `question` and "Route proposed by Erick, Matthew to confirm."

### 4c. Check the draft against the chat

Before the scrub, read the draft line by line. Every step, error string, number and version must point to a chat-log turn (or a command you ran). Anything that can't is either removed or moved under "Suspected cause", marked as a guess. No citation, no fact.

## 5. Scrub (always, before anything is posted)

Run the scrub (cr2-scrub, section S below) on the title, body and chat log. Replace every client name, real person, family member, real email, phone, money figure and client folder name with a placeholder (`Contact A`, `<client folder>`, `an amount`), and add one line saying so. A screenshot gets the same treatment: it is attached only after the visible names are covered.

## 6. Confirm, then file

Show Matthew the title plus three lines (what it is, impact or outcome, labels with "core (default)") and ask "File it?". On yes:

```
gh api repos/ChaletteHQ/cr2/issues -f title="<title>" -F body=@<scratch>/issue.md -f "labels[]=enhancement" -f "labels[]=core" -q .html_url
```

Labels: `bug` or `enhancement`, plus `core` (or `labs` when Matthew said so).

- Use REST only. GraphQL (`gh issue create`, `gh pr list`) is blocked in these sessions.
- If `gh` can't reach the repo in a cloud session, attach it with the add_repo tool (`ChaletteHQ`, `cr2`) and retry once.
- If there is no GitHub access at all, save the issue to scratch and give Matthew a prefilled link: `https://github.com/ChaletteHQ/cr2/issues/new?title=<urlencoded>&labels=enhancement&body=<urlencoded>`. If the body is over about 6,000 characters, give the link with the title only and the body to paste.

**Visual bugs** (a widget, page, artifact, layout, anything you judge by looking): also add the `needs evidence` label. Tell Matthew in one line to take a full-window screenshot (Windows: Win+Shift+S, window mode), cover any names, and drag it into the issue. When he says it's attached, remove `needs evidence`.

## 7. Reply

One line: `Filed #N: <title>` with the link. Add the screenshot line if one is needed. No recap. Then:

`Next: say "get #N ready" here to write its build brief. Then, to build it yourself, open the cr2 repo in Claude Code and say "build #N": it builds from Louis's latest version and puts the result on your preview to test. Or leave it for Louis.`

## Never

- Never open a branch or pull request from this skill. Building happens in Claude Code with cr2-build, from the issue.
- Never post before the scrub passes.
- Never claim something was reproduced or tested when it was only reported.
- Never file `labs` unless Matthew said labs for this item.

## S. The scrub

Use the **cr2-scrub** skill in this plugin: its Step 1 (name list from the book), Step 2 (scan), Step 3 (judge) and, for "scrub the repo", Step 4 (fix). Its script is `cr2-scrub/scripts/scrub_scan.py`. The rule, the allowed list and the placeholders are written there once, so they never drift apart.
