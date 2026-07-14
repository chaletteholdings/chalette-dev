---
title: First-Run Questionnaire Convention
cr_plugin_version_min: 3.13.8.3
last_updated: 2026-05-26
---

# First-Run Questionnaire Convention

Pattern spec for CR skills whose behavior varies by operator. Locked 2026-05-25 in `NEXT_SKILL_BATCH_SPECS` doc; codified here for cr-skill-builder Phase 3 use.

## Why first-run config exists

The substrate already knows a lot about each operator (org graph, projects, people, transcripts). But CEO preferences vary on dimensions the substrate CANNOT infer:
- "How many priorities for my weekly review — 3 or 5?"
- "Where should stalled-project flags surface — Pulse, Friday Wrap, both?"
- "What's a 'healthy' interaction cadence for my customers — weekly or monthly?"
- "What's my OKR cycle length — calendar quarter, fiscal quarter, custom 12-week?"

A skill that hard-codes one answer will frustrate half its users. A skill that asks once and remembers makes itself feel hand-tuned.

## Storage

`_hq/data/skill_config/<skill-name>.json` — one JSON per configured skill.

Directory created lazily on first write.

Schema in `command-room/shared/data-schemas/skill_config.schema.json`. Base shape every skill inherits:

```json
{
  "schema_version": 1,
  "configured_at": "<ISO datetime>",
  "skill_name": "<skill-name>",
  "config": {
    // skill-specific keys
  }
}
```

## Lifecycle (every fire of a config-aware skill) — "Show, then tune"

Config-aware skills MUST follow the CR-canonical **"Show, then tune"** UX: produce useful output IMMEDIATELY with sensible defaults, then offer to tune. **Never block first-time users behind a questionnaire.**

The four trigger modes:

| Mode | Example phrases | Behavior |
|---|---|---|
| **Detect** (default) | "show me [thing]", "[skill] check", main skill triggers | **No questions, ever.** Load config OR use defaults. Run the actual skill work. Render output. On FIRST fire only: auto-save defaults + append a one-time tune offer footer. |
| **Tune** | "tune [skill]", "change my [skill] settings", "change [skill] thresholds", "reconfigure [skill]", "redo [skill] setup" | Load current config → walk questionnaire with current values pre-filled as defaults → save → IMMEDIATELY re-run the actual skill work with new config so the user sees the cause-and-effect. |
| **Show settings** | "show my [skill] settings", "what are my [skill] settings", "show [skill] config" | Load config → display current answers in a read-only widget with one action ("tune"). Do NOT run skill work. |
| **Reset to defaults** | "reset [skill] to defaults", "reset [skill] settings" | Call `wipe_skill_config(workspace_root, "[skill]")` → confirm. Do NOT run skill work. |

### Detect mode pseudocode (the default path — ~95% of fires)

```python
config = load_skill_config(workspace_root, "<skill-name>")
is_first_fire = (config is None)

# Skill's main work — uses defaults if no config saved
output = run_skill_main_work(workspace_root)
render_chat_output_widget(output)

if is_first_fire:
    # Auto-save defaults so subsequent fires skip this branch
    save_skill_config(workspace_root, "<skill-name>", DEFAULT_CONFIG)
    # Append one-time tune offer below the widget
    append_chat("""
First time using <skill-name>. I used the recommended defaults — [brief 1-sentence summary
of what the defaults are]. Want to change [the main thing the user might tune]? Say
**"tune <skill-name>"** to walk a quick setup, or just tell me what you'd change in your
own words and I'll figure out which setting that maps to.
""")
```

**Subsequent fires:** config exists → load → run work → render. No footer, no nag.

### Tune mode pseudocode — questionnaire + immediate re-render

```python
current = load_skill_config(workspace_root, "<skill-name>")
# Walk questionnaire with current["config"] values pre-checked / pre-selected.
# User can accept-all (keeps everything) or change individual answers.

save_skill_config(workspace_root, "<skill-name>", new_config)
# Auto-detects (file exists) → emits skill_reconfigured event.

# CRITICAL: immediately re-render the skill's output with the new config
# so the user sees what their change actually did.
output = run_skill_main_work(workspace_root)
render_chat_output_widget(output)
append_chat("Updated. Showing your [outputs] with the new settings.")
```

