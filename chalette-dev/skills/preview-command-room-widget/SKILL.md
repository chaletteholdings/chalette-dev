---
name: preview-command-room-widget
description: "INTERNAL DIAGNOSTIC — fires solely on the exact phrase 'internal: preview widget [name]' (e.g., 'internal: preview widget inbox'). Plugin-developer use only; not for customer chat."
---

# preview-command-room-widget

User-facing widget preview. Renders any of the 5 scheduled-task widgets on demand without consuming a real fire. Same surface (`mcp__visualize__show_widget`), same renderer (`render_chat_output_widget`), same CSP sandbox = identical fidelity to production.

Per Cowork's confirmed sandbox model: `show_widget` runs the same way regardless of whether it's invoked from a scheduled-task fire or an on-demand skill trigger. CSS / JS / interactivity all behave identically.

## Two modes

### Mode 1 — Canonical fixture (no real data needed)

The user types `preview inbox widget` (or commitments / pulse / past meetings / upcoming meetings). Skill loads the canonical fixture from `tests/run_audit_v2_13_0.py`:
- INBOX = stub email + calendar invite items
- COMMITMENTS = stub YOU OWE + OWED TO YOU items with grouped sub-items
- DONT_FORGET = stub people + project items + REVIEW section
- PAST_MEETINGS = stub processed meetings with multi-person sub-items
- UPCOMING_MEETINGS = stub Sam meeting with brief link

Renders through `render_chat_output_widget()`. Posts via `mcp__visualize__show_widget`.

Use case: "I changed the renderer / CSS / action labels — does the widget still look right?" No real data needed.

### Mode 2 — Replay last fire (uses real data from events.jsonl)

The user types `replay last inbox` (or any orchestrator name). Skill reads the most recent `pack_run` event for that `kind` from `_hq/data/events.jsonl`, extracts the cached `data.last_data_view` field (captured by every fire since v2.14.1 per `telemetry.build_data_view_snapshot`), re-renders through current `render_chat_output_widget()`.

Use case: "An hour ago Inbox fired and the widget had a bug. Did v2.14.x fix it?" Replay the snapshot through the new code without waiting for tomorrow's data.

## Behavior

### Step 1 — Parse the trigger

Recognize these patterns (case-insensitive):
- `preview <name> widget` / `preview <name>` → Mode 1, canonical fixture
- `replay last <name>` / `replay <name>` → Mode 2, last fire's snapshot
- `<name>` ∈ {inbox, commitments, pulse (or legacy `dont forget` / `dont-forget`), past meetings / past-meetings, upcoming meetings / upcoming-meetings}

If `<name>` is unrecognized OR ambiguous, surface plain English:

> *"Which widget? Try `preview inbox widget` / `preview commitments widget` / `preview pulse widget` / `preview past meetings widget` / `preview upcoming meetings widget`. Or `replay last <name>` to re-render the most recent fire from events.jsonl."*

### Step 2 — Discover plugin root + run renderer in one bash call

```bash
SESSION_DIR=$(echo "$CLAUDE_CODE_TMPDIR" | sed "s|/tmp$||")
PLUGIN_ROOT=$(ls -d "$SESSION_DIR"/mnt/.remote-plugins/plugin_* 2>/dev/null | head -1)
WORKSPACE=$(find "$SESSION_DIR/mnt" -maxdepth 5 -type d -name "_hq" 2>/dev/null | head -1 | sed 's|/_hq$||')
cd "$PLUGIN_ROOT" && python3 -c "
import sys, json
sys.path.insert(0, 'shared/scripts')
from chat_output_renderer import render_chat_output_widget

# Mode 1 — canonical fixture
sys.path.insert(0, 'tests')
from run_audit_v2_13_0 import INBOX, COMMITMENTS, DONT_FORGET, PAST_MEETINGS, UPCOMING_MEETINGS
fixtures = {
    'inbox': INBOX,
    'commitments': COMMITMENTS,
    'dont_forget': DONT_FORGET,
    'past_meetings': PAST_MEETINGS,
    'upcoming_meetings': UPCOMING_MEETINGS,
}
target = '<orchestrator-key>'  # set by skill from user input
data_view = fixtures[target]
html = render_chat_output_widget(data_view)
# Output the HTML — skill captures stdout and passes to show_widget
print(html)
"
```

For Mode 2, replace the fixture-loading block with an events.jsonl read:

```python
# Mode 2 — replay last fire
events_path = f"{WORKSPACE}/_hq/data/events.jsonl"
import os
if not os.path.exists(events_path):
    print("REPLAY_ERROR: no events.jsonl found")
    sys.exit(1)
with open(events_path, 'r', encoding='utf-8') as f:
    events = [json.loads(line) for line in f if line.strip()]
# Find most recent pack_run for this kind
kind_alias = {'dont_forget': 'dont_forget', 'past_meetings': 'past_meetings', ...}
matching = [e for e in events if e.get('type') == 'pack_run' and e.get('data', {}).get('kind') == target]
if not matching:
    print(f"REPLAY_ERROR: no pack_run events found for kind={target}")
    sys.exit(1)
last_fire = matching[-1]
data_view = last_fire.get('data', {}).get('last_data_view')
if not data_view:
    print(f"REPLAY_ERROR: pack_run for {target} has no last_data_view (was fired before v2.14.1 telemetry)")
    sys.exit(1)
html = render_chat_output_widget(data_view)
print(html)
```

### Step 3 — Post the rendered HTML via show_widget

Capture stdout from the bash call. The HTML is the widget body. Pass to `mcp__visualize__show_widget`.

If the bash output starts with `REPLAY_ERROR:`, surface that as plain English instead of rendering. (E.g., "No past Inbox fire on file yet — fire one first or use `preview inbox widget` for the canonical fixture.")

If the renderer raises `CanonicalActionError`, `LeakDetectedError`, or `DataShapeError`: surface the exception as plain English. The fixture / snapshot has a real bug. Don't paper-over.

### Step 4 — STOP

The widget IS the post. No commentary, no narration. Per CONTRACT.md Rule 4 + the standard show_widget posting contract.

If user wants to test button clicks (Apply, Edit then send, etc.), they click in the rendered widget. The submission goes to `apply-choices` per the standard widget contract. apply-choices runs against the SAME fixture context — so `Apply all` on a preview fixture produces a consolidated test response. Verifies the full round-trip without a real fire.

## What this skill does NOT do

- Does NOT modify events.jsonl (read-only)
- Does NOT modify any plugin file
- Does NOT call connectors (no Gmail / Calendar / Granola fetches — fixtures are static; replay reads cached snapshot)
- Does NOT charge tokens to the user's scheduled-task budget

Pure local rendering + display. Iteration speed for visual / layout / button testing.

## Trigger patterns

Mode 1 (canonical fixture):
- `preview command room widget` (asks which one)
- `preview inbox widget` / `preview inbox`
- `preview commitments widget` / `preview commitments`
- `preview pulse widget` / `preview dont-forget widget`
- `preview past meetings widget` / `preview past-meetings widget`
- `preview upcoming meetings widget` / `preview upcoming-meetings widget`
- `show me the widget`

Mode 2 (last actual fire):
- `replay last inbox` / `replay inbox`
- `replay last commitments` / `replay commitments`
- (etc. for all 5)

## See also

- `cr test --quick` (also `run command room tests`) — runs the test suites; pairs with this skill for "is the build healthy AND does it look right?"
- `verify command room prompts` — confirms registered scheduled-task prompt versions
- `usage report` — surfaces telemetry from past fires (different read of events.jsonl — focused on cost/usage, not visual replay)
