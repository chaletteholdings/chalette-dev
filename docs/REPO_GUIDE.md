# The Chalette repos: a guide for Erick and Isabella

What each repository you can open holds, how it works, how to get the most from it, and where your time helps Matthew most. Written 2026-10-26 against the live repositories. About fifteen minutes to read.

Setting up (GitHub sign-in, the toolkit plugin, the staging plugin `cr`, a test folder, the four phrases) is already covered in [TEAM_GUIDE.md](TEAM_GUIDE.md). This guide does not repeat it. Do that setup first.

**Your jobs, as Matthew set them on 2026-10-26:** test fixes (both of you), keep the Chalette Design System current as the source of truth (both of you), and test the CRM (Isabella). You are not asked to build. Each of you has a step-by-step guide for those jobs, kept in your own Command Room; this page is the map behind it.

The counts below (open issues, tests waiting) are as of 2026-10-26. For today's numbers, say "what's pending to build".

## The map

| Repository | What it is | Erick | Isabella |
|---|---|---|---|
| `chaletteholdings/cr1` | **Command Room**, the product. Every bug and idea lives here as an issue. | write | write |
| `chaletteholdings/chalette-dev` | **Your toolkit.** A plugin that lets you report, test and read cr1 by talking to Claude. | write | write |
| `ChaletteHQ/ChaletteCRM` | **The CRM pilot.** A relationships page over a Command Room folder, used by two people to learn what the product needs. | write | write |
| `ChaletteHQ/chalette-brand` | **The brand tools.** The skill that keeps anything you make on brand, plus the script that spreads a brand change. | write | write |
| `chaletteholdings/chalette-website` | **The live website**, chaletteholdings.com. | none | write |
| Four per-client repos under `ChaletteHQ` | What a client actually runs: a copy of Command Room plus that client's own skills. | read | none |
| `ChaletteHQ/cr2` | The retired second version of Command Room. Archived, read-only. | write (no effect) | none |
| `ChaletteHQ/ADHD` | "Backstage", an early creator edition of Command Room. No changes since June. | maintain | none |

Access was checked on 2026-10-26. If GitHub shows a pending invitation, accept it.

## How the pieces fit

Command Room is built in one place, `cr1`. Its `main` branch is **staging**: a plugin called `cr`, installed from cr1, always follows it, so a fix is testable the moment it merges. Clients never see `main`. When Matthew cuts a release, a script copies the product into each client's private repo under `ChaletteHQ`. That is the only way a change reaches a client, and only Matthew runs it.

`chalette-dev` is the remote control for cr1. You never need to open GitHub by hand: you say "report this" or "what needs me" and the toolkit does the GitHub work, scrubbed of names.

The brand has one source, the Chalette Design System artifact on claude.ai. `chalette-brand` carries the skill that reads it. What is decided about brand and positioning right now is in [POSITIONING_AND_BRAND_SHEET.md](POSITIONING_AND_BRAND_SHEET.md).

