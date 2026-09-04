# Speaker variants — how to read the named / me_them numbers (ATTRIB1 D10)

The benchmark transcript set is rendered three ways from ONE data structure
and ONE frozen label set. Nothing else changes between the renderings — same
turns, same planted items, same keyphrases, same attendee list on the
connector doc, same prompts, same arms, same model pin.

| variant | what the model sees | why it exists |
|---|---|---|
| `named` | `Sam Sample: …` / `Bo Sample: …`, one turn per line | the original set (BENCH1). Every line names its speaker — the world about 13% of the operator's real transcripts live in |
| `me_them` | `Me: … Them: … Me: …` — the user is `Me:`, **every** other voice is `Them:`, consecutive same-voice turns merge, markers inline on ONE line | the real Granola shape: 76% of the operator's transcripts (the ATTRIB1-A class census on 71 live transcripts: named 9 · me_them 54 · dictation 8). The number M sees in the benchmark should be the number M gets |
| `unlabelled` | turn text only, no markers | optional third arm — what a pasted or diarizer-less transcript gives the product |

Files: `fixtures/bench_transcripts/` is the named set and holds `labels/`;
`fixtures/bench_transcripts/me_them/` and `…/unlabelled/` hold only the
rendered `.txt` files plus a manifest that points back at the shared labels.
`_generate_bench_transcripts.py --check` validates all three (keyphrase
uniqueness per rendering, Me/Them-only markers on one line, no marker at all
for unlabelled, roster-only names).

## The two numbers

Run the same task on the same arm with `--speakers named` and
`--speakers me_them`; the scoreboard's **Speaker variants (t1)** table puts
them side by side. Read them in this order:

1. **Recall / precision (owner-lane).** Did the arm still find the
   commitments when the transcript stopped naming who spoke? Under `me_them`
   the planted items are word-for-word identical, so a recall drop is purely
   the cost of the missing speaker names. Precision guards against the arm
   compensating by capturing everything.

2. **Counterparty-resolved rate — `correct/captured (wrong N, of expected)`.**
   Of the owner-lane items the arm CAPTURED, how many name the labeled
   counterparty. Three outcomes, one rule, both channels, both arms:
   - `correct` — the labeled counterparty is named (first or full name; when
     the counterparty is the user, "you"/"me" counts, because that is how a
     recap addresses them). Naming the right person beside another still
     counts as correct.
   - `wrong` — a DIFFERENT roster person is named and the right one is not.
     A guess presented as a fact. **This is the number that matters most
     under `me_them`**: the product's ATTRIB1 contract is to ask (leave the
     counterparty unresolved with a question) rather than guess.
   - `unresolved` — nobody from the roster is named ("counsel", "the Acme Co
     team", or nothing). Honest, and never counted as wrong.

   The denominator is captured items, so the rate is about attribution, not
   recall — the two are reported beside each other and never folded.

3. **The 2p / 3p+ split.** On a two-party call the `Me`/`Them` marker plus
   the calendar's attendee list identifies the other party exactly — a
   `Them:` promise is the other attendee's, a `Me:` "I'll send you…" is owed
   to them. The product's calendar-2p rung (ATTRIB1 DD-3) exists for this
   case, so **2p under `me_them` is the cell that measures ATTRIB1 directly**
   (the live-book replay target for the same quantity is ≥95%). On a
   three-or-more-party call the marker cannot separate the other voices;
   `correct` there means the arm read it from content, `wrong` means it
   guessed, and `unresolved` is the contract-correct outcome when content
   does not settle it. Do not compare 3p+ cells against the 95% target.

4. **`cp basis (events)`** — Arm A only, informational: the
   `attribution.counterparty_basis` values on the captured rows
   (`calendar` / `vocative` / `speaker` / `person_ids` / `inferred` /
   `unknown`). A high `correct` rate with `inferred` everywhere is a model
   guessing well; `calendar` on 2p rows is the rung doing its job.

## What a good result looks like

- `named` → `me_them`: recall and precision hold within a couple of items;
  2p counterparty `correct` holds (the calendar rung compensates for the
  missing names); `wrong` stays at 0–1; `unresolved` may rise on 3p+.
- A large recall drop under `me_them` means the extractor leans on speaker
  names to find promises at all — a capture problem, not an attribution one.
- `wrong` rising under `me_them` is the failure ATTRIB1 exists to prevent.

## Fairness notes

- The bare arm has no calendar rung; it sees the same attendee list on the
  connector doc and may reason from it. The metric gives it the same credit
  by the same rule.
- Labels' counterparties are "the person in the room the promise was made
  to" — frozen since BENCH1 v1.1. Items where the real recipient is an
  outside party ("send the wire instructions to counsel") score `unresolved`
  on every arm and every variant; the named → me_them DELTA is unaffected.
- The me_them rendering carries one quirk of the real shape on purpose: a
  turn ending in a capitalised word followed by an inline marker
  (`…by Friday Them: …`) is, to a left-to-right label parser, a label
  "Friday Them". cr1's `meeting_capture.transcript_turns` has that shape
  too. The fixture keeps it because the operator's transcripts have it; it
  is a product observation, not a fixture defect.
