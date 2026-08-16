---
name: demo-prospect-workspace
description: "Build a clearly-marked demo workspace for a sales prospect under the Demos folder, expiring after 7 days. Fires on: 'build a demo workspace for [company]', 'demo prospect workspace for [company], meeting [name], [role]', 'rebuild the [company] demo'. Manual only — never fires from the calendar. Does NOT fire on 'prep me for [meeting]' (call-prep), 'research [company]' (research), 'set up command room' (command-room-onboarding), or 'ingest [source]' (workspace-ingest)."
---

## Recommended Model

**Default: Opus.** One run mixes real-world research judgment (what is true and public about this company), synthesis judgment (operating data that reads plausible for how this business actually runs), and a safety contract (every synthesized record visibly marked). A prospect reads the result live on a sales call — bad synthesis or a missing marker costs the deal or the trust.

---

## Names are generation input — entity resolve deliberately not used

The trigger names a company and a person, but this skill performs NO lookup against any existing workspace: the names seed what gets *generated*, and sibling folders under Demos/ are explicitly out of bounds (only their demo provenance file may be read — Step 2). Because no substrate query depends on a resolved entity, Command Room's `entity_resolve.resolve_all` is not invoked; its ENTITY_RESOLVE_PROTOCOL in the command-room payload says when that contract does apply. If this skill ever grows a read against real workspace data, that is a redesign, not a patch.

## Skill Boundary (v2.1)

- **Use demo-prospect-workspace for:** building a self-contained, clearly-marked, 7-day-expiring demo workspace for a named prospect company under a Demos/ folder, so a sales call can walk through "their" Command Room morning.
- **Use `call-prep` for:** a brief before a real meeting that exists on the calendar. call-prep reads real workspace context; nothing is built.
- **Use `research` for:** a cited research brief on a company or topic, saved into the real workspace. This skill RUNS the same kind of public research as its first layer, but its output is a demo folder, not a brief.
- **Use `command-room-onboarding` for:** first-install setup of a real customer workspace from their real connected sources.
- **Use `workspace-ingest` for:** pulling real documents and context into the real workspace.
- **Use `command-room-coach` for:** showing an existing customer around their own workspace ("show me around", "what can you do for me").

## Writer Contract

- **Writes ONLY under `Demos/<prospect folder>/`** — never to the operator's own workspace, never to any sibling demo folder. Everything it creates lives inside the one prospect folder it is building:
  - `_hq/data/entities.json` — people, projects, the one prospect org, and the workspace brand block
  - `_hq/data/events.jsonl` — the synthesized three-week operating history
  - `_hq/data/aliases.json` — first-name and short-name mappings for the synthesized entities
  - `_hq/data/demo_manifest.json` — the demo provenance record (generator id, created, expires, marker convention)
  - `_hq/BUSINESS_CONTEXT.md` — the Layer 1 research landing place: true, publicly sourced company background, UNMARKED because it is the true layer, written from the prospect's point of view (same name and location `command-room-onboarding` gives a real workspace's business context)
  - `CLAUDE.md` at the folder root — session rules for any chat opened on this workspace
- **Reads:** public web (and research connectors when connected) for Layer 1; from sibling folders under Demos/, ONLY each folder's `_hq/data/demo_manifest.json` (Step 2), never their content.
- **Deletes:** only sibling demo folders whose own manifest says this generator built them AND whose expiry date has passed (Step 2); the same prospect's existing folder on an operator-confirmed rebuild, and ONLY if that folder's own manifest carries `generator: "demo-prospect-workspace"` (Step 3 — a name-match without that manifest is never deleted); and its own partial build on a mid-build failure (Step 4).
- **Atomic-write enforcement:** every data file is written through the shared atomic helpers — `atomic_write_json` for the JSON files, `atomic_append_jsonl` for the event lines (the append path runs the standard event checks). No hand-rolled writes anywhere, ever.
- **No new event types:** every synthesized event uses a canonical, already-registered type (`meeting`, `interaction`, `commitment`, `decision`, `note`) with `source_skill: "demo-prospect-workspace"` stamped on each line.

## What It Doesn't Do

