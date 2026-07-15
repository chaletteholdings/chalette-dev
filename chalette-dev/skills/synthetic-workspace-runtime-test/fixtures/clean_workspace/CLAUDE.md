# Command Room workspace

Synthetic fixture workspace. Not a real customer workspace; every entity here is
generated placeholder data.

## Substrate

- `_hq/data/entities.json` -- people, orgs, projects
- `_hq/data/events.jsonl` -- append-only event log
- `_hq/data/aliases.json` -- canonical-name registry

## Rules

- events.jsonl is append-only. Never rewrite it.
- All writes go through `atomic_append_jsonl`.
- Superseded files move to `_archive/`; nothing is deleted.
