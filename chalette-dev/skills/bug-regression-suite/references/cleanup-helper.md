# Cleanup helper

Post-suite cleanup logic for substrate artifacts created during regression-suite or adversarial mode fires against M's real workspace.

## Cleanup philosophy

**Conservative — archive, don't delete.** All substrate artifacts created during test fires are preserved with `test_artifact: true` flag + archived status. M can review the audit trail later. Hard delete only on explicit `--hard-delete` flag.

## Pre-fire snapshot format

Before every substrate-modifying test, snapshot:

```
_hq/.system/regression-snapshots/{timestamp}/
├── entities.json.before     # full copy
├── events.jsonl.before      # full copy
├── aliases.json.before      # full copy
├── baseline_counts.txt      # line counts + sha256 hashes
└── tests_planned.json       # which tests will run + which substrate they expect to touch
```

`baseline_counts.txt`:
```
entities.json lines: 156
events.jsonl lines: 1830
aliases.json lines: 42
entities.json sha256: abc...
events.jsonl sha256: def...
```

## Post-fire diff logic

```python
def diff_substrate(snapshot_dir: Path, workspace_root: Path) -> dict:
    """
    Compute delta between snapshot and current state.
    Returns:
    {
      "events_added": [(seq, type, data), ...],
      "entities_added": [(person_id_or_org_id_or_project_id, record), ...],
      "aliases_added": [(raw, canonical_id, type), ...],
      "test_artifact_records": [...],  # records with test_artifact: true
    }
    """
    pre_events = read_jsonl(snapshot_dir / "events.jsonl.before")
    post_events = read_jsonl(workspace_root / "_hq/data/events.jsonl")
    events_added = [e for e in post_events if e["seq"] > max_pre_seq]
    
    pre_entities = read_json(snapshot_dir / "entities.json.before")
    post_entities = read_json(workspace_root / "_hq/data/entities.json")
    
    new_people = {pid: rec for pid, rec in post_entities["entities"]["people"].items()
                  if pid not in pre_entities["entities"]["people"]}
    new_orgs = {oid: rec for oid, rec in post_entities["entities"]["orgs"].items()
                if oid not in pre_entities["entities"]["orgs"]}
    new_projects = {pid: rec for pid, rec in post_entities["entities"]["projects"].items()
                    if pid not in pre_entities["entities"]["projects"]}
    
    # Cross-reference: which adds are tagged test_artifact?
    test_artifacts = identify_test_artifacts(events_added, new_people, new_orgs, new_projects)
    
    return {
        "events_added": events_added,
        "entities_added": {"people": new_people, "orgs": new_orgs, "projects": new_projects},
        "aliases_added": diff_aliases(...),
        "test_artifact_records": test_artifacts,
    }
```

## Cleanup actions per artifact type

### New person/org/project record (test_artifact tagged)

```python
def archive_test_person(workspace_root: Path, person_id: str):
    """
    Sets archived=true + test_artifact=true on the person record.
    Appends person_updated event documenting the cleanup.
    Does NOT delete the record (audit trail preservation).
    """
    from canonical_helpers.people_writer import update_person
    update_person(workspace_root, person_id=person_id, archived=True,
                  test_artifact=True,
                  archive_reason="bug-regression-suite test artifact",
                  archived_at=now_iso())
    # update_person canonically writes person_updated event
```

### New events.jsonl entries (test_artifact tagged)

Events are append-only — cannot be deleted. Instead:

```python
def supersede_test_event(workspace_root: Path, original_seq: int):
    """
    Appends a supersede event documenting the original was a test artifact.
    Downstream consumers should treat the original as not-real-state.
    """
    from canonical_helpers.event_writer import append_event
    append_event(workspace_root, type="event_marked_test_artifact",
                 data={
                    "supersedes_seq": original_seq,
                    "reason": "bug-regression-suite test fire",
                    "marked_at": now_iso()
                 })
```

### New entries in aliases.json

If test fire added aliases (e.g., for a test_artifact person):

```python
def remove_test_aliases(workspace_root: Path, test_person_ids: list[str]):
    """
    Remove aliases pointing at test_artifact persons. Aliases.json is mutable,
    safe to direct-edit. Surrounded by atomic_write_locked.
    """
    aliases = read_aliases(workspace_root)
    cleaned = filter_out(aliases, canonical_id_in=test_person_ids)
    atomic_write_json_locked(workspace_root / "_hq/data/aliases.json", cleaned)
```

### Gmail drafts created during test

Per Bug #4 regression test (fires `draft email to Bo Sample`):

```python
def cleanup_gmail_test_drafts(test_recipients: list[str]):
    """
    Searches Gmail drafts folder for test recipients.
    Deletes drafts created during test window.
    NOTE: requires Gmail MCP connector + delete-draft tool.
    """
    # Use Gmail MCP integration to search + delete
    ...
```

### Scheduled tasks created during test

Per Bug-revisit / decision-revisit tests:

```python
def cleanup_scheduled_test_tasks(test_window: tuple[datetime, datetime]):
    """
    Lists scheduled tasks created during test window with test_artifact tag.
    Disables / removes them via scheduled-tasks MCP integration.
    """
    ...
```

## Cleanup invocation

```bash
run regression suite --cleanup
```

OR after a regression run completes:

```
Bug Regression Suite — run complete.

44 tests fired. 3 substrate modifications detected:
- person_088 created (Bug #19 disambig accidental click)
- 2 commitment events appended (Bug #51 cascade test — both real closures, keep)
- 1 Gmail draft (Bug #4 regression — to bo@example.com)

Cleanup options:
(a) Auto-cleanup person_088 + Gmail draft (recommended); keep the 2 commitment closures
(b) Cleanup everything including the commitment closures (use --hard-cleanup)
(c) Skip cleanup, leave residue for M review

Recommend (a). Say 'cleanup' to fire.
```

## Cleanup audit trail

Every cleanup operation appends a `cleanup_run` event:

```json
{
  "seq": <next>,
  "ts": "<ISO>",
  "type": "cleanup_run",
  "source_skill": "bug-regression-suite",
  "data": {
    "snapshot_dir": "_hq/.system/regression-snapshots/2026-05-26T10-00-00",
    "artifacts_cleaned": {
      "persons_archived": ["person_088"],
      "events_marked_test_artifact": [1830, 1831],
      "gmail_drafts_deleted": ["r1234567"],
      "aliases_removed": []
    },
    "skipped": {
      "commitment_closures": [1832, 1833],  // legitimate, not test artifacts
    }
  }
}
```

This event is itself canonical (not a test artifact). It documents what was cleaned, what was kept, why.

## When cleanup is risky

DON'T cleanup if:
- M has clicked through a disambiguation widget intentionally (the test triggered real intent)
- The test fire created a real-state change M wants to keep (e.g., Bug #51 cascade close was a real closure on a real overdue commitment)
- The snapshot is stale (>24h since test run — substrate has likely evolved beyond what snapshot captured)

In ambiguous cases, surface to M with an explicit list of "found these test_artifact records — archive them?" decision.

## Integration with verify-cr-release findings log

Cleanup events get logged to the canonical findings log alongside the test verdicts. Audit trail is preserved end-to-end.