- Does NOT watch the calendar. No auto-detection of upcoming sales calls — it fires only when asked, in plain language.
- Does NOT produce run sheets, demo scripts, or demo playbooks — the deliverable is the workspace folder itself.
- Does NOT build per-prospect visual identity beyond exactly two brand values (one accent color + the fixed demo footer line). No logos, no fonts, no themes.
- Does NOT generate from Claude Code or any headless path — this is a Cowork skill, run in a live session with the operator watching.
- Does NOT read anything outside the Demos/ directory — not the operator's workspace, not real client data, not sibling demo folders' content.
- Does NOT invent facts about the real company or real people. True things come from research and are labeled by their source; everything invented is operating data that carries a demo marker in its visible text.
- Does NOT touch the operator's own data files — the generated workspace has its own, and they never mix.

## Do not rationalize past these

A baseline run of this exact task with no skill produced an unmarked fake workspace: fabricated revenue figures, decisions, and quotes attributed by name to the real CEO the operator was about to meet, with zero disclosure in any file. These are the excuses that run produced, verbatim in spirit — do not reuse them:

| The rule | The excuse that will show up | Why the excuse is wrong |
|---|---|---|
| Every synthesized record carries its demo marker in the VISIBLE text | "The user said make it look like her company's workspace — a visible demo label defeats the purpose" | The marked workspace IS the product being demoed: honest provenance rendered everywhere is what lets a prospect trust what they're seeing. Realism without disclosure is a fabricated record about a real company, sitting in front of the person it names. |
| Only research-sourced facts may be unmarked | "The framing is fictional, so I can invent freely" | The company and the person on the call are real. An invented revenue figure or decision with their name on it reads as a claim about them. Fiction is only safe inside the marker convention. |
| The manifest is mandatory | "The files are obviously a demo, nobody needs a provenance record" | Nothing else distinguishes seeded data from captured data, and the expiry sweep (Step 2) can only ever clean up folders that carry the manifest. An unmanifested demo folder is immortal and unlabeled. |
| Fixed volume; no extra surfaces | "More surfaces make a better demo — add financials, transcripts, a tracker" | Fabricated financial statements for a real company are exactly the artifact that cannot exist, marked or not. The volume contract is the tested, known-to-render shape. |
| Stop means stop (Steps 1–4) | "The check failed but the build is probably fine — keep going" | A demo workspace written into a real workspace root, over a twin, or half-built looks like corruption or deception to whoever finds it. Say what failed, plainly, and stop. |

## How to Use

```
build a demo workspace for acmeco.example.com
demo prospect workspace for Acme Co, meeting Sam Sample, COO
demo workspace for Acme Co
spin up a demo workspace for acmeco.example.com — call is Friday
build me a prospect demo for Acme Co
rebuild the Acme Co demo workspace
```

**Inputs:** a company URL (or company name), plus — optional — the name and role of the person who will be on the call. If the name or role is missing, build the workspace for a generic operator in that seat (role given, no name: a synthesized, marked person carries that role; neither given: the seat defaults to CEO). Never block to ask for the missing name — the generic-seat build is the designed fallback.

## How It Works

### Step 0 — Build the checklist (do this first, before any other step)

Create a TodoWrite checklist of all 9 steps of this skill before starting (Step 0b resolves the Command Room payload and can STOP the run). Mark a step complete ONLY after its output actually exists (the folder is checked, the sweep report is written, the file is on disk) — never on intent. A step that is not in the list cannot be silently skipped; a step marked done without its artifact is the failure this checklist exists to catch.

### Step 0b — Resolve the Command Room payload (this skill lives in chalette-dev)

This skill is a chalette-dev (internal) skill that calls TWO Command Room helpers: `workspace_root.py::find_workspace_root` (Step 1's guard) and `commitment_state.py::commitment_counts` (Step 8's self-verify). They are not vendored here on purpose — a second copy drifts from the real one, which is the failure class shared helpers exist to prevent. Resolve the payload once, up front, and **never hardcode a machine path**:

```bash
# Native paths only: an MSYS `/c/Users/…` resolves to a phantom `C:\c\Users\…`
# under Windows python and fails SILENTLY.
_cr_native() { if command -v cygpath >/dev/null 2>&1; then cygpath -m "$1"; else printf '%s\n' "$1"; fi; }
CR_PAYLOAD=""
for _c in "${CR1_CLONE:-}" "$(python3 -c "import json,os,sys;
p=os.path.expanduser('~/repos/chalette-dev/chalette-dev/config/operator.json')
print(json.load(open(p)).get('cr1_clone','') if os.path.isfile(p) else '')" 2>/dev/null)" \
          ~/repos/cr1-canonical ~/.claude/plugins/marketplaces/*/command-room/..; do
  [ -n "$_c" ] || continue
  for _p in "$_c/command-room" "$_c"; do
    [ -f "$_p/shared/scripts/workspace_root.py" ] && CR_PAYLOAD="$(_cr_native "$_p")" && break 2
  done
done
[ -n "$CR_PAYLOAD" ] || { echo "FATAL: Command Room payload not found. Set CR1_CLONE=<path to the cr1 clone or an installed command-room plugin> and re-run." >&2; exit 1; }
```

Both helper calls below run with `sys.path` pointed at `$CR_PAYLOAD/shared/scripts`. If the payload cannot be resolved, STOP — do not fall back to a hand-rolled reimplementation of either helper. A demo workspace built without the real counter is a demo workspace whose numbers are unverified.

### Step 1 — Confirm you are pointed at a Demos/ directory

The current root must be a demos area, not a real workspace:

- **Nested-Demos guard — check this before anything else.** Run `find_workspace_root` from `$CR_PAYLOAD/shared/scripts/workspace_root.py` (Step 0) on the Demos/ directory itself. If it resolves at all — the Demos/ folder or ANY ancestor above it carries the `_hq/data/` workspace anchor — STOP and tell the operator: Demos/ must sit BESIDE the real workspace, never inside it. The real workspace's cleanup and deliverable sweep walk every subfolder beneath their root, so a Demos/ nested inside one would have its generated session notes and documents surface in the real cleanup and sweep as if they were real work.
- The folder (or the folder the operator pointed at) should be a `Demos/` directory — a container of demo workspaces, not a workspace itself.
- If the current root IS a workspace root (it has its own `_hq/data/` anchor files at the top level), or its contents are recognizably real client data, say so plainly — one sentence naming what you found — and STOP. Do not offer to build anyway, do not build in a subfolder as a compromise.

### Step 2 — Expiry sweep (manifest-only reads)

For each sibling folder directly under Demos/:

- Read ONLY `_hq/data/demo_manifest.json` inside it. If that file is absent, the folder is not yours to touch — skip it entirely and read nothing else from it. If the file exists but cannot be parsed, treat the folder the same way — NOT yours, never deleted, skipped — and name it in the sweep report as skipped for a corrupt manifest.
- If the manifest carries `generator: "demo-prospect-workspace"` AND its `expires` date is in the past, delete that folder.
- Report the sweep in one line, plain English: what was removed (folder names) or that nothing was expired. Sibling folders' content beyond the manifest is out of bounds in every case.

### Step 3 — Same-prospect check

If a folder for this company already exists under Demos/ (match on the prospect name in its manifest, or an obvious folder-name match), ask the operator: rebuild it fresh, or keep it as is? Rebuild means delete the existing folder, then continue — **but a rebuild may delete that folder ONLY if the folder's own `_hq/data/demo_manifest.json` carries `generator: "demo-prospect-workspace"`.** A folder that matches the company by name but lacks that manifest (or whose manifest names a different generator, or cannot be parsed) is never deleted, operator consent or not — it is not provably this skill's work. Stop and report it: name the folder, say it matches the prospect but carries no provenance from this generator, and leave it untouched. Keep means stop here with a one-line pointer to the existing folder. NEVER create a second folder for the same prospect — no suffixes, no "v2", no twins.

### Step 4 — Write probe

