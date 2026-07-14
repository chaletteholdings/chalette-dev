# Why the Command Room Suite Runs GREEN While ~300 Real Issues Escaped — Root-Cause Map + New Guard-Test Spec

**Scope:** read-only analysis of `tests/run_event_contract_test.py`, `tests/run_no_real_customer_names_test.py`, `tests/run_all.py`, `shared/data-schemas/events.schema.json`, `shared/data-schemas/entities.schema.json`. All line citations are to those files unless noted. The hypothesis (tests are code-shaped, skills act via prose) was tested directly against the code and is **confirmed**, with one refinement (see §2.1).

---

## 1. What each test actually checks

### 1.1 `run_event_contract_test.py` — producer/consumer structural guard

**Surface scanned.** Production dirs only: `SCAN_DIRS = ["skills", "shared", "references"]` (line 64), extensions `{.md, .py}` (line 65). `tests/` is deliberately excluded (lines 30-32, 63). Exemptions: the test file, `events.schema.json`, `CHANGELOG.md` (lines 69-73), `shared/releases/**` (line 75).

**Canonical set.** `load_canonical_types()` reads `properties.type.enum` from `events.schema.json` (lines 172-175). This is the ONLY schema it loads — it never opens `entities.schema.json`, so project-status / org-scope / relationship-type enums are entirely out of its universe.

**What it treats as a WRITE** (lines 221-230): `WRITE_LITERAL_RE` (`"type": "x"` literals, incl. fenced code in .md, line 83); `TYPE_ASSIGN_RE` (`event_type = "x"`, line 88); prose emit = an emit verb (emit/writ/append/record/stamp/log, lines 90-92) AND a backticked token immediately followed by the literal word "event" (line 93).

**What it treats as a READ** (lines 232-244): a `*_TYPES`/`*_EVENTS` constant block (line 107); or a line carrying a `TYPE_SIGNAL_RE` token (`.get("type")`, `["type"]`, `ev_type`, `et ==|in|!=`, lines 99-105) — only then are quoted tokens on that line harvested as reads. `NOT_EVENT_TOKENS` (113-117) suppresses field-name noise.

**The two hard failures** (lines 248-330): (1) DANGLING READS — a token that is canonical AND read-by-prod AND written-by-no-prod (255-258); (2) NEAR-MISS — a non-canonical written/read token within Levenshtein 1..2 of a canonical type (`NEAR_MISS_MAX_DISTANCE = 2`, line 153). ORPHAN WRITES are soft and `--orphans`-gated (307-316).

**Decisive structural fact:** the only hard failures are "canonical-but-unwritten read" and "near-miss typo." A *written* token is **never** hard-failed for being non-canonical. The docstring concedes the read side is prose-blind (line 312: "most CR consumers read events via PROSE in SKILL.md … which the code-shaped read detector cannot see") — but the authors did not extend that awareness to "writes of types that aren't in the enum at all."

### 1.2 `run_no_real_customer_names_test.py` — name/email leak guard

**Surface.** `SCAN_DIRS = ["skills", "shared", "references", "tests"]` (311) + CHANGELOG.md (314); only the test file + PRIVACY_POLICY.md are exempt (301-307).

**Three layers** (scan, 350-373): Layer 1 named denylist (`FORBIDDEN_NAME_PATTERNS`, ~16 hardcoded historical leaks, 61-78); Layer 2 email-domain allowlist (fails closed for `local@domain.tld`, 89-104, 357-368) — genuinely durable; Layer 3 "structural" allowlist (155-296): three regexes (Firstname-Lastname pair, person-context `with|for|to|from|by|about|via [Name]`, possessive `[Name]'s`) that flag a hit **only if** the captured first token is in `COMMON_FIRST_NAMES` (325 names) AND not in `APPROVED_FIRST_NAMES` (11 placeholders).

**Decisive fact:** Layer 3 detection is gated on a 325-name dictionary — a denylist wearing an allowlist's clothes. Any first name not in the 325-list is structurally invisible.

### 1.3 `run_all.py` — the battery

Auto-discovers every `run_*.py`/`test_*.py` (82-92), classifies into tiers, runs each as a subprocess (non-zero = fail), fail-fast at the guard tier (165-167). GREEN = every discovered suite exited 0. It adds **no** independent checks. There is no suite whose job is "validate that the model-executed instructions in SKILL.md obey the data contracts." That category does not exist in `tests/`.

---

## 2. Why each root pattern escaped — the precise mechanism

Unifying cause: **the substrate contract is enforced against code, but skills perform their reads/writes/field-sets/naming as model-executed prose in SKILL.md and orchestrator-*.md.**

### 2.1 ~50 phantom event-type writes/reads (cleanup_run, schedule_config_changed, project_loaded_deep, bug_self_fixed, decision_logged)

