---
name: "cr2-report"
description: "Files a Command Room 2 bug or feature request for Louis on GitHub (ChaletteHQ/cr2) with chat log, version, built-in scrub, and a build brief with the core or labs route Matthew confirms; also scrubs text or the whole repo. Use on 'report this', 'file a bug', 'feature request', 'spec it', 'send it to build', 'scrub this', 'scrub the repo'."
---

# cr2 report

Turns what just happened in this chat into one clean GitHub issue, so Matthew spends a minute on it and Louis (also spelled Lewis) gets everything he needs. **A report is an issue, never a branch or a pull request.** The issue is also the handoff to Claude Code: cr2-build builds from an issue that carries a route label, `core` or `labs`.

The repo's own rules are `00_docs/github-issue-discipline.md` and `06_labs/README.md` in `ChaletteHQ/cr2`. This skill follows them.

It also owns **the scrub**: the check that keeps client names, personal details and money figures out of the repo. It uses the cr2-scrub skill for that; "scrub this" or "scrub the repo" goes straight to cr2-scrub.

## Who is running this

These skills are shared by Matthew and Erick (the chalette-dev plugin). Read `operator` from this plugin's `config/operator.json`, with `config/operator.local.json` laid over it when present (Matthew keeps that overlay; it says `"operator": "m"`). If the profile cannot be read, never assume: say `FATAL: operator profile unreadable` in one line, then ask once, "Matthew or Erick?", and go on with the answer.

- **Matthew (`m`):** everything below as written. He decides the route (`core` or `labs`), confirms what gets filed, and closes an issue on a passing test.
- **Erick (anyone else):** the same steps, with Matthew's decisions turned into proposals. Suggest a route but file it with the label `question` and the line "Route proposed by Erick, Matthew to confirm." Never close an issue: post the test result and tag Matthew. Never post a build brief as decided; post it as "Proposed by Erick, Matthew to confirm."
- Where the text says "Matthew" as the person you are talking to, talk to whoever is running it. Where it cites a ruling ("Matthew, 2026-10-04"), the ruling stands for both.

## 1. Decide what it is

- **Bug:** something promised, or that used to work, does not. Label `bug`, plus a route (step 4b).
- **Feature request:** Matthew wants new or different behaviour ("I want X", "spec it", "send it to build"). Label `enhancement`, plus a route (step 4b).
- **Scrub only** ("scrub this", "scrub the repo", "privacy check"): skip to section S.
- One problem or one feature per issue. If the chat shows two, file two issues and link them.
- Ask only if it truly could be either. Otherwise decide and say which in the confirmation line.

## 2. Gather (without asking Matthew for what you can see)

- **The chat log:** this conversation is the evidence, so run the skill in the chat where the problem happened. If it happened in another chat, ask Matthew to say "report this" there, or to paste that chat's key turns here.
- **Version:** read `version` from the installed plugin's `.claude-plugin/plugin.json`. Search for a `plugin.json` whose `"name"` is `cr2` (and `cr2-labs` if the problem is in a labs skill) under `~/.claude/plugins`, `/root/.claude/plugins` or `/mnt/skills/plugins`. Note the current `main` version too: `gh api repos/ChaletteHQ/cr2/contents/02_product/.claude-plugin/plugin.json -q .content | base64 -d`. If you can't find it, write "unknown".
- **Where:** chat or scheduled task; desktop, web or phone; folder attached directly or through the connector; test folder or real folder (never its contents).
- **Error text,** verbatim.

## 3. Check for an existing issue

List open and recent issues and match by title and area: `gh api "repos/ChaletteHQ/cr2/issues?state=all&per_page=100&page=1" -q '.[]|select(.pull_request|not)|"\(.number) [\(.state)] \(.title)"'` (page 2 if needed). Read the body of any close match. The search endpoint is blocked in cloud sessions, so use this list.
- If the same problem or feature is already open, **comment there** with the new evidence (same chat log format) instead of opening a twin. Similar symptoms do not prove the same cause; if unsure, open a new issue and link the old one.
- If it was closed and is back, comment on it and say it came back on version X. Louis reopens.

## 4. Write it

