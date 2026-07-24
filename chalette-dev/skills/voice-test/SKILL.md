---
name: voice-test
description: "INTERNAL DIAGNOSTIC — fires solely on the exact phrase 'internal: run voice regression'. Generates test drafts from each writing skill for 1-5 scoring; not for customer chat or real-use drafting."
---

# Voice Test

**For:** ensuring the CEO's voice-calibrated writing skills don't drift over time. Generic-assistant voice creeps in even with Voice Blocks. This skill catches drift before the CEO notices it in a customer-facing email.

## Skill Boundary

- **Use `voice-test` for:** monthly regression testing of voice calibration across writing skills.
- **Use the writing skills themselves (`email-writer`, etc.) for:** actual drafts for real use.
- **Use Chalette calibration service for:** the initial voice extraction and voice-block generation. `voice-test` is the health-check loop, not the creation process.

## Writer Contract

Before writing, read `shared/WORKSPACE_API.md`.

**Primary writer for:**
- `_hq/voice/test-results.jsonl` — append one row per test run.
- `_hq/voice/test-reports/[YYYY-MM-DD]_voice_test.md` — human-readable summary.

**Appends to:**
- `_hq/data/events.jsonl` — event type `voice_test_run`.
- `_hq/voice/corrections-[skill].jsonl` if the CEO provides specific corrections during scoring.

**Reads only:**
- All writing-skill SKILL.md files (to find the ones to test)
- `_hq/data/events.jsonl` (to find representative recent scenarios)
- `_hq/data/entities.json` (for recipient context)

---

## What It Does

Once a month, for each calibrated writing skill in the workspace, pick a representative real recent scenario, invoke the skill to produce a draft, ask the CEO to score it 1-5 on "sounds like you", and log results. If any skill scores below 4, flag it for voice-block refresh.

## How It Works

### Phase 1 — Enumerate writing skills

Scan the plugin's active skills for those tagged as writing skills. Known set:
- `email-writer`
- `memo-writer`
- `follow-up-ritual`
- `one-pager-composer`

Plus any client-specific writing skills in the private plugin (if present).

### Phase 2 — Build scenario batch

For each writing skill, pick ONE real scenario from the last 30 days:

**email-writer test scenario:**
Pick a real person from entities.json who the CEO emailed in the last 30 days. Pick a real topic from recent events involving that person. Prompt:
> "Draft an email to [real person] about [real topic]."

**memo-writer test scenario:**
Pick a real recent decision from events.jsonl (type=decision).
> "Draft a decision memo explaining [real decision]."

**follow-up-ritual test scenario:**
Pick the most recent real meeting with a transcript in Granola.
> "Draft the follow-up pack from [real meeting]."

**one-pager-composer test scenario:**
Pick a real recent project or topic.
> "One-pager on [real topic]."

Scenarios pull from real data so the tests are ecologically valid. Generic test prompts produce generic test results.

### Phase 3 — Invoke each skill, collect drafts

Invoke each writing skill with its scenario. Collect the draft output. Do NOT write these drafts to actual deliverables folders — they are test artifacts only, stored in memory for the scoring pass.

### Phase 4 — Present to CEO for scoring

Show each draft inline with the prompt that generated it. For each, ask:

> "Score 1-5: does this sound like you?"
> - 5 = indistinguishable from something I'd write
> - 4 = sounds like me, minor tweaks
> - 3 = recognizable but off — would need significant editing
> - 2 = doesn't sound like me
> - 1 = sounds like a generic AI

Also collect one-line optional notes per skill: "what's off?"

### Phase 5 — Log results

Append to `_hq/voice/test-results.jsonl`:

```json
{
  "timestamp": "2026-05-15T10:00:00Z",
  "skill": "email-writer",
  "scenario_prompt": "Draft an email to Sam about the LOI meeting push",
  "draft_sample": "[first 200 chars of the draft]",
  "score": 4,
  "notes": "slightly too formal for Sam — his samples are more clipped"
}
```

### Phase 6 — Flag refreshes

After all scores logged, analyze:

- **Score ≥4 on all skills:** no action. Next test next month.
- **Score 3 on any skill:** flag for refresh. Surface in next workspace-status briefing with specific note.
- **Score ≤2 on any skill:** block further output from that skill (via SKILL.md frontmatter flag) until refreshed. Alert CEO explicitly.

For any skill flagged for refresh, propose the next step:
> "email-writer scored 3 — want to run a refresh now, or batch for the next Chalette retainer call?"

### Phase 7 — Write summary report

Write to `_hq/voice/test-reports/[YYYY-MM-DD]_voice_test.md`:

```markdown
# Voice Test — [YYYY-MM-DD]

## Summary
- Skills tested: N
- Average score: X.X
- Flagged for refresh: [list]

## Per-skill results

### email-writer — Score 4
Scenario: [prompt]
Draft: [full text]
Notes: [CEO notes]

### memo-writer — Score 5
...
```

### Phase 8 — Emit events

Append `voice_test_run` event to events.jsonl with per-skill scores.

---

## Scheduling

Register as a monthly scheduled task via the `schedule` skill / `scheduled-tasks` MCP:

- **Day of month:** 1st or 15th (configurable via BUSINESS_CONTEXT)
- **Time:** 9am CEO local time
- **Surfaces as:** interactive prompt in workspace-status briefing, not a silent background task

CEO can defer once per month. Can't defer twice — keeps the rhythm.

## Block-output mechanism

When a skill scores ≤2, `voice-test` appends a block entry to the workspace-local control file at `_hq/voice/skill-blocks.jsonl` — it does **not** modify the shipped plugin SKILL.md files (plugin-source is immutable from inside the plugin).

Each block entry:

```json
{
  "skill": "email-writer",
  "blocked": true,
  "reason": "score 2 in 2026-05-15 voice-test",
  "date": "2026-05-15",
  "bypass_until": null
}
```

Each writing skill reads `_hq/voice/skill-blocks.jsonl` at invocation. If an active block exists for its own name, it emits:

> "⛔ Voice calibration blocked — last test score was too low. Run `voice-refresh` or temporarily override with `--bypass-voice-check`."

Unblocking: pass a voice-test run with score ≥3, which appends a new entry with `blocked: false` (the writing skill reads the latest entry per skill).

This prevents silent drift → bad customer emails → lost trust, without the plugin mutating its own source files.

## Integration with Chalette monthly retainer

For $10K-tier clients, `voice-test` runs on a schedule that aligns to 2-3 days before the monthly retainer call. Chalette sees the results in advance and plans the refresh work for the call. By the time the call happens, Chalette knows exactly which skills need attention.