**(a) Phantom WRITES are detected but never failed.** `cleanup/SKILL.md:109` ("Append ONE `cleanup_run` event"), `workspace-manager/SKILL.md:413` ("write a `project_loaded_deep` event"), `change-schedule/SKILL.md:184` (`'type': 'schedule_config_changed'`) all register as writes — but a non-canonical write can only surface as near-miss or orphan. Edit distances to the nearest canonical type: cleanup_run→pack_run = 6; schedule_config_changed→schedule_created = 10; project_loaded_deep→project_proposed = 10; bug_self_fixed→bug_received = 6; decision_logged→decision_resolved = 5. All are 5-10 edits away, far outside the 1..2 near-miss window. So each lands at worst in the suppressed orphan bucket. GREEN.

**(b) Phantom READS are invisible.** `call-prep/SKILL.md:148` ("Pull from events.jsonl `decision_logged` events") carries no `TYPE_SIGNAL_RE` token, so the read detector harvests nothing; and dangling-read detection only fires on canonical tokens, which these are not. The prose read is doubly invisible.

**(c) Nothing checks writes against the schema floor.** There is no branch that says "a token written by prod must be in canonical." A skill can invent `bug_self_fixed` and the only possible reaction is a suppressed orphan line.

### 2.2 ~25 deprecated-field uses (primary_project_id / project_id vs primary_thread_id)
The contract test does not check field names at all — it is an event-type guard. No test loads the schema's property names and diffs prose field usage against them. **No test owns this class.** GREEN by absence.

### 2.3 ~12 non-canonical project-status values (at-risk, completed)
Status enum is `active|dormant|paused|blocked|archived` (entities.schema.json:176). The contract test never opens entities.schema.json; the name test doesn't model enums; no suite validates prose status strings. GREEN by absence.

### 2.4 ~60 real names/orgs in prose (Drew, Colton, Marcus, Wetsel Brothers)
Layer 3 is gated on the 325-name dictionary + three grammatical positions. `Drew`/`Marcus` are not in the dictionary → invisible in any position. `Colton` is in the dictionary but only flagged in person-context/possessive/pair slots → a bare mention escapes. `Wetsel Brothers` has no known first name to anchor on → dropped at line 268. Surnames and orgs are the biggest blind spot. GREEN.

### 2.5 The asymmetry

| root pattern | carrier surface | test that should own it | why GREEN |
|---|---|---|---|
| phantom event writes | SKILL.md prose / fenced code | contract test | non-canonical writes only near-miss/orphan; all dist ≥5 → orphan (suppressed) |
| phantom event reads | SKILL.md prose | contract test | prose reads carry no TYPE_SIGNAL → invisible; dangling check is canonical-only |
| deprecated field names | SKILL.md prose | (none) | type-only test; no field checker exists |
| non-canonical status | SKILL.md prose | (none) | entities.schema.json never loaded by any guard |
| real names / orgs | SKILL.md/orchestrator prose | name test | detection gated on 325-name dict + 3 positions; surnames/orgs/unknown-firsts uncovered |

---

## 3. Specification — new `run_prose_contract_scanner_test.py`

A single guard-tier suite that treats model-executed prose as a first-class contract surface and validates every claimed event-type, field name, status value, and person/org reference against the canonical enums and the approved-name allowlist.

### 3.0 Placement & wiring
- File: `tests/run_prose_contract_scanner_test.py`. Add `run_prose_contract` to `GUARD_MARKERS` in run_all.py (58-67) → guard tier + fail-fast. Non-zero exit on any violation. stdlib only. Report style mirrors the contract test (287-316).

