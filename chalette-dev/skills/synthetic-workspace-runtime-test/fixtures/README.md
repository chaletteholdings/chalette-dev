# Fixtures — synthetic-workspace-runtime-test

Each fixture represents a different real-world workspace state. The synthetic-workspace-runtime-test skill copies a fixture to a temp directory + fires the 7 canonical-scope surfaces against it.

## Fixtures provided

| Fixture | Purpose | Status |
|---|---|---|
| `clean_workspace/` | Pristine baseline. Happy-path verification. | **POPULATED** |
| `mature_workspace/` | Realistic 80-person workspace with malformed lines + dual-shape seqs. | **POPULATED** |
| `degraded_workspace/` | Edge-case fixture for Bugs #19/#22/#24/#43/#44. | **POPULATED** |
| `fresh_install/` | Day-1 customer fixture for onboarding + M1 widget tests. | **POPULATED** |

Populated 2026-07-15 (`fixture_version: 1.0`, `compatible_plugin_versions: ["4.8.0"]`). Previously all four were skeletons — only `.metadata.json` existed — which meant every fixture-dependent skill had nothing to run against.

## Do not hand-edit the fixtures

`_generate_fixtures.py` is the source of truth. Edit the generator, re-run, commit the output.

```bash
python _generate_fixtures.py --cr1 ~/repos/cr1            # regenerate all four
python _generate_fixtures.py --cr1 ~/repos/cr1 --check    # validate, write nothing
python _verify_fixtures.py   --cr1 ~/repos/cr1            # verify vs cr1's real readers
```

It is **deterministic** — fixed seed, fixed base dates, no wall-clock. Re-running produces a byte-identical tree and a no-op diff (verified). That is what makes the quarterly shape-refresh below practical: hand-maintaining 1500 events across four fixtures through a refresh isn't realistic; regenerating from a spec is.

## The generator reads the live schema rather than trusting the spec

The 0.1-skeleton metadata was pinned to plugin `3.13.8`–`3.14.0`, and its content assumptions had rotted by 4.8.0. Concretely: `degraded_workspace` was specced to plant `followup_pack_drafted` as an **unsanctioned** event type for the Bug #43 detection test — but that type has since been added to `events.schema.json`. It's legal now, so the fixture would have silently stopped testing the thing it exists to test.

So the generator resolves "unsanctioned" against the live enum at generation time and **asserts** the types it plants are genuinely absent from it. If a future schema addition legalises one, generation **fails loudly** rather than quietly producing a fixture that tests nothing. Same principle as the guard-that-cannot-guard fix in cr1 #32 — a check that can't check must not report success.

Names are read live out of cr1's own `tests/run_no_real_customer_names_test.py` (`APPROVED_FIRST_NAMES` × `APPROVED_SURNAMES`), so this generator cannot drift from the names that repo considers safe.

## `_verify_fixtures.py` drives the real readers

A fixture that merely *looks* right is worse than none — it makes the QA layer report green while testing nothing. So verification drives the actual production helpers, not a reimplementation:

| Check | Helper | Guards |
|---|---|---|
| Schema validity | `jsonschema` vs the canonical schemas | every entity + every event |
| Malformed tolerance | `cru_match.load_events_defensively` | Sub-bug #14b |
| Seq hygiene | `next_seq.next_seq` | Bug #41 nano-epoch |
| Structure | file layout per `fixture-spec.md` | connectors, CLAUDE.md |

Current: **82/82 checks pass.**

## What each fixture carries

### clean_workspace — 10 people · 5 orgs · 3 projects · 206 events

All canonical shapes, no malformed lines, no collisions (10 distinct first names). Seqs 1–206, human-counter. Baseline: any failure here is a real regression.

### mature_workspace — 80 people · 20 orgs · 15 projects · 1500 events

The realistic one. Deliberately **not** clean:

