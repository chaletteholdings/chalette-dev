# Fixture spec

Directory structure + content rules for synthetic workspace fixtures.

## Directory structure

Every fixture lives at `fixtures/<fixture_name>/` and follows this structure:

```
fixtures/clean_workspace/
├── .metadata.json              # fixture-level metadata (version compat, characteristics, etc.)
├── CLAUDE.md                   # workspace instructions
├── _hq/
│   ├── data/
│   │   ├── entities.json       # canonical entity records
│   │   ├── events.jsonl        # event log
│   │   ├── aliases.json        # canonical alias map
│   │   └── classifier_feedback.jsonl
│   ├── views/                  # auto-regenerated views (optional, can be empty)
│   ├── connectors/             # canned connector responses for mocked Gmail/Calendar/Granola
│   │   ├── gmail_responses.json
│   │   ├── calendar_responses.json
│   │   └── granola_responses.json
│   └── .system/                # hidden infrastructure (backups, cache, tmp — usually empty)
├── _people/                    # direct-report profiles (optional)
└── [Project folders]/          # any project-scoped data
    └── deliverables/
```

## .metadata.json

```json
{
  "name": "clean_workspace",
  "description": "Pristine baseline — 10 people, 5 orgs, 3 projects, all canonical shapes",
  "fixture_version": "1.0",
  "compatible_plugin_versions": ["3.13.8", "3.13.9", "3.14.0"],
  "characteristics": {
    "people_count": 10,
    "orgs_count": 5,
    "projects_count": 3,
    "events_count": 200,
    "aliases_count": 25,
    "has_malformed_lines": false,
    "has_dual_shape_seqs": false,
    "has_unsanctioned_events": false,
    "has_first_name_collisions": false,
    "has_unattributed_people": false,
    "has_paused_projects": false
  },
  "expected_invariants_pass": ["I1", "I2", "I3", "I4", "I5", "I7", "I9", "I10", "I11", "I13", "I14", "I15", "I16", "I17"],
  "expected_invariants_skip": ["I6", "I8", "I12", "I18"]  // not applicable in pristine
}
```

## Fixture characteristics

Each fixture should represent a DIFFERENT real-world workspace state:

### clean_workspace
- All canonical shapes, all clean
- For verifying happy-path doesn't regress

### mature_workspace
- Realistic scale (~80 people, 20 orgs, 15 projects, 1500 events)
- 8 deliberately malformed events.jsonl lines (per a real-workspace line-shatter pattern)
- Mix of nano-epoch + human-counter seqs (per Bug #41 dual-shape)
- Some events use legacy `person_added`, others use canonical `person_created` (per Bug #34)
- Aliases.json uses BOTH nested + flat shapes (per defensive-read pattern)
- For verifying substrate-hygiene migrations + defensive readers

### degraded_workspace
- 2 Daniels with full-name collision (Bug #19 test)
- 1 person with no email on file (Bug #44 dead-chrome test)
- Decision events with title-only / summary-only / notes-only (Bug #22 fallback chain)
- Some commitment_resolved events that are actually supersedes (Bug #24)
- Some unsanctioned event types in events.jsonl (Bug #43)
- For verifying edge-case + recovery behavior

### fresh_install
- Empty entities.json (just workspace_settings stub)
- Empty events.jsonl
- No aliases.json
- Default CLAUDE.md
- No workspace.brain_name set (Bug #36 prompt test)
- For verifying Day-1 + onboarding behavior

## Connector response fixtures

Canned responses for mocked connectors live at `_hq/connectors/<connector>_responses.json`:

```json
{
  "gmail_search": {
    "queries": {
      "in:inbox newer_than:1d": [
        {"thread_id": "thread_001", "subject": "...", "from": "person@example.com", "snippet": "..."},
        ...
      ]
    }
  },
  "calendar_list_events": {
    "windows": {
      "today": [...],
      "next_7_days": [...]
    }
  },
  "granola_get_transcript": {
    "doc_ids": {
      "abc123": {"transcript": "...", "attendees": [...], "duration": "..."}
    }
  }
}
```

When the synthetic runner mocks connector calls, it consults these fixtures. Each fixture should have responses sufficient for all 7 canonical-scope surfaces to fire end-to-end without external API calls.

## Building a new fixture

To add a new fixture (e.g., `team_deploy_workspace` for v3.14.x team-deploy scenario):

1. `mkdir fixtures/<new_name>/`
2. Copy structure from `clean_workspace/`
3. Mutate substrate to match the scenario being tested
4. Write `.metadata.json` per spec above
5. Add canned connector responses
6. Update synthetic-workspace-runtime-test skill's fixture list
7. Validate by running fire-mock against new fixture; confirm expected invariants pass

## Versioning + maintenance

Fixtures are version-controlled in the chalette repo. When a fixture becomes incompatible with newer plugin versions (e.g., schema migrations), bump fixture version + update `compatible_plugin_versions` array. Old fixtures stay for regression testing against old plugin versions.

## Quarterly refresh

Per V3.13.8_MASTER_PLAN §9: quarterly fixture refresh via diff against the owner's current workspace shape (not content — we never copy real customer data into fixtures). The shape-diff process:

1. Inspect the owner's current workspace shape (entity counts, event-type distribution, alias graph density)
2. Compare against `mature_workspace` fixture's shape
3. If material drift → update `mature_workspace` to match new shape
4. Re-bump fixture version
5. Re-run synthetic-workspace-runtime-test against refreshed fixture
