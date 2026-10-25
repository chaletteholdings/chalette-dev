# Fire-mocking

How to invoke skill code paths against a synthetic workspace without going through the full Cowork → Claude Code SDK round-trip.

## Why mocking

The skill needs to assert runtime invariants on canonical-scope surfaces. Full Cowork round-trips are too slow (~10 sec per fire) + Cowork-dependent. A minimal mock that exercises the skill's code paths against fixture substrate runs in ~30 sec for all 7 surfaces × 4 fixtures = 28 fires.

## Mock surface

```python
class SyntheticFireRunner:
    """
    Invokes a Command Room skill's code path against a synthetic workspace fixture.
    Captures: tool calls, events appended, widget HTML emitted, chat narration.
    """
    
    def __init__(self, plugin_root: Path, workspace_root: Path, surface: str):
        self.plugin_root = plugin_root
        self.workspace_root = workspace_root
        self.surface = surface
        self.tool_trace = []
        self.events_appended = []
        self.widget_html = []
        self.chat_narration = []
        
    def fire(self, trigger: str) -> FireResult:
        """
        Read the surface's SKILL.md/orchestrator file.
        Set up environment so canonical helpers point at fixture's substrate.
        Invoke the orchestrator's Phase 1 → Phase N sequence as a subprocess.
        Capture all side effects.
        """
        env = os.environ.copy()
        env["WORKSPACE_ROOT"] = str(self.workspace_root)
        env["CLAUDE_CODE_TMPDIR"] = str(self.workspace_root.parent / ".tmp")
        env["SYNTHETIC_FIRE_MODE"] = "1"  # canonical helpers consult this to skip Cowork-side calls
        
        # Hook tool calls
        with self._trace_tools():
            result = self._run_orchestrator(trigger, env)
        
        return FireResult(
            tool_trace=self.tool_trace,
            events_appended=self.events_appended,
            widget_html=self.widget_html,
            chat_narration=self.chat_narration,
            exit_code=result.exit_code,
            exception=result.exception,
        )
```

## Hook strategy

Two hook layers:

### Layer 1 — Substrate hooks (always active in synthetic mode)

Set `SYNTHETIC_FIRE_MODE=1`. Canonical helpers that read substrate point at fixture paths instead of the owner's workspace. No mocking — just env-var redirection.

Helpers respecting `SYNTHETIC_FIRE_MODE`:
- `cru_match.py::load_open_commitments(workspace_root=...)` — explicit param already
- `entity_resolve.py::resolve_all(query, workspace_root=...)` — explicit param already
- `brief_writer.py::make_brief(workspace_root=...)` — explicit param already
- `atomic_write.py::atomic_write_locked(path)` — derived from workspace_root
- `next_seq.py::next_seq(events_jsonl_path)` — explicit param already

All helpers should accept `workspace_root` explicitly (audit pass during v3.13.8 if any don't).

### Layer 2 — Tool-call interception (specific to test mode)

Intercept these tools to trace + capture without round-tripping to Cowork:

```python
# Mocks for chalette test harness
@patch("mcp.visualize.show_widget")
def mock_show_widget(html_or_uri: str):
    self.widget_html.append(html_or_uri)
    return {"status": "shown"}

@patch("anthropic.messages.create")
def mock_llm_call(*args, **kwargs):
    # When skill needs an LLM call for synthesis (rare in scheduled-task path),
    # return a canned response from fixture. NEVER make real API call in test mode.
    raise NotImplementedError("Synthetic mode does not make real LLM calls")

@patch("connectors.gmail.search")
@patch("connectors.calendar.list_events")
@patch("connectors.granola.get_meeting_transcript")
def mock_connectors(*args, **kwargs):
    # Return canned responses from fixture's _hq/connectors/<connector>_responses.json
    return fixture_response(args[0])
```

## Invoking orchestrator code paths

Scheduled-task orchestrators live as markdown files in `skills/enable-command-room-schedules/references/orchestrator-*.md`. To invoke them in synthetic mode, the skill reads the orchestrator markdown + executes its phases programmatically.

Pseudocode:

```python
def invoke_orchestrator(surface_name: str, trigger: str, workspace_root: Path) -> FireResult:
    orchestrator_path = (
        PLUGIN_ROOT / "skills/enable-command-room-schedules/references" /
        f"orchestrator-{surface_name}.md"
    )
    orchestrator = parse_orchestrator_markdown(orchestrator_path)
    
    runner = SyntheticFireRunner(PLUGIN_ROOT, workspace_root, surface_name)
    
    for phase in orchestrator.phases:
        runner.execute_phase(phase, trigger)
    
    return runner.result
```

`parse_orchestrator_markdown()` reads the phase structure (Phase 1, Phase 2, etc.) and `execute_phase()` runs the python code blocks + helper invocations the phase specifies.

This is approximate — real orchestrator execution is LLM-driven (Cowork interprets the markdown). The synthetic harness exercises the deterministic code paths (helper invocations, substrate reads, event writes) but mocks the LLM-driven prose synthesis.

## What the synthetic mode CANNOT catch

- Cowork-side LLM judgment quality
- Voice / tone of generated content
- the owner's subjective quality assessment

For those: use the attended tier — `battery --attended`, walked by hand (dogfood plus
`battery/references/VERIFICATION_PLAN.md`). No skill orchestrates it.

## What the synthetic mode CAN catch (the high-leverage stuff)

- Canonical helper not invoked when it should be (Bug #11 / #45 / #52 / #53 class)
- Events written but not matching canonical shape (Bug #34 / #43 / #49 class)
- Defensive readers crashing on malformed substrate (Sub-bug #14b class)
- Widget HTML containing leak tokens (Bug #54 / #57 / #59 class)
- Multi-write atomic-lock deadlock (Bug #20 class)
- Schema-enum violations (Bug #43 class)

These are the bug classes that the attended Cowork loop catches slowly, but synthetic-runtime catches in 30 seconds.

## Trace capture format

The runner captures structured traces:

```python
@dataclass
class FireResult:
    surface: str                 # e.g. "morning-briefing"
    fixture: str                 # e.g. "mature_workspace"
    tool_trace: list[dict]       # [{tool: "render_chat_output_widget", args: {...}, return: {...}}, ...]
    events_appended: list[dict]  # the actual events written to events.jsonl
    widget_html: list[str]       # all rendered widget HTML (canonical OR freelance — caught either way)
    chat_narration: str          # captured natural-language between-tool narration
    exit_code: int               # 0 if no exception, non-zero on crash
    exception: Exception | None
    duration_ms: int             # for speed observation
```

This is what `verify_invariants()` consumes.

## Limitations + escape hatches

If a skill's code path is too entangled with Cowork-side LLM behavior to mock cleanly (e.g., heavy use of LLM-generated content as substrate input), the synthetic harness can be configured to:

1. **Skip:** mark the surface as "synthetic-incompatible" + don't run the runtime gate on it. Surface this in skill output so M knows.

2. **Stub:** use a fixture-provided canned LLM response. Trace this clearly — the test only validates the deterministic code path, not the LLM judgment.

3. **Real LLM in test mode:** with explicit env-var override `SYNTHETIC_ALLOW_REAL_LLM=1`. Slower + non-deterministic + costs tokens. Only for very specific test cases.

Default: skip with surfaced message. M can opt into stub or real-LLM modes per fire.
