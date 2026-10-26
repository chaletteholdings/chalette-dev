# Team guide: chalette-dev

For Isabella and Erick. About ten minutes to read, fifteen to set up. Written 2026-10-26.

Brand, positioning and copy are not in this guide. They are mid-rebrand and have their own sheet: [POSITIONING_AND_BRAND_SHEET.md](POSITIONING_AND_BRAND_SHEET.md).

## What this repo is

Command Room 1 is built in one repository, `chaletteholdings/cr1`. Every bug and every idea for it lives there as a GitHub issue.

This repository, `chalette-dev`, is the toolkit that lets you work on those issues by talking to Claude instead of using GitHub by hand. Install it once, and in any chat you can say "report this" and a clean issue appears on cr1, or say "what needs me" and get a short test to run.

You do not write code here. You report what you see, test what was fixed, and see what is coming.

## Set up once

1. **GitHub access.** You both have write access on `cr1` and `chalette-dev` (checked 2026-10-26). Isabella also has write on `chalette-website`. If GitHub shows a pending invitation, accept it.
2. **The GitHub command line, signed in as you.** The skills use it to know who you are and to post.
   - Mac: `brew install gh`. Windows: `winget install GitHub.cli`.
   - Then `gh auth login` and follow the prompts.
   - Check: `gh api user --jq .login` prints your own account name.
3. **The plugin.** In the Claude desktop app, open Plugins, add the marketplace `chaletteholdings/chalette-dev`, and turn on `chalette-dev`. In a Claude Code terminal the same thing is `/plugin marketplace add chaletteholdings/chalette-dev`, then `/plugin install chalette-dev@chalette-dev`.
4. **Check it knows you.** Start a new chat and say "what's pending to build". The first line of the reply says who it took you for: "Running as Isabella" or "Running as Erick". If it names someone else, stop and tell it who you are. Your word stands for the rest of that chat.

You do not need to clone this repo or cr1, and you should not create `config/operator.local.json`; that file is Matthew's alone.

## The four things you will say

| Say | What happens |
|---|---|
| "report this", "file a bug", "feature request" | Turns the chat you are in into one issue on cr1: what happened, the exact error, the version, how bad it is. Run it in the chat where the problem happened, so the chat is the evidence. |
| "what needs me", "test #N" | Lists fixes waiting for a test, then gives you a short script: what to type, what a pass looks like, three runs. Your result is posted on the issue. |
| "what's pending to build", "explain #N" | Everything waiting on cr1, sorted by what it is waiting on, each item explained from the client's side. Read this before you describe the product to anyone, so you know what is true today and what is coming. |
| "scrub this" | Checks a piece of text for client names, personal details and money figures before it goes to GitHub. The other three run it for you; run it yourself on anything you write by hand. |

The plugin carries eleven more skills (the battery, the test suites, the skill builders). Those are for whoever builds. You can ignore them, and they must never be pointed at a real client's folder.

## What you decide, and what goes to Matthew

- **You can:** file issues, add evidence to an existing issue, run a test and post the result, and propose how something should be built.
- **Matthew decides:** what gets built, what merges, when an issue is closed, and when a release goes out to clients.
- **So:** anything you file is labelled `question` and signed "Proposed by <your name>, Matthew to confirm." The skills do this for you. Never close an issue; post the result and tag Matthew.

## The rule that cannot slip: no client data in GitHub

Nothing about a client, prospect, partner, family member or any real person outside the team, and no money figure, goes into GitHub. Not in an issue, a comment, a screenshot, a file name or a pasted email.

- Describe a problem by its shape: "a client with three email accounts", never the client's name.
- Never attach a screenshot taken in a real client's folder. Give the exact error text instead, or reproduce it in a test folder.
- The team may be named: Matthew, Erick, Isabella, Claude.
- If you are not sure whether something is sensitive, leave it out and ask Matthew.
- If you find something sensitive already posted, stop and tell Matthew. Do not edit or delete it yourself; removing it from GitHub's history is his decision.

## A good report, a good test

- **Report where it happened.** The chat is the evidence. If it happened elsewhere, say "report this" in that chat, or paste its key turns.
- **Exact words.** The error text as it appeared, and what you typed just before it.
- **Screenshots, when they help:** the whole window, not a crop; move the mouse out of the picture; mark the important spot with a red box; keep an unmarked copy.
- **A test is three runs.** Each in a new chat. Report how many of three passed. "Looks good" is not a pass; a pass is the yes-or-no check in the script.
- **A fix you cannot see yet** is usually not in your version. Most fixes reach the product only when Matthew releases one. The test skill checks this first and tells you.

## Where things live

| What | Where | Who changes it |
|---|---|---|
| The product and every issue | `chaletteholdings/cr1` | Builders, by pull request; Matthew merges |
| This toolkit and this guide | `chaletteholdings/chalette-dev` | One change per pull request; Matthew merges |
| The website | `chaletteholdings/chalette-website` | Isabella proposes by pull request; Matthew merges |
| The brand (colours, type, logo, copy rules) | The Chalette Design System artifact, linked from the brand sheet | See [POSITIONING_AND_BRAND_SHEET.md](POSITIONING_AND_BRAND_SHEET.md) |
| What is decided about positioning and brand right now | [POSITIONING_AND_BRAND_SHEET.md](POSITIONING_AND_BRAND_SHEET.md) | Updated when Matthew rules |

## When something goes wrong

- **"FATAL: operator profile unreadable"**: the GitHub command line is not signed in. Run `gh auth login`, then start a new chat.
- **It cannot see GitHub at all**: you are probably in a web or phone chat with no GitHub connection. Use the desktop app.
- **It took you for the wrong person**: say who you are; it carries on as you.
- **Anything else**: ask Matthew, with the exact words on screen.

## Changing this repo

Rare for either of you, but the rules: one change per pull request, `pytest tests/` passes, the diff scans clean, and this repo's version and CHANGELOG change in the same pull request. Matthew merges. Full rules: [CLAUDE.md](../CLAUDE.md) and [README.md](../README.md).
