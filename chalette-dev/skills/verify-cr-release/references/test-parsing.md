# Test-plan parsing

How to parse a verification plan markdown into a structured test list.

## Expected plan structure

The reference plan is `Desktop/Claude/Command Room/COMPREHENSIVE_VERIFICATION_PLAN_2026-05-23.md`. Format:

```markdown
## Phase 0 — Update Cowork (do this FIRST)

☐ **0.1** — [step description]

☐ **0.2** — Paste: `[trigger]`
  - **Should see:** [pass criteria]
  - **🚩 If [condition]:** [red flag]

## Phase A — v3.13.7 Tier 1 ship-blocker verification (8 items)

### A1 — Bug #4 — Email-writer cascade (SHIP BLOCKER #1)

☐ Paste: `[trigger prompt]`

- **Should see:** [pass criteria]
- **CRITICAL:** [hard-stop condition]
- Click `send` → [expected behavior]
- **🚩 RED FLAG:** [red flag pattern]
```

## Parsing algorithm

```python
def parse_plan(plan_path: Path) -> list[dict]:
    """
    Parse markdown into list of test dicts:
    [
      {
        "id": "0.1" | "A1" | "B1-1",
        "phase": "0" | "A" | "B-Tier 1",
        "name": "Cowork update" | "Bug #4 email cascade" | ...,
        "trigger_prompt": "command room update" | "...",
        "pass_criteria": ["plugin v3.13.8 confirmed", ...],
        "red_flags": ["draft appears before click", ...],
        "expected_events": ["email_drafted", "email_sent", "chat_dismissal"],
        "is_ship_blocker": True | False,
        "known_bug_id": 4 | 14 | 19 | ...,
        "subsequent_actions": [
            "click `send` → verify Gmail draft created + sent",
            "click `edit then send` → inline editor opens",
            ...
        ],
        "confirm_prompt_hint": "verify lazy-Gmail contract held"  # for prompt template selection
      },
      ...
    ]
    """
    content = plan_path.read_text()
    
    tests = []
    
    # Phase regex: "## Phase X — name" or "## Phase X-Tier Y — name"
    phase_pattern = re.compile(r"^##\s+Phase\s+(\d+|[A-Z](?:-Tier\s+\d+)?)\s+[—-]\s+(.*?)$", re.MULTILINE)
    
    # Test regex: "### X.Y — Bug #N — name" or "### X.Y — name" or just "☐ **X.Y** — name"
    test_pattern = re.compile(
        r"(?:^###\s+([A-Z]?\d+(?:-?\d+)?(?:\.\d+)?)\s+[—-]\s+(.*?)$|"
        r"^☐\s+\*\*([A-Z]?\d+(?:-?\d+)?(?:\.\d+)?)\*\*\s+[—-]\s+(.*?)$)",
        re.MULTILINE
    )
    
    # Trigger regex inside a test block: "☐ Paste:\n```\n[trigger]\n```"
    trigger_pattern = re.compile(
        r"☐\s+Paste:\s*\n```\n(.+?)\n```|"
        r"☐\s+Paste:\s+`(.+?)`",
        re.DOTALL
    )
    
    # Pass-criteria regex: "**Should see:** [criteria]" or "- ✅ [criteria]"
    pass_pattern = re.compile(
        r"\*\*Should see:\*\*\s+(.+?)$|"
        r"-\s+(?:✅|✓)\s+(.+?)$",
        re.MULTILINE
    )
    
    # Red-flag regex: "🚩 [flag]" or "**🚩 RED FLAG:** [flag]"
    red_flag_pattern = re.compile(
        r"(?:🚩\s+(?:\*\*)?(?:RED FLAG:?)?\*?\*?\s*)(.+?)$",
        re.MULTILINE
    )
    
    # ... extract and structure ...
    
    return tests
```

## Parsing fallback

If the plan markdown doesn't match expected structure:

```python
def parse_with_fallback(plan_path: Path) -> list[dict]:
    try:
        tests = parse_plan(plan_path)
        if len(tests) < 3:  # implausibly few tests
            raise ValueError("Parse produced too few tests")
        return tests
    except (ValueError, re.error, Exception) as e:
        # Surface to M
        print(f"Plan parsing failed: {e}")
        print("Falling back to manual test list. Paste tests one at a time as: <id> | <name> | <trigger>")
        # M provides interactively
        return manual_test_entry()
```

## Cross-reference with findings log

For each parsed test, look up the bug catalog (the findings log) to populate `known_bug_id`:

```python
def cross_reference_bug_catalog(test: dict, findings_log_path: Path) -> dict:
    """
    If test name mentions "Bug #N", populate known_bug_id.
    If test name doesn't mention but trigger matches a known bug's symptom regex,
    populate via heuristic.
    """
    log_content = findings_log_path.read_text()
    
    # Look for "Bug #N" in test name
    m = re.search(r"Bug\s+#(\d+)", test["name"])
    if m:
        test["known_bug_id"] = int(m.group(1))
        # Pull bug record from findings log
        test["bug_context"] = extract_bug_context(log_content, int(m.group(1)))
    
    return test
```

## Test ordering + phase gates

Tests should preserve plan ordering — the plan author put them in dependency order. The skill must:
- Respect order from the markdown
- Respect explicit `prerequisite` references (e.g., "A1 must pass before A2 can fire")
- Honor phase decision gates (see `phase-decision-gates.md`)

## Plan format extensions

For the verify-cr-release skill, the plan can optionally use these markdown extensions:

```markdown
### A1 — Bug #4 — Email-writer cascade

<!-- VERIFY-CR-RELEASE-METADATA
prerequisite: 0.1, 0.2, 0.3
ship_blocker: yes
known_bug: 4
expected_events: email_drafted, email_sent, chat_dismissal
confirm_variant_lock: A
-->

☐ Paste: `draft email to David Williams about getting lunch next Thursday`

- **Should see:** widget renders with `send / edit then send / draft / skip`
...
```

The HTML-comment metadata block is OPTIONAL — if absent, the parser uses heuristic detection. If present, it overrides heuristics. Plan authors can lock down test behavior via this block.

## State persistence

The parser writes parsed tests to `_hq/verify-runs/<session_id>/parsed_tests.json`. On `continue verification`, the parser re-reads this file rather than re-parsing the plan markdown (so test order is stable across resumes even if M edits the plan in flight).

## Idempotency

Calling `parse_plan()` twice on the same file should produce identical results. The parser MUST be deterministic — no ordering depending on filesystem iteration, no time-dependent fields populated, etc. This is critical for resume behavior.
