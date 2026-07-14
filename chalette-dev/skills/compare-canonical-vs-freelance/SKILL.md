---
name: compare-canonical-vs-freelance
description: "INTERNAL — POST-V3.13.8 DEPENDENT. Fires a given Command Room skill TWICE against the same input: once through the canonical render+dispatch path (file-URI transport per §2.1), once through a mocked freelance fallback. Captures side-by-side diff of: widget HTML byte counts, action labels (canonical lowercase vs freelance variants), dispatch payload shape (apply choices vs sendPrompt), events written, leak-scanner findings. Generates .docx comparison artifact for design review. Triggers: 'compare canonical vs freelance for [skill]', 'render-path diff [skill]'. Used to validate v3.13.8 §3.6 widget degradation ladder per-skill. Plugin-developer use only. Companion to verify-cr-release + synthetic-workspace-runtime-test."
---

# compare-canonical-vs-freelance

**STATUS: SCAFFOLD — full implementation depends on v3.13.8 §2.1 file-URI transport landing first.** The skill's value-add (side-by-side render-path diff) requires the canonical file-URI transport so we can deterministically force canonical vs freelance render paths from a test harness.

## What this skill does (post-v3.13.8)

Fires a Command Room skill TWICE against the same synthetic input:
1. **Canonical run** — forces file-URI transport per §2.1, real canonical render + apply-choices dispatch
2. **Freelance run** — mocks the canonical path failure point to force freelance fallback (bespoke HTML + sendPrompt indirection)

