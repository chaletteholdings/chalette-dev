# BENCH1 scoring rubric — countable metrics only

The scorer (`scripts/bench_scorer.py`) is deterministic code. The same logic
scores both arms; only the CHANNELS differ (Arm A has an event stream; Arm B
has chat/files only). Every per-item judgment records its evidence line so a
reviewer can audit any count without re-running.

## 1. Commitment extraction (task t1 only)

Ground truth: the frozen labels beside each transcript. Every planted item
has a unique `keyphrase` that appears in exactly one transcript (enforced by
the generator's validator); the scorer matches output rows to labels by that
keyphrase, case-insensitively. No semantic matching, no model judgment.

**Route assignment per planted item:**

| Channel | Rule |
|---|---|
| events (Arm A) | `commitment` → book; `commitment` with `pending_review` (or `commitment_review_proposed`) → review; `commitment_observed` (or `tier: "observed"`) → observed |
| chat/files (both arms) | keyphrase inside a commitment-shaped line, where "commitment-shaped" is one of three fixed shapes: (1) the `COMMITMENT_LINE` regex (will/owes/to-verb/by-date/action-item/task/due, plus hedge markers might/could/tentative/pending/no-promises for review-lane items; "aspirational"/"hedged"/"someday" are deliberately excluded — they mark dismissal roundups, and counting them scored correct rejections as false captures in the pilot); (2) a row of a commitment-shaped markdown table (header matches commitment/owed/owner/due/action/task); (3) an arrow-bullet row (`- **Owner** → deliverable`). Shapes 2–3 and the hedge markers were added at pilot calibration after real output used them; all three are arm-symmetric and frozen for the battery → `chat_capture` |

Labels may carry `alts`: paraphrase aliases for output matching only ("COO"
for "chief operating officer", hyphenation, dropped articles). The primary
keyphrase remains the transcript anchor and the uniqueness-validated key.
Alts were added at pilot calibration (both arms re-scored identically) and
are frozen for the battery.
| neither | `mentioned_only` (keyphrase present, not as a capture) or `absent` |

The events channel wins when both fire. `mentioned_only` is NOT a capture —
a distractor discussed and dismissed in prose counts as correctly rejected.

**Outcomes:**

- **Owner-lane recall** = (book+review planted items assigned book, review,
  or chat_capture) / (book+review planted). The bare arm has no routes, so
  `chat_capture` is its only capture form — this is the arm-fair recall.
- **Owner-lane precision (vs planted)** = owner-lane captures /
  (owner-lane captures + reject items captured in any form).
- **Route exactness (Arm A capability metrics)**: `book_exact`,
  `review_exact`, plus the observed split below. The observed tier is a
  distinct outcome: correctly-observed is neither a capture nor a miss. Arm B
  has no observed tier; its observed-row cells read N/A, never zero.
- **Observed split (label set v1.1, after the 2026-08-27 investigation)**:
  shipped precedence is caution rail > party test
  (`capture_gate.classify_capture:870`, pinned by
  `run_w4c_capture_gate_test`'s `test_caution_rail_beats_every_mode`) — a
  dated or money-bearing third-party item opens BEFORE party-ness is
  consulted, so it cannot reach the observed tier by construction. Labels
  mark those `rail_shadowed`; for them the shipped-correct outcome is the
  open lane (`observed_shadowed_open_ok`), and `observed_shadowed_as_observed`
  firing would mean the rail did NOT engage. Only un-dated third-party items
  (`observed_undated_*`) test the observed tier itself. The pilot's 0/11
  "observed misses" were all rail-shadowed items routing exactly as shipped —
  a scoring-design artifact, not a product defect; the W4c-doctrine-vs-rail
  tension is a product design question tracked outside this rig.
- **False captures** = reject items assigned any capture form.
- **Unplanted captures** = capture rows (events channel) matching no planted
  keyphrase. Reported as a count with the row text; these overlap with the
  hallucination metric but are counted separately.

**Receipt cross-check (Arm A):** the scorer compares its book+review count
against CR's own `capture_counts` receipts on `meeting_processed` events.
Disagreement does not change the score — it flags the run for investigation
in the scorecard (`receipt_cross_check.agree: false`).

## 1c. Counterparty-resolved rate (task t1; ATTRIB1 D10, 2026-09-04)

Per planted **book/review** item carrying a `counterparty_name` label, and
only when the item was CAPTURED (assigned book / review / chat_capture): does
the capture name that counterparty? The verdict is read from the SAME row
or line the recall credit came from.

| verdict | events channel | chat channel |
|---|---|---|
| `correct` | `data.counterparty_id` resolves (fixture roster) to the labeled name; or a string `counterparty` field names them | the counterparty's first or full name is in the capture line; when the counterparty is the user, second person ("you"/"me") counts |
| `wrong` | the id / string names a DIFFERENT roster person and not the labeled one | a roster first name that is neither owner nor counterparty is in the line, and the counterparty is not |
| `unresolved` | no id and no roster name (null, "counsel", "the Acme Co team") | no roster name in the line |
| `unknown_id` | a `counterparty_id` the pre-run fixture roster does not hold (an entity the run minted); reported as its own count, never folded into unresolved | — |

Naming the right person beside another is `correct`. A non-roster string is
`unresolved`, never `wrong`. Items not captured sit outside the denominator
(`not_captured`), so the rate measures attribution, not recall.

Reported per party bucket — `2p` (two attendees on the label) and `3p+` —
as `correct/captured (wrong N, of expected)`, plus `rate_correct_of_captured`,
`rate_wrong_of_captured`, `rate_correct_of_expected`. Arm A rows also tally
`attribution.counterparty_basis` values (informational). Same rule on every
arm and every speaker variant; the named → me_them delta is the D10 number.
Reading guide: `references/speaker-variants.md`.

## 2. Entity resolution (tasks t1, t5)

Per labeled mention:

- **right** — the expected canonical name (or org name) appears in output or
  events. Rendering the canonical form is the contract under test.
- **partial_surface_only** — the raw surface appears but the canonical name
  never does (the resolver was skipped or failed silently).
- **missed** — neither appears.
- For the UNKNOWN_PERSON label (a roster-legal name absent from
  entities.json): **right** = the name is surfaced as new/unknown; **wrong** =
  output binds it to an existing person (e.g. asserts the Sample surname for
  a Stone unknown); **missed** = never mentioned. The wrong-bind rule applies
  ONLY on t1 (where the arm processed the transcript that introduced the
  unknown). On t5, answering a first-name question from the roster is
  correct, not a wrong bind — calibrated after the pilot penalized both arms
  for the right answer.

## 3. Hallucinated rows (all tasks)

Count of invented person names: name-shaped bigrams in output whose first
name exists in the roster but whose full name exists nowhere in roster,
known-unknowns, or org list (e.g. "Quinn Stone" when only Quinn Sample
exists). Common-word bigrams are filtered by a fixed stoplist. Conservative
by design: it undercounts rather than overcounts.

## 4. Leak survivals (all tasks)

Forbidden-token catalog over chat + created files (substrate files excluded —
they are not user-facing). Source of truth: cr1's
`docx_leak_scanner._FORBIDDEN_PATTERNS`, imported live when `--cr1` is
passed; the embedded mirror is the fallback. Same catalog, both arms. Note
the asymmetry is real and intended: Arm B has no internal vocabulary to leak,
so its baseline is ~0; the metric exists to prove Arm A's scaffolding does
not leak engineering vocabulary into user-facing output.

## 4b. Event schema validity (all tasks, battery onward)

Every event a run appends to `events.jsonl` is validated against cr1's
canonical `events.schema.json`; the scorecard carries
`event_validity: {events, invalid, errors[]}`. Arm-symmetric by code — added
at battery start when the confirm turn revealed the bare arm hand-writing
its own rows into the substrate: an appended row is only durable capture if
the product's own readers can consume it. Skip-not-fail: without a cr1
clone or jsonschema the metric is absent, never zero.

## 4c. Speaker variant (all tasks, 2026-09-04)

Every scorecard carries `speakers` (`named` / `me_them` / `unlabelled`, from
`run_meta.json`; legacy runs read as `named`). Runs on different speaker
variants are never aggregated with each other — they are compared, side by
side, in the scoreboard's *Speaker variants* table.

## 5. Cost (all tasks)

Wall-clock ms and token counts copied verbatim from the headless run's usage
block, per (arm x task). Runs on different reported model ids are never
aggregated. Timeouts and CLI errors are reported as their own rows, never
silently dropped.

## Fairness notes (on the record)

- The `COMMITMENT_LINE` regex is the one judgment-shaped rule in the scorer.
  It is fixed, arm-symmetric, published here, and every application of it
  records the matched line in the scorecard for audit.
- Chat-channel scoring gives the bare arm full credit for a correct capture
  reported only in prose. Arm A gets the same chat-channel credit when its
  events channel is silent.
- No metric rewards verbosity: recall counts distinct planted items, not
  mentions, and cost is reported beside quality in every table.