Create `Demos/<prospect folder>/` (folder named with the company's proper name) and write one small probe file inside it. If either write fails, say so plainly and STOP — never half-build. Remove the probe file once the check passes. If any later write fails mid-build, delete the partial prospect folder and say what happened: a half-built workspace that looks whole is worse than none.

### Step 5 — Layer 1: research (true data, no markers)

Public research on the company: market, service lines, size and footprint, recent public signal, and a read on the named person and their role. Rules:

- **Source tiering, per the workspace research rule:** if a research connector is connected (Vibe Prospecting for structured company data, Tavily for deeper web), use it FIRST; built-in web search is the fallback floor. State which tier actually ran, in one line of the final report.
- Everything in this layer is true and publicly sourced. It carries NO illustrative marker — that is what distinguishes it from Layer 2.
- Where research comes back thin, leave it thin. Never pad the true layer with invented "facts" about the real company — invention belongs only in Layer 2, behind the marker.
- Keep a working note of real employee names the research surfaced: Step 6 must avoid every one of them when inventing people.
- **The research lands in `_hq/BUSINESS_CONTEXT.md`** inside the prospect folder — the durable home of this layer, written from the prospect's point of view, mirroring the business-context file `command-room-onboarding` writes for a real workspace. Like everything else in this layer it is true, publicly sourced, and carries NO marker. A thin research pass makes a thin file, never a padded one.

### Step 6 — Layer 2: synthesis (marked data, fixed volume)

Synthesize plausible operating data consistent with what Layer 1 found about how this business runs — their projects, their meeting rhythm, their open promises. This is the prospect's workspace: every record is written from their point of view, their morning, never the operator's.

**Fixed volume** (tune only if a surface demonstrably renders wrong, and then minimally):

- roughly 10 people (8–12), one of whom is the primary user
- exactly 4 projects
- about 3 weeks of meetings and message activity: at least 20 events spanning 14–28 days, all dated on or before the manifest's `reference_date` (today, the build date), with the most recent event inside the last 7 days of it
- exactly 8 OPEN commitments

**Marker convention — exactly this, no variants:**

- Every rendered text field of every event starts with the prefix `[DEMO] ` — meeting titles and summaries, decision text and rationale, commitment titles, interaction summaries, note text.
- Every project's `display_name` and `next_step` start with `[DEMO] `.
- Every INVENTED person's `canonical_name` ends with the suffix ` (Demo)` — a suffix, not a prefix, so names stay sortable and read naturally mid-sentence while still carrying the marker wherever the name shows. Each person also gets their bare first name as an alias.
- The prospect org itself is UNMARKED — it is the real company. Its disclosure lives in the footer line, the workspace CLAUDE.md, and the manifest, not in its name.
- The named person from the trigger takes the primary-user seat with their real name, UNMARKED — they render clean exactly as the org does, because both are true data. Their disclosure is carried by their synthesized items (every one `[DEMO] `-prefixed), the document footer, the workspace CLAUDE.md, and the manifest, which names them via `primary_person_id` and states `primary_is_real_person: true`. No name given: the generic seat is invented like any other synthetic person, so it KEEPS the ` (Demo)` suffix and the manifest states `primary_is_real_person: false`.

**Name and email safety:**

- Invented people must not share a name with any real person Layer 1 surfaced. If a generated name collides, change it. The placeholder roster the reference fixture uses (first names like Sam, Rio, Mira, Aria with surnames Sample or Stone) is the always-safe fallback.
- Every synthesized email lands on an RFC 2606 example domain, styled like the company (for Acme Co: `sam@acmeco.example.com`). Never fabricate an address on the company's real domain.
- Never name a third-party company or person in synthesized text. Counterparts stay generic — "the two pilot retailers", "the routing vendor" — because a named fake client of a real company is a fabricated business relationship.

**Record shapes** — match the reference fixture at `command-room/tests/fixtures/demo_prospect_workspace/` and the shared data schemas exactly:

- `entities.json`: top-level `version`, `last_updated`, `last_writer: "demo-prospect-workspace"`, a `workspace` block carrying `first_name` (the primary user's first name), `user_timezone` (the company's home timezone from research), `primary_user_id`, and the `brand` block (below) — then `entities` with `people`, `projects` (the canonical inner key), and exactly one org: the prospect, `is_primary_focus: true`, `status: "active"`, its real public domain in `domains`, and a note stating every operating record around it is synthesized.
- Every project carries the `folder_name` key (null is fine) alongside `display_name`, `kind`, `org_id`, `status: "active"`, an owner and stakeholders from the synthesized people, and a `next_step`.
- `events.jsonl`: one JSON object per line in the current event shape — `seq` (monotonic from 1), `ts` (ISO, no timezone suffix), `type`, `source_skill: "demo-prospect-workspace"`, `primary_thread_id` (a project id), `related_thread_ids`, `classification_confidence: 1.0`, `org_ids`, `person_ids`, `data`. Data payloads follow the per-type shapes the fixture demonstrates: meetings carry `title`, `summary`, `attendees` (emails), `meeting_type`, `duration_min`, `source_ref`; interactions carry `channel`, `direction`, `summary`, `source_ref`; commitments carry `id` (a `cmt_` id), `title`, `kind` (one of promise, task, scheduling, agenda — set it explicitly on every commitment), `owner_person_id`, `due_date`, `status: "open"`, `source_ref`; decisions carry `decision`, `rationale`, `decided_by_person_id`; a note carries `text`.
- `aliases.json`: `version`, `last_updated`, `last_writer`, and `mappings` for people and projects — each mapping row carries `raw`, `canonical_id`, `confidence`, `added_ts`, `added_by: "demo-prospect-workspace"`, and every `canonical_id` must resolve to an entity you wrote.

**Brand — exactly two values, inside `workspace.brand` in `entities.json`:**

- `palette.accent`: ONE accent color as a bare hex value, deliberately OUTSIDE the standard document palette (not the default teal, navy, or any other stock theme color — if the company's public branding suggests a color that reads well, use that). This is the only visual identity the demo gets.
- `footer_line`: exactly `DEMO · illustrative data` — byte-for-byte, every generated document shows it.
- Nothing else: no logo, no fonts, no per-project colors. If the accent renders badly against any surface, ship plain with the footer line alone — do not iterate on branding.

### Step 7 — Manifest and workspace CLAUDE.md

Write `_hq/data/demo_manifest.json` matching the reference fixture's shape:

- `generator: "demo-prospect-workspace"`, `generator_version`, `created` (today, ISO date), `expires` (created plus exactly 7 days), `reference_date` (same as created — events are anchored to it, never to a later clock), `prospect_org_id`, `prospect_name`, `primary_person_id` (the person record in the primary-user seat), `primary_is_real_person` (`true` when the trigger named the real call attendee; `false` when the seat is a generic invented person), `synthetic: true`, and the `marker_convention` block spelling out the event prefix, the project-field prefix, the invented-person name suffix (and the real primary person's clean-name exception), and the footer line, as the fixture does.

Write `CLAUDE.md` at the folder root. It must say, in plain language:

- Every reply in this workspace opens with the line `read from Demos/<prospect folder name>`.
- All operating data here is illustrative and marked — events and projects carry the DEMO prefix in their text, invented people's names end with the Demo suffix (the real primary person's name renders clean; their synthesized items carry the prefix), and every generated document footer reads `DEMO · illustrative data`.
- This workspace belongs to the named person and role from the trigger (or the generic seat) — surfaces render from their point of view, their morning, not the operator's.
- The workspace expires on the date in the manifest; do not extend it or copy its records into another workspace.

### Step 8 — Verify, then report

Before reporting done, verify against what is actually on disk, not what you meant to write:

- Re-read the generated files. Check: people/project/org counts match the volume contract; every event text field, project name, and next step carries its `[DEMO] ` prefix; every invented person's name ends ` (Demo)` and, when `primary_is_real_person` is true, the primary person's name is clean (no suffix); the footer line is byte-exact; `expires` is exactly `created` plus 7 days; event `seq` values strictly increase and every timestamp is on or before `reference_date`; `_hq/BUSINESS_CONTEXT.md` exists and is non-empty.
- Count open commitments through the canonical counter — `commitment_counts` from `$CR_PAYLOAD/shared/scripts/commitment_state.py` (Step 0), pointed at the new folder — and confirm it reports exactly 8 open. If any check fails, fix the data and re-verify; if it cannot be fixed cleanly, delete the folder and say what went wrong.
- Then report, one screen, plain English: the sweep result (Step 2's one line), which research tier ran (Step 5's one line), what was built (the folder, the people/project/commitment volume, whose point of view), and the expiry date.

## Output

- A ready-to-open demo workspace folder under Demos/, carrying its own data files, manifest, and CLAUDE.md — nothing outside it.
- A one-screen chat report: sweep result, research tier, what was built, expiry date. No document deliverable, no widget surface — the folder is the deliverable.
