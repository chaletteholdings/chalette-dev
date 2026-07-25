# chalette-dev — Changelog

(Release history before v0.3.0 lives in `.claude-plugin/plugin.json`'s `description` field.
This file starts at the CONSOL1 release.)

## v0.4.0 (2026-07-24) — TI2: triage-intake routes work out (contributor packet + cr1 BACKLOG)

Capability addition. Skill count unchanged (**16**). Zero trigger changes — `triage-intake`'s
frontmatter description is **byte-identical** to v0.3.1 (verified by diff against the branch base).

### Added — "Routing work out" mode in `triage-intake` (`may_ship` operators ONLY)

The gap: work that a fork contributor could execute cold pooled in the maintainer's own
build-specs queue, where a contributor cannot see it, and ad-hoc handoffs had no gate standing
between triage prose and a contributor's eyes.

An item whose verdict is `SPEC` and which passes the **five-clause suitability test** — target
repo is `cr1_clone`; fully specifiable from repo contents; buildable AND testable against the
battery + synthetic fixtures alone; zero client/org/person names needed in spec, code, tests or
PR text; zero ship authority — now yields two extra outputs:

1. **`<specs_dir>/packets/PACKET_<TAG>.md`** — self-contained for a cold fork contributor:
   handoff header (fork → branch → PR, what the builder never does, the BACKLOG TAG), a spec
   body shaped per cr1's checked-in `templates/TEMPLATE_SPEC.md` with §0 **already ruled**, the
   kickoff prompt, acceptance including the scrub AC verbatim, and a **PR-description
   requirements** block carrying the `TEMPLATE_BUILD_REPORT` slots (deviations at top, gates
   table with numbers incl. the mutation check demonstrated by REMOVING the fence, files
   touched, reviewer-visible defaults). Never committed into cr1 — filled records stay out of
   the repo (cr1 G12).
2. **One scrubbed `READY` row on `<cr1_clone>/BACKLOG.md`** (repo root, contributor-visible via
   fork, never fanned out to client repos — promote writes `command-room/` only).

Any "no" on the suitability test → normal maintainer-side spec, no packet, no BACKLOG row. On a
contractor profile the whole section is inert prose behind the `may_ship` gate: delivery stays
PR-attach, `BACKLOG.md` is never touched. INTAKE1 F1 (append offers restricted to `new/`) and F5
(resurrection guard) untouched.

### Added — `scrub_roster` operator key + a FAIL-CLOSED outbound scrub gate

New key in `config/operator.json`, committed default **`null`** (contractor-safe; the real value
lives ONLY in the gitignored overlay, per the CONSOL1 D3 pattern). Before either outbound write,
the full outbound text is grepped against every client/org/person name in the roster.

- `scrub_roster` null / missing / unreadable / **readable but yielding zero names** → **both
  writes refused** with the explicit line `scrub roster unavailable — BACKLOG/packet emission
  disabled`; the maintainer-side spec is still delivered. Fail-closed by construction: a
  contractor has no roster and never needs the feature. An empty or truncated roster is an
  unavailable roster, never an all-clear (REVIEW_TI2 F-1 — Drive-sync truncation is a live
  failure mode on this substrate). The grep matches individual name tokens as well as full
  names, case-insensitive.
- A roster hit blocks the write and surfaces the offending line for rewrite — **never** an
  automatic name substitution.