### 3.1 Surface to scan
- Dirs: `["skills", "shared", "references"]` (production prose only). Do NOT scan `tests/` (fixtures legitimately contain phantom types).
- Files: `SKILL.md` + every `references/**/orchestrator-*.md` and `references/**/*.md`. `.md`-only (python is already covered by the existing code-shaped test).
- Exempt: schema files, CHANGELOG.md, shared/releases/**, PRIVACY_POLICY.md, DATA_CONTRACT.md, shared/CONTRACT.md (these *document* the contract and contain didactic examples), and the test file itself.

### 3.2 Canonical sources of truth (load once)
- Event types: events.schema.json `properties.type.enum` (reuse loader at 172-175).
- Field names: union of property keys across events.schema.json + entities.schema.json `$defs`. Build `CANONICAL_FIELDS` and a `DEPRECATED_FIELDS` map by detecting "DEPRECATED" in each property's description (e.g. events.schema.json:166 project_id; entities.schema.json org_id/email/project_class/type/domain). Parse the canonical replacement from the description ("Use `primary_thread_id`").
- Enums: from entities.schema.json — project `status` (176), org `scope` (281), `relationship_type` (294), `tier` (303), person/org `status`, project `kind` (215), engagement `kind` (379). Key each enum by its owning field.
- Approved names: **parse** PRIVACY_POLICY.md at runtime (do not re-hardcode) so the allowlist can't drift from policy.

### 3.3 Extraction patterns
- **Class A — event-type writes:** broaden the contract test's prose-write detection (90-93) + fenced `"type": "x"` (83). Violation = captured token ∉ event enum. **Do NOT require near-miss** — any non-canonical written type fails. (This alone catches cleanup_run, schedule_config_changed, project_loaded_deep, bug_self_fixed.)
- **Class B — event-type reads:** read verb (`scan|pull|read|filter|aggregat|count|load|fetch|tied to|filtered for/to|of type`) + backticked token + "event(s)"; or token co-occurring with `events.jsonl`. Violation = token ∉ enum (non-canonical read) OR token read but never written anywhere (dangling prose read). Cross-check against the existing code-side `scan()` so the check spans both surfaces.
- **Class C — field names:** harvest backtick snake_case tokens on data-contract lines (mention `events.jsonl`/`entities.json`/`data:`/`field`/`tied to`/`set … to`, or in a fenced block). Violation = a known deprecated or unknown field. Suggest the canonical replacement. (Catches the ~25 deprecated-field uses; `primary_project_id` is not even a real field.)
- **Class D — status/enum values:** when a line sets status/scope/kind, validate the value against the owning entities enum. `at-risk`/`completed` ∉ status enum → fail.
- **Class E — person/org names:** see §3.4/§3.5.

### 3.4 Name strategy that does not regress to a denylist
In a synthetic/placeholder codebase the only names that should appear are approved placeholders. So: extract every candidate human/org reference (positional regexes + standalone PascalCase + PascalCase pairs), strip code/URLs/backticks, then **flag any candidate whose token(s) are not in the approved placeholder set** parsed from PRIVACY_POLICY.md. No 325-name dictionary, no positional gating, no surname blind spot. Keep Layer 1 (denylist) and Layer 2 (email allowlist) as-is; Class E replaces the broken Layer 3.

### 3.5 False-positive controls
1. Skip fenced/indented code for prose classes (A1, B, E); Class A2/C still scan fenced blocks for `"type":`/field literals.
2. Quoted-example/changelog exemption: lines inside an `Example:`/`e.g.`/`❌`/`✅`/`Don't:`/`Format:`/blockquote span are exempt for the name class (a SKILL.md may show "❌ never write 'with Drew'").
3. PascalCase stop-list (structural, not a name denylist): exempt markdown headings, known product/system nouns parsed from a real `references/APPROVED_TECHNICAL_PHRASES` list (Live State, Master Tracker, Command Room, connector names…), and sentence-initial single caps.
4. Deprecated-field back-compat exemption (Class C): a deprecated field on a line containing `back-compat`/`fall back`/`legacy`/`reader(s) use` is describing the read-fallback contract → INFO, not fail. Only new WRITES to deprecated fields fail.
5. Every allowlist is parsed from a markdown doc under `references/`, never hardcoded — a new placeholder requires a PRIVACY_POLICY.md edit in the same change (the fails-closed property the original test claimed but undercut by hardcoding).

### 3.6 Violation table
| class | condition |
|---|---|
| A event write | prose/code claims a write of `tok` and `tok` ∉ events enum |
| B event read | prose claims a read of `tok` and (`tok` ∉ enum) OR (`tok` written nowhere) |
| C field | a data/write-context line uses a deprecated or unknown field (excl. back-compat prose) |
| D status/enum | a set-status/scope/kind line uses a value outside the owning enum |
| E name/org | a person/org candidate is not an approved placeholder (excl. example spans + technical-phrase allowlist) |

### 3.7 Wiring into run_all.py
Add `"run_prose_contract"` to `GUARD_MARKERS` (58-67) → guard tier, fail-fast. Discovery + run_suite handle the rest; non-zero exit flips the battery RED.

### 3.8 Self-test fixtures
Ship `tests/fixtures/prose_contract/` with a SKILL.md that must fail each of A–E, plus a clean control file (canonical types, primary_thread_id, status active, Sam Sample/Acme Co) that must pass. A `--selftest` mode regression-guards the scanner itself — the same "no test of the tester" gap that let these escape must not recur.

---

## 4. Bottom line
The suite is GREEN because **every contract is enforced against code while the violations live in model-executed prose.** The one place that peeks at prose — the contract test's write detector — has no schema-conformance branch, only a near-miss branch tuned to distance ≤2 that wholly-invented types (distance 5-10) sail past. The name test's "structural" layer is a 325-name dictionary gated to three positions, i.e. a denylist that misses any name it doesn't already know and every org/surname. Status and field-name drift have no owner at all because no guard loads entities.schema.json or models field names. The fix is one new guard-tier suite that scans prose, validates against the canonical enums + a PRIVACY_POLICY-parsed allowlist, and fails closed.