The CRM is a pilot. Its product version is being built inside cr1 as the relationships page (cr1 #300 to #306), so the pilot's job is to learn, and anything the product needs ends up as a cr1 issue.

The website is plain web pages. Anything that lands on its `main` branch is live in about thirty seconds.

## Repo by repo

### cr1: the product

**What is inside.** `command-room/` is the plugin itself: 63 skills, the Python engine they call, and the test battery. `SKILLS.md` lists every skill, what it does and what to say to start it. `docs/START_HERE.md` is the front door for anyone reading the code. `ISSUES.md` holds the tracker rules; `CONTRIBUTING.md` holds who does what.

**How work moves.** Report (an issue) → desk (made buildable, Matthew answers the open questions) → build (one issue, one pull request, in Claude Code) → merge (Matthew) → test on the staging `cr` plugin → release and promote to clients (Matthew).

**How to use it best.**

- **Use the staging plugin `cr`, in a test folder only.** The steps are in [TEAM_GUIDE.md](TEAM_GUIDE.md). Never use it in your own work folder or a client's. If you also have the released `command-room` plugin, turn it off while you test, so you know which one answered. Press Update on `cr` and start a new chat before each test.
- **Read `SKILLS.md` once.** It is the fastest way to know what the product does and the exact phrases that start each part.
- **Before you describe the product to anyone,** say "what's pending to build" so you know what is true today and what is still coming.

**Where you help.** Today cr1 has 213 open issues. Two piles are yours to shrink:

- **32 issues labelled `needs UAT`**: fixed and merged, waiting for someone to try them. Say "what needs me".
- **25 issues labelled `needs evidence`**: someone saw a problem but nobody has reproduced it. Try it in a test folder and add what you see, with the exact error text.

**Never:** push to `main`, merge a pull request, close an issue, or put a client name, a real person or a money figure anywhere in the repo. GitHub will show you a Merge button on a green pull request. Do not press it; merging is Matthew's.

### chalette-dev: your toolkit

**What is inside.** The `chalette-dev` plugin: the four skills you use (report, test, what's pending, scrub), eleven builder skills you can ignore, and the documents written for you: [TEAM_GUIDE.md](TEAM_GUIDE.md), [POSITIONING_AND_BRAND_SHEET.md](POSITIONING_AND_BRAND_SHEET.md) and this guide.

**How it works.** The plugin uses the GitHub command line signed in as you, so everything you post is under your own name. It labels what you file `question` and signs it "Proposed by <your name>, Matthew to confirm."

**How to use it best.**

| Say | What happens |
|---|---|
| "report this" | The chat you are in becomes one clean cr1 issue. Say it in the chat where the problem happened; the chat is the evidence. |
| "what needs me" / "test #N" | A short test script: what to type, what a pass looks like, three runs in fresh chats. Your result is posted on the issue. |
| "what's pending to build" / "explain #N" | Everything waiting on cr1, explained from the client's side. |
| "scrub this" | Checks text for names, personal details and money before it goes to GitHub. |

**After a test.** Picking a fix to test puts your name on it. A pass moves it from `needs UAT` to `ready to close`; Claude then checks your evidence in Matthew's chat, and only Matthew closes it. The full sequence is "What happens after your test" in [TEAM_GUIDE.md](TEAM_GUIDE.md).

**A good test:** three runs, each in a new chat, the build you tested named, the exact words on screen quoted or a screenshot per check. "Looks good" is not a pass.

### ChaletteCRM: the relationships pilot

**What is inside.** A Claude plugin (`chalette-crm`) with three skills: "set up my CRM", "refresh my CRM", "schedule my CRM refresh". It publishes a private CRM page you can open on desktop or phone. A local desktop version sits beside it as an alternative. Code only: no contact, mail or client data is ever committed; names live in a `config.json` on each machine.

**How it works.** The page shows people, how warm each relationship is, what is owed both ways and who introduced whom. Changes you make on the page wait until **Save now** (desktop app) or "refresh my CRM" writes them into your Command Room folder through Command Room's own writers. Two people share through one OneDrive folder: nothing moves until one presses Share and the other presses Accept.

**How to use it best.** The README in the repo is the install guide, with a checklist for the second person. You need Python 3.11 or newer on your machine, available as `python`. The **Feedback** button on the page is the quickest way to say what works and what does not.

**Where you help.** Isabella tests it, on her own real work; Erick does not need to. Run the checklist in your step-by-step guide, retest each fix when its issue says it landed, and keep the Feedback button busy. A bug in the pilot goes on ChaletteCRM; anything the finished product should do goes to cr1 with "report this".

**Never:** test it against a client's folder, or paste a real name, address or email into an issue or a commit.

### chalette-brand: the brand tools

**What is inside.** The `chalette-brand` skill, and `sync_brand.py`, the script that copies a brand change from the design system into Matthew's workspace and the product.

**How it works.** The source of truth is the Chalette Design System artifact on the team account (https://claude.ai/artifact/Eruzdf8JqM5UWsmkSuzjqi): the brand book, colours, type, logo and copy rules. This repo copies none of those values; it only reads them.

**How to use it best.** Install the plugin (Plugins → add marketplace `ChaletteHQ/chalette-brand` → turn on `chalette-brand`). From then on, any Claude session that touches Chalette or Command Room loads it and makes things on brand without you asking. In claude.ai chat without plugins, upload the skill folder in Settings instead.

**Where you help.** Brand and positioning are mid-rebrand. Before you draft anything public, check its row in [POSITIONING_AND_BRAND_SHEET.md](POSITIONING_AND_BRAND_SHEET.md): each row is Ruled, Working, Open or Retired. Nothing goes public on an Open row.

**Keeping the design system current is your job.** When Matthew rules something the design system does not say yet, you put it in: the `chalette-brand` skill shows you the exact before and after, you say yes, and it stamps your name. Then send Matthew the summary so his machine carries it into the product. Anything he has not ruled goes to him as a proposal first. The steps are in your step-by-step guide.

**Never:** change the brand in this repo (a change here changes tooling, not the brand), or run `sync_brand.py`. It runs once per change on Matthew's machine and OneDrive spreads the result.

### chalette-website (Isabella)

**What is inside.** Eight plain web pages (Home, The Product, The Service, Results, About, Security, Partners, Book), the link-preview image, and older sample PDFs kept so old links still work.

**How it works.** Anything merged into `main` is live on chaletteholdings.com in about thirty seconds. `main` is protected (since 2026-10-26): GitHub refuses a direct push from anyone, so every change goes through a pull request and Matthew merges.

**How to use it best.**

- Edit the pages in the repo itself. The README says the source is a build script in the "Chalette Rebrand" folder; that script no longer exists, and the pages in the repo are the source.
- Preview before proposing: in the repo folder run `python -m http.server 8000` and open http://localhost:8000.
- Copy follows the design system README and the brand sheet: "owners" and "business people", never "operator"; no prices; the guarantee is exactly "We guarantee value."; no exclamation marks.

**Where you help.** Turn brand-sheet rows that are Ruled or Working into page changes, one change per pull request, with a screenshot of the preview. Matthew merges, which is the moment it goes live.

**Never:** add a client name, a quote or a figure without Matthew's written yes.

### Erick only: the client repos, cr2 and Backstage

- **The four client repos (read).** Each is what one client runs: a copy of Command Room at their release, plus a folder of that client's own skills. Use them to check which version a client has, or to read their custom skills before a working session. They are written by Matthew's release script, so nobody edits them by hand, and nothing from them (names, skill content, folder names) goes into a cr1 issue.
- **cr2 (archived).** The retired second version. Read-only for everyone; nothing to do there. Build, test and file against cr1 only.
- **Backstage (`ADHD`, maintain).** An early creator edition, untouched since June. Ask Matthew before spending any time on it.

## Where your time helps most, in order

1. **Clear the test queue.** "what needs me" with `cr` in a test folder. 32 fixes were waiting on 2026-10-26, and until now Matthew has been the only tester. When there is time left, reproduce the `needs evidence` issues (25 on 2026-10-26) with the exact error text.
2. **Keep the design system current.** Every ruling Matthew makes about the brand, positioning or copy goes into the design system the same day.
3. **Test the CRM (Isabella).** The checklist, then each fix as it lands.

Along the way, report what you hit in real use from the chat where it happened. Website pull requests (Isabella) come after these three.

## What stays with Matthew

What gets built, what merges, when an issue closes, when a release goes to clients, and every brand or positioning ruling. You propose; he decides. When you are unsure which side of that line something sits on, ask him with the exact words on screen.

## The one rule that never bends

Nothing about a client, a prospect, a partner, a family member or any real person outside the team, and no money figure, goes into any of these repositories: not in an issue, a comment, a pull request, a commit, a file name or a screenshot. Describe a problem by its shape ("a client with three email accounts"). Never attach a screenshot from a real client's folder; reproduce it in a test folder or give the exact error text. The team may be named: Matthew, Erick, Isabella, Claude. If you find something sensitive already posted, stop and tell Matthew; do not edit or delete it yourself.
