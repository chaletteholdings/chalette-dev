# Invariant catalog

The full list of runtime invariants the skill asserts after every canonical-surface fire.

## Invariant categories

1. **Render-path invariants** — verify canonical path actually invoked
2. **Substrate-write invariants** — verify events written + correct shapes
3. **Leak-token invariants** — verify no forbidden tokens in any output surface
4. **Defensive-read invariants** — verify substrate-hygiene readers tolerate malformed lines
5. **Canonical-helper invariants** — verify entity_resolve / load_open_commitments / brief_writer invoked
6. **Voice-contract invariants** — verify process narration scrubs internal mechanism names

## Per-invariant detail

### I1 — canonical_render_invoked

**Test:** `render_chat_output_widget()` is called on every fire that produces a widget surface.

**How:** trace `import` + function-call hooks on the canonical renderer. If `mcp__visualize__show_widget` is called WITHOUT `render_chat_output_widget()` having been called first → fail.

**Why:** Bug #32 root cause — model bypasses canonical render at the transport step.

### I2 — no_freelance_render

**Test:** `mcp__visualize__show_widget` is NOT called via the freelance path (i.e., always via canonical render's file-URI transport per §2.1).

**How:** check that `mcp__visualize__show_widget` calls come through `widget_transport.render_and_relay()` helper, not directly.

**Why:** Bug #32 + Bug #38 + Bug #39 + Bug #44 all rely on canonical path being the default.

### I3 — pack_run_written

**Test:** Every scheduled-task fire writes exactly one `pack_run` event at Phase 8 (or equivalent telemetry phase) with `data.kind`, `data.surfaced`, `data.duration_ms` populated.

**How:** scan events.jsonl post-fire for pack_run with type=pack_run, source_skill=<surface_name>, data.kind=<expected>.

**Why:** Bug #61 — 60% telemetry blindness fix.

### I4 — pack_run_kind_populated

**Test:** `pack_run.data.kind` is NOT null/missing/"unknown".

**How:** Bug #61's specific failure pattern — 54/191 fires logged as `unknown` kind.

### I5 — no_leaks

**Test:** No leak tokens in widget HTML OR chat narration OR appended event data fields.

**How:** Tag-stripped run-collapsed word-boundary-anchored scan per Bug #54 refinement. Regex catalog per `response-classifier.md` in verify-cr-release.

**Why:** Bug #54 / #57 / #59 / #60 — universal leak gate.

### I6 — defensive_read_invoked

**Test:** Any code path that reads events.jsonl uses `_load_events_defensively()` (per §2.7 Layer 2).

**How:** trace `json.loads(line)` patterns vs the canonical helper.

**Why:** Sub-bug #14b — silent corruption masking prevention.

### I7 — canonical_entity_resolve

**Test:** Any name resolution from loose input goes through `entity_resolve.py::resolve_all()`, not substring grep.

**How:** trace `entity_resolve` import + invocations vs raw `re.search(name, entities_json)` patterns.

**Why:** Bug #45 — 10-skill cross-skill enforcement.

### I8 — canonical_load_open_commitments

**Test:** Any commitment-surface read goes through `cru_match.load_open_commitments()`.

**How:** trace `load_open_commitments` invocations vs raw events.jsonl scans with closure-suppression logic.

**Why:** Bug #52 — morning-briefing freelance scan fix.

### I9 — canonical_brief_writer

**Test:** Any `.docx` output goes through `brief_writer.make_brief()`.

**How:** trace `make_brief` invocations vs `docx-js` / `python-docx` direct hand-rolled invocations.

**Why:** Bug #53 — 6-skill brief_writer migration.

### I10 — schema_compliance

**Test:** Every event written has `type` in the events.schema.json enum.

**How:** parse events.schema.json enum at fire start; assert every appended event.type ∈ enum.

**Why:** Bug #34 (person_added) + Bug #43 (followup_pack_drafted) + Bug #49 (schema audit) — schema-additive policy.

### I10b — event_gate_routed

**Test:** Any surface that wrote events routed those writes through `append_event` (i.e. through `atomic_append_jsonl`, where the event gate lives).

**How:** if `result.wrote_events` is true, assert `result.called("append_event")`; a landed unsanctioned type or a write that skipped `append_event` means the surface bypassed the gate.

**Why:** the strict event gate now lives inside `atomic_append_jsonl` (cr1 Phase 4, 2026-07-02, confirmed live by BUILD_SB1's Gate-3 audit). This checks the live routing invariant from the read side — paired with I10 (schema_compliance) under SKILL.md Invariant 7. (CONSOL1 D6: re-added; the transition-era "rig-hygiene" grep prose was dropped.)

### I11 — closure_canonical_shape

**Test:** Closure events (`commitment_resolved` / `thread_resolved` / `commitment_superseded` / `decision_resolved` / `decision_superseded`) use canonical shape:
- `commitment_resolved`: `data.commitment_id` = closed event's seq
- `thread_resolved`: `data.thread_id` = thread ref
- `*_superseded`: `data.supersedes_seq` populated

**Why:** v3.11.4 canonical closure shape + Bug #51 cascade-close pattern.

### I12 — show_my_list_cascade

**Test:** When show-my-list resolves a discuss-wrapper, the source commitment ALSO gets resolved (per §2.9 cascade fix).

**How:** fire show-my-list → click `resolved` on a wrapper → assert 2 commitment_resolved events written (wrapper + source).

**Why:** Bug #51.

### I13 — voice_contract_narration

**Test:** Chat narration during between-tool-call execution does NOT contain forbidden tokens per Bug #16 / #60 voice contract.

**How:** Scan chat narration text (capture from skill's stdout/stderr during execution) for: `project_NNN`, `0.\d+ confidence`, `Phase \d+`, `STOP_CONTRACT`, `bootloader`, `validator passed`, file paths.

**Why:** Bug #16 + #60.

### I14 — atomic_write_multi_safe

**Test:** When multiple writes happen in one fire (e.g., update-bridge migration), the `multi_write_context()` helper holds the lock once across all writes.

**How:** trace lock-acquire/release events; ensure single acquire-release pair around the batch, not N pairs.

**Why:** Bug #20 + #18 + #21 — atomic-write hardening per §2.14.

### I15 — apply_choices_canonical_dispatch

**Test:** Widget action clicks dispatch via canonical `apply choices: [...]` payload, NOT via sendPrompt natural-language indirection.

**How:** trace post-widget-click message handling; assert apply-choices skill invoked with structured payload.

**Why:** Bug #38 + #39 — dead handler fixes.

### I16 — file_uri_transport

**Test:** Widget HTML > 5KB transmits via file-URI transport, not byte-relay through tool parameter.

**How:** assert `render_chat_output_widget(persist_to=...)` was called; assert `mcp__visualize__show_widget` received `file_uri` parameter, not raw HTML.

**Why:** Bug #32 root cause fix.

### I17 — leak_scan_invoked_post_render

**Test:** Every `make_brief()` invocation runs `docx_leak_scanner.scan()` on the output.

**How:** trace `docx_leak_scanner` invocations post-write.

**Why:** Bug #57 + #59 — universal post-render scan gate.

### I18 — closure_reversal_check

**Test:** Revival/re-engagement actions (thread-resurrection, intro-broker, follow-up-ritual) check for prior closure directives before action.

**How:** assert `check_closure_reversal.py` (or equivalent helper) called when target person has prior `thread_resolved` / `chat_dismissal` events.

**Why:** Strength #20 codification.

## Per-fixture expected outcomes

The skill runs each fixture against each canonical surface; expected outcomes per fixture:

### `clean_workspace`

ALL 18 invariants should pass on every surface. Any failure = bug regression.

### `mature_workspace`

- I6 (defensive_read_invoked) MUST pass (fixture has malformed lines that trigger the codepath)
- I3 (pack_run_written) MUST pass with kind populated
- I7 (canonical_entity_resolve) MUST pass (fixture has multi-Daniel collision)
- Otherwise same as clean

### `degraded_workspace`

- I12 (show_my_list_cascade) MUST pass against fixture's wrapper + source pair
- I11 (closure_canonical_shape) tested against fixture's mislabeled supersedes
- I10 (schema_compliance) tested against fixture's unsanctioned event types (should detect + flag)

### `fresh_install`

- I3 (pack_run_written) MUST pass even on first fire
- I7 (canonical_entity_resolve) handles empty alias graph case
- I18 (closure_reversal_check) trivially passes (no prior closures to check)

## Failure-mode logging

When an invariant fails, capture:
- Test ID + fixture name
- Failing invariant
- Evidence: verbatim trace excerpt OR exception message OR substrate excerpt
- Likely cause hypothesis (cross-referenced to known bug catalog)
- Recommended action

Format per `references/findings-log-format.md` in verify-cr-release skill.
