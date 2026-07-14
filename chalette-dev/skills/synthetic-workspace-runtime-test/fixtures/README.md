# Fixtures — synthetic-workspace-runtime-test

Each fixture represents a different real-world workspace state. The synthetic-workspace-runtime-test skill copies a fixture to a temp directory + fires the 7 canonical-scope surfaces against it.

## Fixtures provided

| Fixture | Purpose | Status |
|---|---|---|
| `clean_workspace/` | Pristine baseline. Happy-path verification. | SKELETON |
| `mature_workspace/` | Realistic 80-person workspace with malformed lines + dual-shape seqs. | SKELETON |
| `degraded_workspace/` | Edge-case fixture for Bugs #19/#22/#24/#43/#44. | SKELETON |
| `fresh_install/` | Day-1 customer fixture for onboarding + M1 widget tests. | SKELETON |

All 4 fixtures are currently SKELETONS — only `.metadata.json` files exist. The actual `entities.json` / `events.jsonl` / `aliases.json` / `_hq/connectors/*.json` content needs population in a dedicated build session.

## Population work (separate session, ~3-4 hours)

The synthetic fixtures need careful construction to:
- Match canonical schemas (entities.schema.json + events.schema.json + aliases.schema.json)
- Cover the right edge cases per `.metadata.json` characteristics
- Use ONLY canonical placeholder names (Bo Sample, Rio Sample, etc. per scrub-rules.json) — never real M-workspace data
- Be deterministic + reproducible

Recommended build sequence per fixture:
1. Read `.metadata.json` → understand fixture intent + characteristics
2. Read canonical schemas at `~/.claude/plugins/marketplaces/commandroom1/command-room/shared/data-schemas/`
3. Generate substrate content matching the characteristics
4. Validate against schemas via `python3 -m jsonschema -i events.jsonl events.schema.json` etc.
5. Run `synthetic-workspace-runtime-test [fixture_name]` → confirm expected invariants pass + expected_invariants_skip handled correctly

## Fixture compatibility

Each fixture's `compatible_plugin_versions` array tracks which plugin versions the fixture supports. When v3.13.8 ships → may need fixture updates (e.g., new event types added to schema). Bump fixture_version + extend compatible_plugin_versions when verified.

## Quarterly refresh

Per V3.13.8_MASTER_PLAN §9: quarterly shape-diff against M's actual workspace (never content-copy). Update mature_workspace fixture to match new shape characteristics. Re-validate all 4 fixtures against the latest plugin version.

## Scrub-rules compliance

Fixtures MUST use ONLY canonical placeholder names per `references/PRIVACY_POLICY.md`:
- First names: Sam, Bo, Rio, Skyler, Mira, Aria, Bowie, Lyra, Quinn, Dustin, Adan
- Surnames: Sample (canonical), Stone (disambiguation)
- Org names: Acme Co, Northstar Partners, Category Company
- Email domain: @example.com

If the fixture needs a person/org name NOT in the approved list, add to scrub-rules.json + privacy guard first.