This cannot ride cr1's G9 alone: G9's first-name dictionary plus placeholder allowlist cannot
know real ORG names, which is precisely how an org name has slipped past a name guard before.
The mechanized backstop is CI-side in cr1 (`BACKLOG.md` joins G9's staging scan).

### Changed — writer contract (explicit amendment, not a silent widening)

`triage-intake` may now write exactly **two** outbound surfaces, both post-scrub:
`<specs_dir>/packets/PACKET_*.md` and `<cr1_clone>/BACKLOG.md` — the latter **staged via
`git add`, never committed, never pushed**. No other file in any repo is ever written by triage.
A triage session still ends with **zero new commits** in the cr1 clone; the maintainer commits
and pushes in his own ship window. Everything else (no substrate events, no version/CHANGELOG,
ship/promote stays with `may_ship`) is unchanged, as are the single-writer folder rules.

### Changed — closing decision table gains an `Eric?` column

Records the suitability verdict per `SPEC` item (`n/a` for non-SPEC verdicts, `—` on a
contractor profile). When a packet is emitted, the staged `BACKLOG.md` diff is shown under the
table — that staged diff IS the "this is pending" marker.

### Companion change in cr1 (separate repo, separate branch)

Repo-root `BACKLOG.md` seeded with its covenant header, `BACKLOG.md` added to G9's staging scan
(`SCAN_STAGING_FILES`), G2's `BACKLOG\.md` token relabelled (the ban still holds over the plugin
payload — the repo-root dev backlog is the only legitimate home), one `CONTRIBUTING.md` pointer,
and regression pins for both guards. No cr1 version movement.

## v0.3.1 (2026-07-24) — MAINT2: Git-Bash fence fix + two skill retirements

Maintenance batch. Skill count **18 → 16**.

### FIX (priority) — the operator-profile pattern silently no-opped under Git Bash on Windows

`SHIP_RECORD_CONSOL2` finding 3. **Pattern-wide across all 11 reading skills, pre-existing**
(it predates CONSOL1; the F-1 fix in `901898f` correctly matched the established pattern and
did not introduce it).

Two compounding traps, both silent:

1. `${BASH_SOURCE[0]}` is **empty** when an agent runs a SKILL.md block through a Bash tool —
   it is not a sourced script. `dirname ""` is `.`, so the plugin root resolved against
   whatever the cwd happened to be.
2. `pwd` under Git Bash yields an MSYS path (`/c/Users/…`). Native `python.exe` resolves a
   leading `/c/…` against the current drive → `C:\c\Users\…`, so `os.path.exists()` returned
   **False for both config files**. MSYS rewrites path-like ARGV for a native `.exe` but never
   text inside a `python -c` script string — and that interpolation is exactly how the skills
   pass the paths. The merged profile came back **empty**, resolution fell through to the
   synthetic default, and **nothing raised**: an operator granted `allowed_targets: ["real"]`
   silently ran synthetic.

The canonical bash preamble now **searches** for `config/operator.json` (candidates: the
`$CHALETTE_DEV_ROOT` escape hatch, `$PWD`, `$PWD/chalette-dev`, the parent, `~/repos/chalette-dev/…`,
`~/.claude/plugins/marketplaces/*/chalette-dev` — never a hardcoded machine path), converts
the hit with `cygpath -m` (`C:/Users/…`, readable by both MSYS bash and Windows python), and
**fails loud** when the root or the profile is unreadable. It is delimited by
`# --- operator-profile resolution` / `# --- end operator-profile resolution ---`, and the code
inside is byte-synced across the four bash-form skills (comments are per-skill; code is not).

- **Bash form (4):** bug-regression-suite, ship-readiness-gate, synthetic-workspace-runtime-test,
  verify-cr-release. Also `DEV_PLUGIN_ROOT` replaces the ambiguous `PLUGIN_ROOT`/`SELF` naming —
  in synthetic-workspace-runtime-test `PLUGIN_ROOT` means the *Command Room* plugin under test.
- **Python form (7):** capture-for-code, cr-skill-builder, cr-test, cross-skill-interaction-test,
  scale-stress-test, smoke-watch, triage-intake — each gains the same loud fence and states the
  native-path contract for `SKILL_PLUGIN_ROOT`. `cr-skill-builder/references/cr-contract-checklist.md`
  also moves off its `operator.json`-only read onto the merged-overlay form. `CLAUDE.md` documents
  the trap so it is not reintroduced.