Title: `[Area] what fails, in plain words` for a bug, `[Area] what the owner can do` for a feature. Area is the skill or surface: `[Let's work]`, `[Maintenance]`, `[Morning Brief]`, `[Conversion]`, `[Email writer]`, `[Labs]` and so on.

**Bug body:**
```
**What happened:** one line
**Impact:** who is affected and how badly
**Expected:**
**Actual:** (error text verbatim)
**Steps to reproduce**
1. ...
**Where:** plugin <version> (main is <version>) · chat or scheduled task · desktop, web or phone · folder attached or connector · test or real folder
**Reproduced?** seen once by Matthew / seen N times / not yet reproduced
**Acceptance check:** what will be true when this is fixed

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

Chat log rules (Louis's ask): one line per turn, high level. What was typed (verbatim), what Claude did, what it answered, errors verbatim. **No internal reasoning, no long tool output, no file contents.** About 5 to 20 lines. Trim the turns that don't matter.

### 4a. Feature body

```
**Outcome:** what Matthew can do afterwards that he cannot do now
**Why:** the moment it came up (by shape, no names) and what it costs today
**Acceptance check:** how we will know it works (observable steps)
**Priority:** now / next / later, and why
**Not asking for:** limits, so the scope stays small
**Related:** #N

## Build brief
- **Route:** core / labs (Matthew's call)
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

### 4b. Route: suggest one, Matthew decides

Louis agreed (2026-10-04) that Matthew decides what is core and may build either route.
- Suggest **core** for a change in `02_product/`: a script, Maintenance, the cloud view, a contract, a scheduled task, or how an existing cr2 skill behaves or words its answer. A bug is usually core.
- Suggest **labs** for an add-on that only reads the book through cr2's own commands or the cloud view, and writes nothing or only an intake drop for Maintenance to fold.
- Put the suggestion in the confirmation line. Matthew's answer is the route; never file a route he has not confirmed.

## 5. Scrub (always, before anything is posted)

Run the scrub (cr2-scrub, section S below) on the title, body and chat log. Replace every client name, real person, family member, real email, phone, money figure and client folder name with a placeholder (`Contact A`, `<client folder>`, `an amount`), and add one line saying so. A screenshot gets the same treatment: it is attached only after the visible names are covered.

## 6. Confirm, then file

Show Matthew the title plus three lines (what it is, impact or outcome, labels and the suggested route) and ask "File it?". On yes:

```
gh api repos/ChaletteHQ/cr2/issues -f title="<title>" -F body=@<scratch>/issue.md -f "labels[]=enhancement" -f "labels[]=core" -q .html_url
```

Labels: `bug` or `enhancement`, plus the route Matthew confirmed, `core` or `labs`.

- Use REST only. GraphQL (`gh issue create`, `gh pr list`) is blocked in these sessions.
- If `gh` can't reach the repo in a cloud session, attach it with the add_repo tool (`ChaletteHQ`, `cr2`) and retry once.
- If there is no GitHub access at all, save the issue to scratch and give Matthew a prefilled link: `https://github.com/ChaletteHQ/cr2/issues/new?title=<urlencoded>&labels=enhancement&body=<urlencoded>`. If the body is over about 6,000 characters, give the link with the title only and the body to paste.

**Visual bugs** (a widget, page, artifact, layout, anything you judge by looking): also add the `needs evidence` label. Tell Matthew in one line to take a full-window screenshot (Windows: Win+Shift+S, window mode), cover any names, and drag it into the issue. When he says it's attached, remove `needs evidence`.

## 7. Reply

One line: `Filed #N: <title>` with the link, then: "To build it yourself, open the repo in Claude Code and say: build #N. Or leave it for Louis." Add the screenshot line if one is needed. No recap.

## Never

- Never open a branch or pull request from this skill. Building happens in Claude Code with cr2-build, from the issue.
- Never post before the scrub passes.
- Never claim something was reproduced or tested when it was only reported.
- Never file a route Matthew has not confirmed.

## S. The scrub

Use the **cr2-scrub** skill in this plugin: its Step 1 (name list from the book), Step 2 (scan), Step 3 (judge) and, for "scrub the repo", Step 4 (fix). Its script is `cr2-scrub/scripts/scrub_scan.py`. The rule, the allowed list and the placeholders are written there once, so they never drift apart.