Pre-filling current values is what makes tune feel like "edit settings" instead of "start over." Re-rendering with the new config is what makes the cause-and-effect visible — user sees the threshold they just changed actually changing the output.

### Freeform tune (preferred when user gives natural-language feedback)

If the user responds to output with natural-language feedback rather than firing the structured tune flow — e.g., "flag paused threads sooner" or "I don't care about exploring threads" — parse the intent and apply the implied config change directly without walking the full questionnaire.

Each config-aware skill SHOULD include a freeform-tune mapping table in its SKILL.md that lists common feedback phrases → config field changes. See `command-room/skills/stalled-projects/SKILL.md` for the canonical example.

After applying the change: `save_skill_config(..., is_reconfigure=True)` + re-run work + confirm in plain English ("Got it — paused threshold is now 30 days. Here's the updated list."). Don't make the user walk the full questionnaire if a single sentence captured their intent.

### Show-settings mode pseudocode

```python
current = load_skill_config(workspace_root, "<skill-name>")
if current is None:
    respond("You haven't run <skill-name> yet. Fire the main trigger to see output using the defaults — you can tune anytime after that.")
else:
    # Render current["config"] as a read-only widget with one action: "tune"
```

### Reset-mode pseudocode

```python
existed = wipe_skill_config(workspace_root, "<skill-name>")
if existed:
    respond("Settings reset to defaults. Next fire uses defaults again — and offers you the tune flow on first re-fire.")
else:
    respond("No settings to reset — you're already on defaults.")
```

### Why "show, then tune"

Locked 2026-05-26 from real Cowork testing of stalled-projects v3.14.1. The original pattern (questionnaire FIRST, then output) created three real problems:

1. **Users had to answer abstractly before seeing what defaults produced.** "How many days quiet before flagging?" is hard to answer in the abstract; easy to answer after seeing your stall list.
2. **First-time friction killed exploration.** Users who fired a skill out of curiosity got hit with a setup wall and dropped.
3. **Tuning felt heavyweight.** Walking 5 questions to change one threshold is a UX failure.

Show-then-tune fixes all three: instant value, contextualized configuration, lightweight tuning.

### Pattern enforcement

cr-skill-builder Phase 4 should surface a **BLOCK** if a config-aware skill's SKILL.md describes a first-run questionnaire flow that blocks output. Detect mode MUST produce output before any questions. Hard gate (Gate 21 — show-then-tune) planned for chalette v0.8 once the pattern has shipped against at least 2 config-aware skills. For v0.7.2, treat as a strong convention enforced by code review.

## Questionnaire flow

1. **Announce:** "First time running for this workspace. Quick 3-5 questions to tailor."
2. **Walk questions sequentially.** Each question:
   - Plain-English statement (NO jargon).
   - Substrate-derived default pre-populated.
   - Multiple-choice or short structured input (NEVER open-ended free text).
   - "Use defaults" skip-all option at the top of Q1.
3. **After all answered:**
   - Write config via `skill_config_writer.py::save_skill_config()` (atomic).
   - Emit `skill_first_run_configured` event with `config_snapshot`.
   - Proceed with the actual skill work.

## Reconfigure / show-settings / reset paths

See the **Lifecycle** section above — the canonical four-mode UX (detect / show-settings / reconfigure / reset) is required for every config-aware skill. The exemplar implementation lives in `command-room/skills/stalled-projects/SKILL.md` (v3.14.1.1+). Copy the trigger-intent table + mode-dispatch logic when scaffolding new config-aware skills.

## 5-question cap (Gate 10 — CI-enforced)

The principle: if you need >5 questions to configure, you're asking for state the substrate should derive. cr-skill-builder Phase 3 enforces the cap; CI validator re-enforces at PR time.

## Substrate-aware default rules

Apply these to every questionnaire's defaults:

| Question type | Default source |
|---|---|
| "Which customers / projects / people?" | Read `_hq/data/entities.json` — present top N by `last_interaction` recency |
| "How often / cadence?" | Read scheduled-chat config + calendar cadence patterns from events.jsonl |
| "Voice / tone / format?" | Reference `VOICE_SAMPLES.md` if it exists + workspace-manager's stored voice calibration |
| "Tier / threshold / sensitivity?" | Pick sane default labeled "we recommend X" |
| "Which connectors?" | Reference `_hq/data/connector_status.json` if it exists |

## Anti-patterns (blocked by Gate 10 or warned at Phase 3)

- More than 5 questions → BLOCK
- Open-ended free text ("what are your goals?") → WARN (suggest converting to multi-select)
- Asking for state already in entities.json / events.jsonl → BLOCK (DROP the question)
- Gating the first useful output behind the questionnaire — if user picks "use defaults," skill must produce real value immediately → WARN

## Per-skill questionnaire authoring (Phase 3 walkthrough)

cr-skill-builder Phase 3 walks M through drafting questions. For each question, the helper auto-suggests:
- The substrate-aware default rule that applies (from the table above)
- Adjacent existing skills with similar questionnaires (for consistency)
- Whether the question survives the "5-question cap" pressure test
- Whether the question's answer is already derivable from the substrate (DROP candidate)

Output: a config object schema dropped into `command-room/shared/data-schemas/<skill_name>_config.schema.json` + a template at `_hq/data/skill_config/<skill_name>.json.template`.

## New event types this pattern introduces

To be added to `events.schema.json` enum (Gate 1) when the first-run pattern ships:

- `skill_first_run_configured` — emitted on first questionnaire completion. Shape:
  ```json
  {
    "type": "skill_first_run_configured",
    "data": {
      "skill_name": "<name>",
      "schema_version": 1,
      "config_snapshot": { /* the config object */ }
    }
  }
  ```
- `skill_reconfigured` — emitted on reconfigure. Same shape.

## Consumer skills for these events (Gate 2)

At least one consumer required. Suggested consumers:
- `usage-report` — track first-run configs across the workspace (which skills have been tailored)
- `weekly-audit` — surface skills NOT yet configured (potential drift)

## Helper script

`command-room/shared/scripts/skill_config_writer.py` exposes:

```python
load_skill_config(workspace_root, skill_name) -> dict | None
save_skill_config(workspace_root, skill_name, config: dict, schema_version: int) -> None
wipe_skill_config(workspace_root, skill_name) -> None  # for reconfigure flow
```

Internally uses `atomic_write_json`. Validates against `skill_config.schema.json`.

To be added at v3.14 ship time alongside the first set of config-aware skills (customer-health-scorer, okr-tracker, 1on1-tracker, weekly-review-coach, stalled-project-detection enhancement).

## Example questionnaire (customer-health-scorer)

5 questions, each with substrate-aware defaults:

1. **Where's your customer list?**
   - Default: CRM connector (if installed) > `_hq/CUSTOMERS.md` > entities.json orgs with `relationship_type ∈ {client, prospect, portfolio_company}` (default if ≥3 matches)

2. **What signals count toward health?** (multi-select, defaults pre-checked)
   - ☑ Interaction recency
   - ☑ Commitment completion rate
   - ☑ Transcript sentiment (if Granola connected)
   - ☐ Revenue trend (if QuickBooks connected)
   - ☐ Contract renewal proximity

3. **Healthy interaction cadence?**
   - Default: Per-customer baseline (computed from 12-month history)
   - Alternates: weekly / biweekly / monthly / quarterly

4. **Tier thresholds.**
   - Default: GREEN ≥ 70, YELLOW 40-69, RED < 40
   - Or customize

5. **How often should this run?**
   - Default: On-demand only
   - Alternates: Weekly with Friday Wrap / Daily with morning-briefing (RED tier only)

Output config:
```json
{
  "schema_version": 1,
  "configured_at": "2026-05-26T14:30:00Z",
  "skill_name": "customer-health-scorer",
  "config": {
    "customer_list_source": "entities_orgs",
    "signals": ["interaction_recency", "commitment_completion_rate", "transcript_sentiment"],
    "cadence_baseline": "per_customer",
    "tier_thresholds": {"GREEN": 70, "YELLOW": 40, "RED": 0},
    "run_cadence": "on_demand"
  }
}
```