**Guard 2 gains Fence 4 — +29 tests, 24 → 53** (51 once the two retirements below drop their
two `quick_validate` cases). Static analysis was structurally blind to this bug, so
the fence **executes** the shipped preamble out of each SKILL.md and asserts the merged profile
reads at least one file: once with cwd = repo root (no env hints), once from an unrelated cwd via
the escape hatch. Plus: an unfindable root must exit non-zero with `FATAL`; resolution code must
stay byte-synced; `BASH_SOURCE` is banned outside comments; every operator-reading skill must
carry the loud-failure line; and one test documents the MSYS-resolution mechanism itself.
Parametrization is keyed on the **consumer** (`'$OPERATOR_CFG'`), not the sentinel, so a skill
that drops the preamble fails instead of vanishing from the test run.
Mutation-verified: reverting the preamble to the pre-MAINT2 form fails 5 tests (all 4 executable
ones); removing only the `cygpath -m` conversion fails the repo-root resolution test.

### RETIRED — compare-canonical-vs-freelance (deleted)

Its validation niche is complete. It existed to validate the **v3.13.8 §3.6 widget degradation
ladder** per skill by firing each widget skill twice — once canonical, once through a mocked
freelance fallback — and diffing. Command Room is at v5.2.0; the freelance fallback it diffed
against no longer exists, widget output goes through `widget_transport.render_and_persist` and its
validators, and the property the ladder diff was inferring is asserted directly by synthetic
invariant **I2 `no_freelance_render`** (plus I1 `canonical_render_invoked` and I16
`file_uri_transport`). The `ship-readiness-gate` step built on it (old Step 2) is gone and its
steps renumbered 3–6 → 2–5. Its coverage claims were **corrected, not silently inherited**:
Bug #46 now cites I1/I2/I16, and Bug #48 (action-label drift) is stated honestly as **not**
covered here at all — it is cr1's `CanonicalActionError` renderer validator running in the unit
tier (`cr test --quick`); I15 covers dispatch shape, not labels.

### FOLDED — run-command-room-tests → cr-test (deleted)

Step-0-verified: `cr-test` **never delegated to it** — it always called `tests/run_all.py`
directly, which discovers every suite at call time, while the retired skill ran a hardcoded five
of 40+. Its trigger phrases now live in **cr-test's frontmatter description** (description-only
routing — the phrase has to be in the description to route) as aliases for `cr test --quick`:
`internal: run plugin tests`, `run command room tests`, `command room health check`,
`verify plugin code`. cr-test's description: 607 → 905 chars, inside the ≤980 doctrine.

### Sweep

Every live companion reference to both retired skills removed: `ship-readiness-gate` (description
companion list, target-mode bullet, Step 2, coverage claim, failure mode, implementation
references), `verify-cr-release` (description companions, DOES-NOT-FIRE fence, companion-skills
list, plugin-family list), `bug-regression-suite` (SKILL.md ladder list + `bug-catalog.md` trigger
line), `synthetic-workspace-runtime-test` fence, `preview-command-room-widget` see-also, `cr-test`
(3 places), `README.md` table (+ a retirement note), `CLAUDE.md` skill count, `plugin.json`
description head. Earlier CHANGELOG entries and the `PRIOR HISTORY` half of the plugin.json
description are **append-only history** and keep their original wording — this entry is what tells
a reader the skills are gone.

## v0.3.0 (2026-07-24) — CONSOL1: single canonical home for the shared QA/dev toolkit

chalette-dev is now the **one and only home** of the shared testing / verification /
skill-building toolkit. The same 18 skills were duplicated in the private `chalette` plugin
(chalette030) and the two copies had silently drifted; CONSOL1 removes the `chalette` copies
(there, `chalette` v0.10.0) and reconciles the survivors here to their canonical, operator-fenced
form. Skill count unchanged (18). Second-eyes review (REVIEW_CONSOL1) is pending before either
repo publishes.

### Per-skill reconciliation (newest-wins WITH fence preservation)
- **bug-regression-suite** — kept dev base (operator-fenced target resolution + overlay);
  ported `ChaletteHQ/cr1` repo naming; noted the dual-copy byte-identical catalog invariant
  RETIRED (single copy now); L1 real-name audit-residue docs confirmed removed (deletion-forward).
- **capture-for-code** — kept dev base; scoped the placeholder-names rule to non-`real` operators
  (INTAKE1 F7); added the operator.local.json overlay.
