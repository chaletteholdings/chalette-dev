---
name: "cr2-scrub"
description: "Use before anything goes to the ChaletteHQ/cr2 GitHub repo, to check text, files or the whole repo for client names, personal information and money figures. Use on 'scrub this', 'scrub the repo', 'privacy check', and before any cr2 issue, comment, PR or commit."
---

# cr2 scrub

The rule (Matthew, 2026-09-29, extended 2026-10-04): **nothing about a client, prospect, partner, family member or any real person, and no money figure, goes into the `ChaletteHQ/cr2` repo.** Not in files, tests, issues, comments, pull requests, commit messages, branch names, chat logs or screenshots. The full text is section 0 of `00_docs/github-issue-discipline.md` in the repo.

Allowed: the team by name (Matthew, Louis/Lewis, Erick, Claude), `dev@chaletteholdings.com`, sample names and `*.example` addresses, version numbers, commit SHAs, issue numbers, sizes and counts that are not money.

Two modes:
- **Check** (default, and what cr2-report and cr2-test call): scan one piece of text before it is posted.
- **Sweep** ("scrub the repo"): scan every branch, issue, PR and comment, then fix what it finds.

## Who is running this

These skills are shared by Matthew and Erick (the chalette-dev plugin). Work out who is running them in this order and stop at the first answer:

1. **The local profile.** `config/operator.local.json` in this plugin, when present: its `operator` wins (`"m"` is Matthew). Only Matthew keeps one, on his own computer.
2. **The GitHub account.** Run `gh api user --jq .login`. `chaletteholdings` is Matthew; `erick559` is Erick; any other account is treated as Erick. Web and phone chats load a fresh copy of the plugin with no local profile, so this is how they know who is there.
3. **The shared default.** `operator` in `config/operator.json` (Erick).

Say who in one line in the first reply ("Running as Matthew, from the GitHub account."), so a wrong guess shows at once. If the person says otherwise, their word stands for the rest of the chat. If none of the three can be read, never assume: say `FATAL: operator profile unreadable` in one line, then ask once, "Matthew or Erick?", and go on with the answer.

- **Matthew (`m`):** everything below as written. He confirms what gets filed and closes an issue on a passing test.
- **Erick (anyone else):** the same steps, with Matthew's decisions turned into proposals. Never close an issue: post the test result and tag Matthew. Never post a build brief as decided; post it as "Proposed by Erick, Matthew to confirm."
- Where the text says "Matthew" as the person you are talking to, talk to whoever is running it. Where it cites a ruling ("Matthew, 2026-10-04"), the ruling stands for both.

## Step 1. Build the name list from the book (every run, never stored)

Client names come from Matthew's own book, so the list is always current and never lives anywhere public.

1. Find the book: the attached folder that holds `_hq/data/entities/` (the operator's own book folder).
   - If this session has the `mcp__remote-devices__` tools (a cloud chat linked to his computer), copy the three files in with `device_stage_files`: `_hq/data/entities/people.*.jsonl.txt`, `orgs.*.jsonl.txt` and `threads.*.jsonl.txt` (list the folder first to get the current part names). They land under `/mnt/user-data/uploads/NEW Penelopes Brain/`.
   - If the folder is mounted directly, use it in place.
   - If neither works, say so, ask Matthew to attach the folder, and in the meantime scan with the fixed checks only (money, emails, phones, secrets, family surnames). Say plainly that the name check did not run.
2. Run the script that ships with this skill, `scripts/scrub_scan.py` (copy it to this session's scratch folder first if the skill folder is read-only; never into the repo or the book folder):
   `python3 scrub_scan.py terms --book "<book root>" > <scratch>/terms.txt`
   It also reads the operator's private extra lists from this plugin's `config/scrub.local.json` when present (family surnames to always flag, first names and words to ignore). That file is gitignored and stays on the operator's own computer; never commit or post it.
3. The terms file is scratch only. Never commit it, never paste it into GitHub, never print the whole list in chat.

## Step 2. Scan

- Check mode: write the text to `<scratch>/post.md` and run `python3 scrub_scan.py scan --terms <scratch>/terms.txt <scratch>/post.md`. Exit 0 means clean.
- Sweep mode: clone or fetch `ChaletteHQ/cr2` with all branches. Dump each live branch's current files (open text for `.docx`/`.xlsx`/`.pptx` from their XML), and all issues, PRs, issue comments and review comments through the REST API (`gh api repos/ChaletteHQ/cr2/issues?state=all&per_page=100&page=N`, `.../issues/comments`, `.../pulls/comments`). Paginate by hand: `--paginate` and GraphQL fail through the session proxy. Scan the lot in one call so the pattern compiles once.

## Step 3. Judge each hit (the script is a net, not a verdict)

- Real client, person, family member, company, client folder name, real email, phone or secret: **must go**.
- Money: any price, rate, revenue, invoice amount or deal size must go. An obviously synthetic amount inside a test fixture (a sample receipt) may stay; say so in one line.
- False positives (a common word that is also a surname, a team member): ignore, and do not argue with the list.
- Also read for what a regex cannot see: a real situation described closely enough to identify a client ("the bus company in Riverside"), a real file name, a quote from a client's email. Replace those with their shape.

Replace with neutral placeholders: `Contact A`, `Client B`, `<client folder>`, `Sample Co`, `an amount`, `owner@sample.example`. Add one line saying a redaction was made.

## Step 4. Fix (sweep mode)

Matthew's ruling (2026-10-04): **current files only. Git history is not rewritten.**
- Files on `main`: one small branch and one PR per item (`fix/scrub-<few-words>`), no version bump ("needs version" for Louis). Run the tests with `CR2_RUNTIME=writer PYTHONUTF8=1 python 03_tests/run_all.py`.
- Files on an open PR's branch: push one scrub commit to that branch and comment asking for a squash-merge, so the old commits never reach `main`.
- Issue bodies and comments: edit in place (`gh api -X PATCH repos/ChaletteHQ/cr2/issues/N -F body=@file`, or `.../issues/comments/ID`) and add `_Redacted <date>: names replaced with placeholders._`. Never delete an issue.
  - **An edit does not erase the old text.** GitHub keeps every earlier version of an issue body or comment under its "edited" marker, readable by anyone who can see the repo. There is no API or `gh` command to remove it. So after editing, list each redacted item with its link and tell the operator to remove the old version by hand: click **edited** on the comment, open the earlier version, then **Options → Delete revision from history**. Only the comment's author or someone with write access can do this; who edited it and when stays visible. Until that is done, the redaction is not finished.
- Commit messages and old commits: report them, do not touch them.
- A credential or token found anywhere: tell Matthew at once so he can rotate it. Fixing the text does not make the secret safe.

**When history might be rewritten (Matthew's decision only, never done by this skill).** GitHub's own guidance:
- A secret: revoke or rotate it first. Once it is dead, rewriting history is usually unnecessary.
- Client information inside a commit: report it to Matthew with the commit and file. If he decides to remove it, the method is `git filter-repo --sensitive-data-removal --replace-text`, a force-push, then a request to GitHub Support to purge cached views and pull request references. Side effects: every later commit ID changes, closed pull request diffs can be lost, and any old clone (Louis's, Erick's) can bring the data back unless it is deleted and re-cloned.

Before fixing, show Matthew the findings in one table (kind, where, what replaces it), then fix on his yes. Report: what was fixed, the PR links, and what was left and why.