- **8 malformed lines at 100–107** — the Sub-bug #14b shatter pattern: 7 bare-key JSON strings plus 1 truncated event. **This shape matters.** Only the truncated line raises `JSONDecodeError`; the 7 bare strings **parse fine** as top-level JSON strings, and a reader that then calls `.get()` on a `str` gets `AttributeError`. That was the actual crash class. A fixture with only broken-JSON lines would test half the bug.
- **Dual-shape seqs (Bug #41)** — 1200 human-counter (1–1200) + 300 nano-epoch artifacts (1.77e18+). Verified: `next_seq` returns 1201, not an astronomical number.
- **Legacy + canonical event names (Bug #34)** — `person_added` through seq 500, `person_created` after.
- **Both alias shapes** — nested list and flat map in one file, so both defensive read paths get exercised.
- **12 unattributed people** (no org, `needs_enrichment: true`) — the backfill target shape.
- **3 paused projects**, **4 orgs with no domains** (Bug #1).

### degraded_workspace — 15 people · 8 orgs · 5 projects · 100 events

- **First-name collision (Bug #19)** — `Sam Sample` and `Sam Stone`: same first name, distinct full names.
- **2 people with no email (Bug #44)** — the dead-chrome / send-class case.
- **Decision fallback chain (Bug #22)** — decisions with *only* `title`, *only* `summary`, *only* `notes`.
- **2 mislabeled supersedes (Bug #24)** — `commitment_resolved` events carrying `supersedes_seq`: supersedes wearing a completion's label.
- **5 unsanctioned events (Bug #43)** — types verified illegal against the live enum.
- **show-my-list wrapper + source pair** — for the I12 cascade test.

`.metadata.json` marks `I10` as `expected_invariants_fail_intentional`: schema compliance *should* fail here. That's the point — it proves the detection works.

### fresh_install — empty

Empty entities, single seed marker event, no `aliases.json`, no `brain_name` (Bug #36 prompt test). The `workspace_settings` stub is present but **empty**: the schema types `user_timezone` as `string`, not `["string","null"]`, so an unset value must be *omitted*, not written as `null`. A Day-1 workspace genuinely has no timezone yet — that's the shape onboarding fills in.

## Two deviations from the 0.1-skeleton spec — both flagged to M

**1. `degraded_workspace` no longer uses names that read as real contact data.** The skeleton spec named two people whose names were not in cr1's approved placeholder allowlist and one of which matched a real client surname — it looked like real contact data that leaked into the fixture spec. Replaced with approved placeholders (`Sam Sample` / `Sam Stone`), which satisfies the Bug #19 first-name-collision requirement identically.

**2. `mature_workspace.has_first_name_collisions` flipped `false` → `true`.** Two reasons. Mechanically: the approved vocabulary is 11 first names × 2 surnames = 22 unique full names; 80 people cannot avoid collisions. Substantively: an 80-person org with zero repeated first names is exactly the too-clean fixture that produced a bug class in the first place — and `invariants.md` already expects collisions here (*"I7 … fixture has multi-Daniel collision"*), contradicting mature's own metadata. If you want 80 distinct full names, the approved allowlist needs extending; say the word.

## Fixture compatibility

Each fixture's `compatible_plugin_versions` array tracks which plugin versions the fixture supports. Currently `["4.8.0"]`. When the schema gains or loses types, re-run `_verify_fixtures.py` — it will catch a fixture that has silently stopped testing its target — then bump `FIXTURE_VERSION` / `COMPATIBLE` in the generator.

## Quarterly refresh

Per `references/fixture-spec.md`: quarterly shape-diff against the real workspace's **shape** (never a content copy). Update the generator's counts/characteristics to match the new shape, re-run, re-verify. Because generation is deterministic, the diff shows exactly what the refresh changed.

## Scrub-rules compliance

Fixtures use ONLY canonical placeholder names, read live from cr1's `run_no_real_customer_names_test.py`:

- **First names:** Adan, Aria, Bo, Bowie, Dustin, Lyra, Mira, Quinn, Rio, Sam, Skyler
- **Surnames:** Sample (canonical), Stone (disambiguation)
- **Org names:** synthetic placeholders (Acme Co, Northstar Partners, Category Company, …)
- **Email domain:** `@example.com`

If a fixture needs a name outside the approved list, extend the allowlist in cr1's guard **first** — don't hardcode an exception here. Note there's no `scrub-rules.json` in either repo despite older docs referencing one; the guard's `APPROVED_*` sets are the de facto source of truth, which is why the generator reads them directly.