Then captures + diffs:
- Widget HTML bytes (canonical vs freelance)
- Action labels (canonical lowercase per Rule 6 vs freelance variants)
- Dispatch payload shape (apply choices: [...] JSON vs sendPrompt natural-language)
- Events written (canonical event-write chain vs freelance silent-write)
- Leak-scanner findings (per Bug #54 word-boundary scan)

Generates a `.docx` comparison artifact for design review + ladder validation per V3.13.8_MASTER_PLAN §3.6.

## When this fires (post-v3.13.8)

| Trigger | Context |
|---|---|
| `compare canonical vs freelance for email-writer` | Fire email-writer twice, diff outputs |
| `compare canonical vs freelance for intro-broker` | Same for intro-broker |
| `render-path diff [skill]` | Synonym |
| `validate widget ladder [skill]` | Diff against §3.6 expected canonical surface for the skill |

## Why this skill exists

v3.13.8 §3.6 codifies a widget degradation ladder:
- n>1 + actionable → Path A canonical batched widget
- n=1 + actionable + compose-new → Path B1 editor card
- n=1 + actionable + confirm-drafted → Path B2 confirmation card
- n=1 + degraded → Path B2 with recovery widget (Bug #44 add_email_then_send)
- Single-question single-decision → Path D AskUserQuestion
- Closure-reversal detected → confirmation widget (Strength #20)
- Read-only orientation → chat-mode synthesis (no widget)

After v3.13.8 ships, every skill should route per the ladder. **This skill validates that each skill's canonical path matches its declared canonical surface per the ladder.** If a skill says it should render via Path B1 but actually emits Path A's full batched widget, that's drift the ladder enforcement test (§3.7) won't catch but this diff will.

## Behavior (post-v3.13.8 — TODO until §2.1 lands)

### Step 1 — Locate skill + load test harness

```python
# TODO post-v3.13.8: integrate with §2.1 file-URI transport
from shared.scripts.widget_transport import render_and_relay  # exists post-§2.1
from shared.scripts.chat_output_renderer import render_chat_output_widget  # exists pre-§2.1
```

### Step 2 — Fire canonical path

```python
# TODO post-v3.13.8: 
canonical_result = run_skill_with_transport_mode(
    skill_name=skill_name,
    fixture=test_fixture,
    transport_mode="canonical_file_uri",  # forces §2.1 path
)
```

### Step 3 — Fire freelance path

```python
# TODO post-v3.13.8:
freelance_result = run_skill_with_transport_mode(
    skill_name=skill_name,
    fixture=test_fixture,
    transport_mode="freelance_simulated",  # mock canonical path to error → forces fallback
)
```

### Step 4 — Diff

```python
# TODO post-v3.13.8:
diff = compare_results(canonical_result, freelance_result)
# diff structure:
# {
#   "widget_html_bytes": {"canonical": N, "freelance": M, "delta": pct},
#   "action_labels": {"canonical": [...], "freelance": [...], "drift": [...]},
#   "dispatch_payload": {"canonical": "apply choices: [...]", "freelance": "sendPrompt(...)"},
#   "events_written": {"canonical": [...], "freelance": [...], "missing_in_freelance": [...]},
#   "leak_findings": {"canonical": [], "freelance": [...]},
# }
```

### Step 5 — Generate .docx comparison artifact

```python
# TODO post-v3.13.8:
generate_comparison_docx(diff, output_path)
# .docx structure:
#   §1 Executive verdict (which path is correct per §3.6 ladder)
#   §2 Widget HTML side-by-side screenshots (rendered via PDF preview)
#   §3 Action labels diff table
#   §4 Dispatch payload diff
#   §5 Event-write diff (events missing in freelance highlighted)
#   §6 Leak-scanner findings
#   §7 §3.6 ladder verdict — does skill match its canonical surface?
```

### Step 6 — Surface to chat

```
compare canonical vs freelance for email-writer

CANONICAL PATH (§2.1 file-URI transport):
- Widget bytes: 43,488
- Actions: send / edit then send / draft / skip (canonical lowercase ✓)
- Dispatch: apply choices: [{"n":"1","action":"send"}]
- Events: email_drafted, email_sent (2)
- Leak scan: clean

FREELANCE PATH (forced fallback):
- Widget bytes: 28,200 (-35%)
- Actions: Send / Edit & send / Save to drafts / Discard (Rule 6 violations ✗)
- Dispatch: sendPrompt('Create the email and send to...')
- Events: NONE (silent non-write per Bug #39)
- Leak scan: clean

§3.6 LADDER VERDICT: email-writer should use Path B1 editor card.
- Canonical render currently produces Path A batched widget (overshooting ladder)
- Freelance render produces a different shape entirely

Recommended fix: email-writer's canonical render path should be tuned to Path B1 single-recipient editor card per §3.6. File this as a polish bug for v3.13.8.1.

View comparison artifact: _hq/render-path-diffs/email-writer_2026-05-25.docx
```

## What this skill validates

Per V3.13.8_MASTER_PLAN §3.6 ladder + Bug #46:

| Skill | Expected canonical surface per ladder |
|---|---|
| email-writer (compose-new, n=1, has email) | Path B1 editor card |
| email-writer (compose-new, n>1) | Path A batched widget |
| email-writer (compose-new, n=1, no email) | Path B2 recovery widget (Bug #44) |
| intro-broker (n=2, both have emails) | Path A 2-direction batched widget |
| follow-up-ritual (n=1) | Path B2 confirmation card |
| thread-resurrection (n=1) | Path B2 confirmation card |
| calendar-writer (n=1 invite-confirm) | Path B2 (M's locked product call from B1-4) |
| calendar-writer (single decision) | Path D AskUserQuestion |
| commitments scheduled | Path A canonical batched widget |
| show-my-list | Path A canonical batched widget |
| list-active | chat-mode synthesis (no widget) |

This skill produces a per-skill verdict on whether the canonical render matches its declared ladder surface.

## Failure modes

**Pre-v3.13.8:** skill returns "BLOCKED — §2.1 file-URI transport must ship first."

**Post-v3.13.8:** if `render_and_relay()` not found at expected path, surface clear error.

## Implementation TODO (post-v3.13.8)

Once v3.13.8 §2.1 lands:

1. Implement `run_skill_with_transport_mode()` — invoke skill code path through forced canonical OR freelance transport
2. Implement `compare_results()` — structured diff per fields above
3. Implement `generate_comparison_docx()` — uses §2.2 brief_writer table primitives + §2.4 universal leak scan
4. Wire to fixture system (uses synthetic-workspace-runtime-test fixtures for test inputs)
5. Validate against email-writer (highest-value first test target)

Estimated implementation: 2-3 hours post-v3.13.8.

## Companion to other chalette skills

- `verify-cr-release` — M-attended Cowork loop (catches LLM-side behavior)
- `synthetic-workspace-runtime-test` — pure runtime substrate gate (catches code-path issues)
- **this skill** — render-path adherence to §3.6 ladder (catches widget-shape drift)

Three orthogonal gates. None substitutes for the others.

## Connection to V3.13.8_MASTER_PLAN

This skill specifically validates:
- §2.1 file-URI transport lands (otherwise this skill BLOCKED)
- §3.6 widget degradation ladder codified correctly
- §3.7 action-label canonical enforcement (this skill's diff surfaces non-canonical labels)
- §2.4 universal post-render leak scan (this skill runs it on both paths)

If v3.13.8 ships and this skill reports drift for any of the 10+ widget-rendering skills → that drift is a v3.13.8.1 patch candidate.
