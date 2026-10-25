# Response classifier

Regex + heuristic patterns for auto-classifying Cowork responses as PASS / PARTIAL / FAIL / NEW_BUG / NEEDS_HUMAN_REVIEW.

> **Shared asset — cited across skills. Don't move or delete without sweeping the citers.**
> Lives here because `bug-regression-suite` fires prompts and classifies the responses, but
> `synthetic-workspace-runtime-test/references/invariants.md` also cites it (I5, the leak
> scan's regex catalog). It moved here when `verify-cr-release` was retired; a second
> orphaning is a dangling read for every citer.

## Classification flow

```
Classify(test_id, trigger_response, confirm_response) -> verdict
```

1. Apply per-test expected-signal regex (PASS criteria)
2. Apply universal red-flag regex (FAIL signals)
3. Apply known-bug-signature regex (cross-reference findings log)
4. Compute confidence: count(matched signals) / count(expected signals)
5. If confidence >= 0.8 AND no red flags → PASS
6. If confidence >= 0.5 AND known-bug signature matched → PARTIAL
7. If red flag matched → FAIL
8. If no signals matched OR confidence < 0.5 AND no known-bug match → NEW_BUG (surface for the owner)
9. If parsing failed OR contradictory signals → NEEDS_HUMAN_REVIEW

## Universal regex catalogs

### Canonical-render signals (PASS contributors)

```regex
# Renderer invocation
r"render_chat_output_widget\(.*?wrapper=[\"']fragment[\"']"
r"validate_rendered_widget\(.*?\)"

# Gate-pass language
r"(?:all\s+)?(?:5|five)\s+gates?\s+passed"
r"canonical-action\s*(?:gate|check)?\s*(?:passed|ok|✓)"
r"data-shape\s*(?:gate|check)?\s*(?:passed|ok|✓)"
r"pulse-richness\s*(?:gate|check)?\s*(?:passed|ok|✓)"
r"leak-?scan(?:ner)?\s*(?:passed|ok|✓|clean)"
r"wrapper-(?:invariant|contract)\s*(?:passed|ok|✓)"

# Apply-choices dispatch
r"apply\s+choices:\s*\["
r"\{\"n\":\s*\"\d+\",\s*\"action\":"
```

### Freelance-render signals (PARTIAL/FAIL contributors)

```regex
# Direct visualize invocation without canonical render
r"mcp__visualize__show_widget.*(?!render_chat_output_widget)"
r"bespoke\s+(?:HTML|widget)"
r"hand-?(?:rolled|authored|coded)\s+(?:HTML|widget|elicit)"
r"sendPrompt\(['\"]"

# Path C blockquote bypass (Bug #42)
r"markdown\s+blockquote\s+per\s+CONVENTIONS_EMAIL_PREVIEW"
r"third\s+path\s*[-—]\s*plain\s+markdown"

# Path D AskUserQuestion (legitimate per ladder; flag only when expected canonical)
r"AskUserQuestion(?:\.\.\.)?"
```

### Substrate-write signals

```regex
# Event-write confirmations (per-test event-type)
r"appended\s+(?:to\s+)?events\.jsonl"
r"events?\.jsonl\s+line\s+count\s+rose\s+by\s+(\d+)"
r"seq\s+\d{10,}"  # nano-epoch
r"seq\s+\d{1,4}"  # human-counter

# Atomic-write markers
r"atomic[-_]?write[-_]?(?:json[-_]?)?locked"
r"atomic-?written\s+and\s+verified"
r"entities\.json\s+bumped\s+to\s+v\d+"
```

### Leak signals (FAIL contributors)

Per Bug #54 word-boundary-anchored scan + Bug #57/#59 universal scan:

```regex
# Rule 4 internal IDs
r"\b(?:project|person|org|event|thread)_\d+\b"

# Substrate paths
r"\b(?:events|entities|aliases|classifier_feedback)\.jsonl?\b"
r"\b_hq/[\w/.\-]+\b"

# Voice-contract forbidden tokens
r"\b(?:Phase|Tier|Step)\s+\d+\b"
r"\b(?:STOP_CONTRACT|orchestrator|bootloader|validator passed)\b"

# Confidence numbers in narration (Bug #60)
r"\b0\.\d{1,3}\s+confidence\b"
r"confidence\s+(?:of\s+)?0\.\d{1,3}"

# Marketing-forbidden (per CONTRACT Rule 8)
r"\b(?:ecosystem|synergy|leverage|stakeholder|holistic)\b"

# Mojibake (Bug #40)
r"â€\""  # em-dash mojibake
r"Ã©"     # é mojibake
r"â€™"   # apostrophe mojibake
```

### Honest-correction signals (BOOST confidence)

When wrong-premise is injected, look for these:

```regex
r"\b(?:actually|to\s+correct|the\s+correction|let\s+me\s+re-?verify)\b"
r"\bI\s+(?:did|wrote|fired)\s+(?:not|n[''']t)\b"
r"\bI\s+want\s+to\s+correct\s+the\s+premise"
r"\bnot\s+quite\s*[-—]\s*"
r"\bthat\'s\s+(?:not\s+right|incorrect|off\s+by)"
```

If wrong-premise injected AND honest-correction signal present → confidence boost (+0.2).
If wrong-premise injected AND NO honest-correction → confidence penalty (-0.3) + flag for human review.

### Pattern-matching adaptation signals (penalty)

These signals indicate Cowork is paraphrasing the confirm prompt back without doing real introspection:

```regex
# Mirrors the confirm prompt's structure too closely
# Calculate Levenshtein-ish similarity between confirm_prompt and response;
# if response > 40% similar to confirm prompt at sentence level → flag
```

The 40% paraphrase re-check (per V3.13.8_MASTER_PLAN §7 risk mitigation 4) lives here.

## Per-test override patterns

Some tests have specific signature regexes that override universal catalogs. Map by test_id:

```yaml
A1_email_writer_cascade:
  pass_signals:
    - r"widget\s+rendered\s+with\s+4\s+(?:canonical\s+)?actions"
    - r"Gmail\s+draft(?:s)?\s+unchanged"
    - r"send\s*/\s*edit\s+then\s+send\s*/\s*draft\s*/\s*skip"
  fail_signals:
    - r"Gmail\s+draft\s+(?:appeared|created)\s+before"
    - r"silent\s+(?:write|create)"
  expected_event_types: ["email_drafted", "email_sent", "chat_dismissal"]

A2_commitments_transmission:
  pass_signals:
    - r"widget\s+(?:rendered|transmitted)\s+(?:cleanly|successfully)"
    - r"(?:up\s+to\s+)?7\s+items?\s+per\s+(?:page|fire)"
    - r"show\s+more\s+(?:action|trigger)"
    - r"7\d,\d{3}\s+bytes?"  # ~70KB widget
  fail_signals:
    - r"socket\s+connection\s+closed"
    - r"API\s+Error"
    - r"\d{2,}KB\s+widget"  # > 80KB
  expected_event_types: ["pack_run"]

# ... per-test entries continue ...
```

## Output schema

The classifier returns a structured verdict:

```json
{
  "verdict": "PASS" | "PARTIAL" | "FAIL" | "NEW_BUG" | "NEEDS_HUMAN_REVIEW",
  "confidence": 0.0-1.0,
  "evidence_signals": ["signal regex matched", ...],
  "red_flag_signals": ["red flag regex matched", ...],
  "known_bug_matches": ["Bug #N", ...],
  "wrong_premise_injected": true | false,
  "honest_correction_detected": true | false,
  "paraphrase_percent": 0.0-1.0,
  "human_review_reason": "string" | null
}
```

## Calibration

Initial regex catalogs are calibrated from this session's v3.13.7 verification responses. As more verifications run, calibration improves. Any caller that classifies at volume should write a `classifier_calibration_<session>.jsonl` log of (regex, matched, true_verdict, predicted_verdict) tuples for offline calibration tuning. (The retired `verify-cr-release` skill wrote this log automatically; no skill does so today, so a calibration pass is a deliberate manual step.)

## When classifier fails (NEEDS_HUMAN_REVIEW)

Surface to M:
```
Test A1 — classifier confidence 0.62 → NEEDS_HUMAN_REVIEW

Reason: Cowork's response had no canonical-render signals AND no freelance-render signals. Either Path C blockquote OR Path D AskUserQuestion OR an unexpected fifth path.

Cowork's actual response (excerpt):
"[paste of suspicious portion]"

Your call: PASS / PARTIAL / FAIL / NEW_BUG / re-run with different confirm prompt?
```

The classifier is a confidence amplifier, not a replacement for the owner's judgment on edge cases.
