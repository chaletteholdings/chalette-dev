---
name: smoke-watch
description: "INTERNAL — passive observation during the 24h post-promote smoke window. Watches the operator's real Cowork usage (event log + chat narration on paste-back) for architectural surprises that automated gates missed. Requires an operator profile with 'real' in allowed_targets (config/operator.json); refuses otherwise — it has no synthetic mode. Triggers: 'start smoke watch', 'smoke window monitor', 'watch for v[version] issues'. Compresses the Decision-5 24h operator-only smoke window into structured surveillance. Catches bug classes that other gates can't see. Plugin-developer use only."
---

# smoke-watch

**Passive observation during the 24h post-promote smoke window.** Watches the operator's real Cowork usage for architectural surprises that the pre-promote gates missed.

> **Operator profile (read first).** Load `config/operator.json`, then overlay `config/operator.local.json` per-key if it exists (gitignored; the operator's local overlay — only M has one). This skill has **no synthetic mode**: if the merged `allowed_targets` does not include `"real"`, refuse and say so (it observes a live workspace or nothing — that's honest). All paths below resolve from `workspace_root`.
> ```python
> import json, os
> op = {}
> for _n in ("operator.json", "operator.local.json"):
>     _p = os.path.join(SKILL_PLUGIN_ROOT, "config", _n)
>     if os.path.exists(_p): op.update(json.load(open(_p)))
> if "real" not in op.get("allowed_targets", []): refuse("smoke-watch needs an operator profile with 'real' in allowed_targets")
> ```

**STATUS: SCAFFOLD.** Implementation deferred to dedicated session — best built after a real promote cycle so the watch patterns reflect actual smoke-window observations.

## When this fires (post-implementation)

| Trigger | Context |
|---|---|
| `start smoke watch` | Begin 24h passive observation window |
| `smoke window monitor` | Same |
| `watch for v3.13.8 issues` | Version-specific watch |
| `smoke watch status` | Current watch state + observations |
| `smoke watch verdict` | End watch + emit PROMOTE-TO-PROD-OR-ROLLBACK verdict |

## Behavior (post-implementation TODO)

### Step 1 — Initialize watch window

```python
watch_id = f"smoke_watch_v{version}_{start_iso}"
state = {
    "watch_id": watch_id,
    "version_under_smoke": version,
    "window_started": start_iso,
    "window_ends": start_iso + 24h,
    "observations": [],
    "architectural_surprises": [],
}
```

State persists in `_hq/.system/smoke-watches/{watch_id}.json`.

### Step 2 — Passive observation loop

For 24h, the watch:

1. **Polls the operator's events.jsonl** (under `workspace_root`) every N minutes for new events
2. **Listens for the operator's manual paste-backs** (when they paste-share unusual Cowork behavior)
3. **Checks for new error events** (pattern_break_detected, freelance_render_detected, corruption_recovery)
4. **Aggregates regression signals** vs the bug-regression-suite catalog
5. **Surfaces architectural surprises** to M in real-time

Example surprise surface:
```
smoke-watch alert: 

I just noticed your last 3 morning-brief fires emitted pack_run events with data.kind = "unknown" — that's Bug #61 not fully resolved for past-meetings orchestrator in v3.13.8. Logging as candidate for v3.13.8.1 patch.

Continuing watch (18h remaining in smoke window).
```

### Step 3 — End-of-window verdict

After 24h (or M fires `smoke watch verdict`):

```
smoke-watch verdict — v3.13.8 (24h window complete)

Observations:
- 47 scheduled-task fires (clean across 7 surfaces)
- 12 on-demand skill fires (3 email-writer, 4 commitments, ...)
- 2 architectural surprises flagged:
  * Bug #61 partial: past-meetings + upcoming-meetings still emit pack_run kind=unknown
  * Bug #46 partial: render_path_router not enforced for email-writer (M observed canonical render but action-label drift)
- 0 critical regressions
- 0 new ship-blocker bug classes

Recommendation: PROMOTE TO PRODUCTION ✓

Both architectural surprises are PARTIAL-FIX completion items, suitable for v3.13.8.1 follow-up but not blocking promote.
```

### Step 4 — Verdict outputs

```
SMOKE_WATCH_v3.13.8_2026-05-26.md saved under <workspace_root> (resolved from config/operator.json)

Verdict: PROMOTE | ROLLBACK | HOLD

If PROMOTE:
- Run ship-cr-plugin Step 9 production promote
- M is safe to fire v3.6.4 → v3.13.8 production update

If ROLLBACK:
- Revert staging clone to prior version
- Surface specific failures

If HOLD:
- Extend smoke window
- Specific items needing the operator's call
```

## Implementation TODO

Substantive code needed:
1. Event-log polling helper (incremental read since last poll)
2. Regression-signal aggregator (matches incoming events against bug-regression-suite catalog patterns)
3. M paste-back parser (accepts ad-hoc reports from M about anything unusual)
4. Architectural-surprise classifier (regex + heuristics over new event types + skill outputs)
5. End-of-window verdict generator

Estimated implementation: 2-3 hours dedicated session post-first-promote-cycle (so observation patterns reflect reality).

## What this skill catches

- Production-only bug classes that synthetic + verification can't reproduce
- Slow-burn issues that surface only over hours of real use
- Cowork-platform variations that affect customer environments differently
- Regression of fixes that PASSED pre-promote gates but break in production

## What it can't catch

- Bugs that only surface 1+ week post-promote (would need longer windows or scheduled re-checks)
- Issues that only happen for OTHER customers (the operator's workspace ≠ all customer workspaces)
- Bugs in adjacent systems (Anthropic infra issues, MCP connector outages)

## Integration with ship-readiness-gate

ship-readiness-gate emits PROMOTE recommendation → M fires `start smoke watch v3.13.8` → smoke-watch runs 24h → emits final PROMOTE/HOLD/ROLLBACK → M decides production promote.

The two skills together compress the v3.13.8 master plan §10 Decision 5 smoke window into a structured + observable workflow.

## Connection to V3.13.8_MASTER_PLAN

This skill operationalizes §10 Decision 5 (24h M-only smoke before promote). Without it, smoke window is manual + ad-hoc. With it, smoke window is structured + auditable + emits a defensible promote recommendation.
