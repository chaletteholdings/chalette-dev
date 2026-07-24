# chalette-dev — Changelog

(Release history before v0.3.0 lives in `.claude-plugin/plugin.json`'s `description` field.
This file starts at the CONSOL1 release.)

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
