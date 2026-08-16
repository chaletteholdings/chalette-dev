---
name: triage-intake
description: "Process the intake queue — verify each captured bug against the cr1 clone, feasibility-check each idea/skill for trigger collisions and overlap, sweep for same-class sites, then write a build spec (SPEC_*.md) or surface a kill/park recommendation, and move each file to its status folder. Companion to capture-for-code: capture writes items the moment they're spotted; triage-intake verifies and specs them with the repo open. Use when the operator says: 'triage intake', 'triage the intake', 'process intake', 'process the intake queue', 'what's in intake', 'run intake triage', 'work the queue', 'triage the queue'. DOES NOT fire on 'bug intake' / 'process bug report' / customer-inbound reports. DOES NOT build or fix code — output is specs and decisions; builds happen in fresh sessions from the spec. DOES NOT fire on 'triage my inbox' or 'commitment triage' (Command Room product skills)."
---

# triage-intake

The verify half of the intake pair. Sibling of `capture-for-code`. Turns raw captures into either a build-ready `SPEC_*.md` or an honest "don't build this" — never leaves an item in limbo silently.

> **Operator-aware.** Read `config/operator.json`, then overlay `config/operator.local.json` per-key if present (gitignored; the operator's local overlay — M keeps one for his real paths; not every operator has one). Keys used: `intake_root` (queue location, default `~/cr-intake`), `cr1_clone` (the repo to verify against), `chalette_clone` (a chalette030 clone, when the item targets the chalette plugin; not every operator has one), `specs_dir` (where specs land; default `<intake_root>/specs/`), `parking_doc` (PARK target; default `<intake_root>/PARKING.md`), `scrub_roster` (grep source for the outbound scrub gate; **null = outbound packet/BACKLOG emission disabled**, see "Routing work out"), `allowed_targets`, `may_ship`, `may_build_own_spec`. **Non-M operators verify against synthetic fixtures ONLY** (`skills/synthetic-workspace-runtime-test/fixtures/`) — never a real workspace. **The two authority keys are independent, and conflating them is the bug this split fixed.** `may_ship: false` means no version bump, no CHANGELOG entry, no release, no promote, no merging your own PR — unchanged, and it binds regardless of anything below. `may_build_own_spec: true` — **the shipped default, on purpose** — means the spec THIS session writes may be built by this same operator directly, in one pass, with review happening at the pull request; `may_build_own_spec: false` (only if an overlay turns it off) keeps the old pre-build handoff — the spec goes to M and someone else decides it becomes a build.
> ```python
> import json, os, sys
> op = {}
> for _n in ("operator.json", "operator.local.json"):
>     _p = os.path.join(SKILL_PLUGIN_ROOT, "config", _n)
>     if os.path.exists(_p): op.update(json.load(open(_p)))
> # SKILL_PLUGIN_ROOT must be a NATIVE path — on Windows `C:/Users/…`, never an MSYS
> # `/c/Users/…` (convert with `cygpath -m`): python.exe reads `/c/…` as `C:\c\…`, both
> # files miss, and an empty profile silently becomes the default. Fail loud instead.
> if not op: sys.exit(f"FATAL: operator profile unreadable under {SKILL_PLUGIN_ROOT}")
> ```

## What this is and is not

**Is:** a batch triage that, per item: locates the code, verifies or refutes the capture against the actual repo, sweeps for the same class of problem elsewhere, sizes it, writes a spec sized to the item, and ends with a one-screen decision table. File moves = the record.

**Is not:** a fix session. Even a one-line fix gets recommended, not applied — the fix happens in a normal build session (or lands as its own PR after a ruling). Not the customer-bug triage either.

## Preflight (every run)

1. **Sync the clone**: `git -C <cr1_clone> pull` — never triage against a stale tree. **INTAKE1 F4 (operator-aware):** if an item targets the chalette plugin AND `chalette_clone` is set in the merged profile, also `git -C <chalette_clone> pull` before verifying that item (only M has a chalette clone; contractors skip this).
2. List `<intake_root>/new/`. **Resurrection guard (INTAKE1 F5):** before triaging, cross-check each `new/` filename against `speced/`, `killed/`, and `done/` — an exact match means a multi-machine sync re-added an item triage already moved out of `new/`; delete-or-skip it, never re-triage. If empty: check `needs-input/` for items since answered (a ruling note appended below the questions = answered), report the queue state in two lines, done.
3. **Stale check**: items in `new/` older than 30 days go on the decision table with a kill-or-keep prompt.
4. If >5 items, state the count and confirm batch order (severity first, then oldest) — or take a subset.

## Per-item flow — BUG

1. **Read the capture. Treat `## Hypothesis (UNVERIFIED)` as a lead, never a fact.** Re-derive root cause from the repo even when the hypothesis looks right.
2. **Locate** the code path: grep skill texts AND runtime scripts — prose-only behavior won't show in `.py`; instruction-layer bugs live in SKILL.md text. Re-verify any "X doesn't exist" conclusion with a second search strategy before writing it down.
3. **Verify — graduated, cheapest sufficient level, then STOP:**
   - **L1 read-trace:** read the code path; a defect provable by reading (wrong constant, missing branch, stale string) is confirmed at L1.
   - **L2 test slice:** run the relevant existing test file(s), not the full battery.
   - **L3 fixture repro:** reproduce against the synthetic fixtures (reuse `synthetic-workspace-runtime-test` machinery) — only for behavior L1/L2 can't prove. Synthetic fixtures ONLY unless `allowed_targets` includes `real`.
   - Cosmetic/label-level items never go past L1.
4. **Same-class sweep:** grep the anti-pattern fleet-wide. The sweep count drives fix scope: surgical vs sweep vs structural.
5. **History check:** the bug-regression-suite catalog + last 5 CHANGELOG entries — regression of a known fix, or a known-issue pattern?
6. **Verdict** (always explicit):
   - `CONFIRMED` — root cause at file:line + blast radius → bug-fix spec (or "trivial — fix inline, no spec" for a provable one-liner with an obvious regression test).
   - `COULD-NOT-REPRODUCE` — first-class outcome, never silently dropped: record what was tried at which level, write 1-3 questions into the file, move to `needs-input/`.
   - `NOT-A-BUG` — working as designed: cite the design decision or spec that pins the behavior. M can overrule.

## Per-item flow — IDEA / SKILL

1. **Trigger-collision check:** would the imagined trigger phrases route to an existing skill? Grep skill frontmatter descriptions across the plugin — routing runs on descriptions only.
2. **Overlap check:** ≥80% of an existing skill → recommend "extend X", not a new build; say which sections of X change.
3. **Touch-surface inventory:** files/skills/substrate touched; new event types must register in `events.schema.json` + `EVENT_TYPES.md` with a named consumer.
4. **Score `ease`** (1-5) in the frontmatter; ICE = impact × confidence × ease is a sort key for attention, never a verdict.
5. **Verdict:** `SPEC` / `PARK` (real but not now — append a one-paragraph entry to `parking_doc` from the merged profile, default `<intake_root>/PARKING.md`; M's overlay points it at his `FUTURE_WORK.md`; then file to `killed/` with a pointer) / `KILL` (with the honest reason).

## Writing the spec

Templates in `references/spec-templates.md` — two sizes, pick by item, never inflate: **bug-fix spec** ≤1 page, **feature/skill spec** ≤3 pages with a §0 open-decisions table where every genuine fork gets a **recommended default** (flag ambiguity, never silently guess; blocking decisions marked `AWAIT ruling — DO NOT BUILD`).

Specs land in the merged `specs_dir` (default `<intake_root>/specs/`; M's overlay points it at his `build-specs/` folder), named `SPEC_<TAG>_<snake_name>.md` (fresh TAG — check for collisions). **Delivery is `may_build_own_spec`-gated** (NOT `may_ship` — that conflation was the bug GATE1 fixed): when the merged profile has **`may_build_own_spec: true`, or `may_ship: true`** (a ship operator may always build their own spec), the spec lands directly in `specs_dir` ready to build, **regardless of `may_ship`** — the build proceeds in a normal build session and **the pull request is the review point**, so do not ask anyone to approve the spec first. Building from your own spec does **not** grant ship authority: the `may_ship` rules in the Writer contract still bind in full (no version bump, no CHANGELOG, no promote, no self-merge). When `may_build_own_spec: false` and `may_ship: false`, attach the spec to the related cr1 PR or hand it over in your normal channel — contractors never self-approve a spec into a build. Then rewrite the intake file to a pointer ("superseded by SPEC_XXX — <date>") and move it to `speced/`.

Spec hygiene: reference files by path, never inline code the builder can read; a section that restates what any Claude already knows gets cut.

## Routing work out — Eric packet + BACKLOG (`may_ship` operators only)

Everything in this section is gated on the merged profile having **`may_ship: true`**. On a contractor profile it is inert: delivery stays exactly as "Writing the spec" describes (attach to the PR / hand over), no packet is written, `BACKLOG.md` is never touched. A contractor does not route work to themselves.

**Eric-suitability test — applied at verdict time, ALL clauses must hold:**

1. Target repo is `cr1_clone` (never the chalette plugin, never the workspace).
2. The fix is process/code-shaped and fully specifiable from repo contents alone.
3. Buildable AND testable against the battery + synthetic fixtures alone — no real-workspace verification step.
4. Zero client/org/person names needed in spec, code, tests, or PR text.
5. Zero ship authority: no version bump, no CHANGELOG, no promote, no client-repo contact.

Any "no" → normal M-side spec into `specs_dir`, **no packet, no BACKLOG row**. Record yes/no per SPEC-verdict item in the decision table's `Eric?` column.

**Scrub gate — fail-closed, runs BEFORE either write.** Read `scrub_roster` from the merged profile and grep the full outbound text (packet body AND the BACKLOG row) against every client/org/person name in it. This does not ride cr1's G9 alone: G9's first-name dictionary cannot know real ORG names, which is exactly how org names have leaked past a name guard before.

- `scrub_roster` null, missing, unreadable, or **readable but yielding zero names** → **refuse both outbound writes** with the explicit line `scrub roster unavailable — BACKLOG/packet emission disabled`, and still deliver the normal M-side spec. An empty or truncated roster is an unavailable roster, never an all-clear. Never proceed on an unverified roster. Grep **individual name tokens as well as full names, case-insensitive** — a bare first name or a possessive form is a hit.
- Roster hit → block the write, surface the offending line for rewrite. **Never auto-substitute a name.**
- Phrase items by mechanism, never by origin: "stale-baseline drift in X guard", not the client or workspace context that surfaced it.

**Packet — one file, `<specs_dir>/packets/PACKET_<TAG>.md`, self-contained for a cold fork contributor.** Never committed into cr1 (filled records stay out of the repo — G12). Structure in `references/spec-templates.md`; contents: handoff header (repo + fork→branch→PR per cr1 `CONTRIBUTING.md`, what the builder never does, the BACKLOG row TAG), the spec body shaped per cr1 `templates/TEMPLATE_SPEC.md` with §0 **already ruled** (a packet never ships with open AWAIT rows — a genuine surviving fork means the item is not packet-ready), the kickoff prompt, acceptance criteria including the scrub AC verbatim, and the PR-description-requirements block. Self-containment rule: no workspace paths (the operator's workspace folder name included), no chalette-plugin references, no operator-overlay values anywhere in packet text.

**BACKLOG.md — `<cr1_clone>/BACKLOG.md`, repo root.** One row per emitted packet: `TAG · outcome (one line) · size (S/M/L) · status (READY / CLAIMED — PR # / MERGED @ short-SHA)`. Shape + covenant header: `references/spec-templates.md`.

- **Stage-and-show, always:** `git -C <cr1_clone> add BACKLOG.md`, show the staged diff in the closing decision table, **STOP**. No `git commit`, no `git push`, ever, from a triage session — a triage session ends with zero new commits in `<cr1_clone>`. M commits it in his own ship window.
- **Reconcile on every `may_ship` run** (closing batch): check rows against `git log` (merged PRs) and `done/` moves — flip statuses, and delete `MERGED` rows after one run of visibility. History lives in git; the file stays a one-screen board, not a ledger. Reconciliation edits use the same stage-and-show posture.

## Closing the batch — the decision table

End with ONE screen:

| Item | Type | Verdict | ICE / Sev | Eric? | Recommendation | Open decisions |
|---|---|---|---|---|---|---|

`Eric?` — yes/no per SPEC-verdict item from the suitability test above (`n/a` for non-SPEC verdicts, `—` on a contractor profile). When a packet was emitted, the staged `BACKLOG.md` diff goes under the table.

Apply rulings: move files (`new/` → `speced/` / `needs-input/` / `killed/`), append rulings into the files. Unruled items stay in `new/` untouched — never assume.

## Writer contract

- Moves files OUT of `new/` (single-writer rule: capture writes `new/`, triage owns everything downstream). Never writes into `new/`.
- `done/` moves happen when the fix/feature ships, not during triage.
- **Outbound surfaces — exactly two, `may_ship` only, both post-scrub:** `<specs_dir>/packets/PACKET_*.md` (workspace-side) and `<cr1_clone>/BACKLOG.md` (repo-root file — **staged via `git add`, never committed, never pushed**). **No other file in any repo is ever written by triage.**
- No substrate events, no version/CHANGELOG bumps, no commits/pushes unless asked. Ship/promote stays with M (`may_ship` in operator.json).