- **cr-test** — added rule 0 (`cr1_clone` from the operator profile wins if set); "M's call"
  delegate → "the ship operator's call (`may_ship`)".
- **cross-skill-interaction-test** — operator-fenced (requires `real`; no synthetic paste-back mode);
  neutralized M-identity prose.
- **ship-readiness-gate** — A (chalette030) won content (ChaletteHQ/cr1 + promote fan-out wording);
  **rebuilt on the operator pattern** — default synthetic, m-workspace only when `allowed_targets`
  grants `real`; dropped the false "fixtures unpopulated" claim; verdict/findings paths resolve
  from the profile; Step-0 clone detection resolves `cr1_clone`.
- **synthetic-workspace-runtime-test** — kept dev base (populated fixtures); **re-added Invariant 7
  `event_gate_routed`** (D6); `cr1_clone`-resolved fallback replaces the stale `commandroom1`
  marketplace path; shape-prose neutralized.
- **triage-intake** — kept dev base; **ported INTAKE1 F5 (resurrection guard)** — which had landed
  only in chalette030 and would otherwise have been lost; F4 `chalette_clone` operator-aware;
  `specs_dir` + `parking_doc` keys; `may_ship`-gated spec delivery; F1 single-writer verified present.
- **verify-cr-release** — kept dev SKILL.md + VERIFICATION_PLAN.md; ported A's findings-log-format
  production-HEAD wording (ChaletteHQ + `promote_core_to_clients`); `Tester: the operator`; output
  paths resolve from the profile (attended M's-Cowork prose kept — authority-accurate).
- **cr-skill-builder** (L4) — output dir resolves from the profile (workspace_root or a
  cr1_clone-adjacent scratch); the leak-token negative example's real Windows username swapped for a
  placeholder; overlay added to the clone read; companion refs re-pointed `chalette:`→`chalette-dev:`.
- **skill-creator** — stale `plugin-source-v2/skills/` path rule replaced with the cr1-clone
  canonical surface + cr-skill-builder contract pointer.
- **smoke-watch / scale-stress-test** (L2 / L3) — operator-fenced: smoke-watch requires `real`
  (no synthetic mode — honest); scale-stress-test defaults to the populated `mature_workspace`
  fixture, real only when granted. Paths resolve from the profile.
- Byte-identical clean skills (compare-canonical-vs-freelance, preview-command-room-widget,
  run-command-room-tests) — no change beyond deletion of the chalette030 duplicate.

### Operator profile + overlay
- `config/operator.json` gains `chalette_clone`, `specs_dir`, `parking_doc` (all null / contractor-safe).
- New gitignored `config/operator.local.json` overlay: every reading skill loads `operator.json`
  then overlays `operator.local.json` per-key. Committed default stays contractor-safe; M's real
  profile lives only in the overlay. `.gitignore` added.
- `CLAUDE.md` + `README.md` document the overlay, the single-canonical-home rule, and the guards.

### Structural guards (permanent)
- **Guard 1** `scripts/check_toolkit_overlap.py` — fails if any shared-toolkit skill name exists in
  both plugins. Mutation-fence verified (planted duplicate → exit 1 naming it; intersection logic
  disabled → passes silently).
- **Guard 2** `tests/test_operator_fences.py` — asserts the committed operator.json stays
  contractor-safe (allowed_targets==["synthetic"], may_ship/may_promote false, workspace_root null,
  operator!="m"), operator.local.json untracked, and quick_validate passes for all 18 skills.
  Mutation-fence verified (may_ship→true → test fails; assertion removed → passes).
- `.github/workflows/toolkit-guard.yml` runs Guard 2 + quick_validate unconditionally, Guard 1 only
  when `CHALETTE030_READ_TOKEN` is present (absent → SKIPPED/green, so forks never fail).

### quick_validate hygiene
- Removed stray top-level `template_version` frontmatter key from regenerate-skill, skill-generator,
  voice-test.
- Shrank regenerate-skill (1082→906) and skill-generator (1113→927) descriptions to the ≤980
  doctrine, preserving every trigger phrase + DOES-NOT-FIRE fence verbatim.
- 18/18 skills pass quick_validate.
