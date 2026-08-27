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
  `review_exact`, `observed_exact`, `observed_as_open` (an observed item
  wrongly opened as an owner commitment). The observed tier is a distinct
  outcome: correctly-observed is neither a capture nor a miss. Arm B has no
  observed tier; its observed-row cells read N/A, never zero.
- **False captures** = reject items assigned any capture form.
- **Unplanted captures** = capture rows (events channel) matching no planted
  keyphrase. Reported as a count with the row text; these overlap with the
  hallucination metric but are counted separately.

**Receipt cross-check (Arm A):** the scorer compares its book+review count
against CR's own `capture_counts` receipts on `meeting_processed` events.
Disagreement does not change the score — it flags the run for investigation
in the scorecard (`receipt_cross_check.agree: false`).

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
