#!/usr/bin/env python3
"""Deterministic generator for the BENCH1 labeled transcript set.

Reads the clean_workspace fixture roster (people / orgs / projects) and emits
12 synthetic Granola-shaped transcripts plus a frozen labels.json per
transcript. The labels are the single source of truth for scoring; transcript
text and labels are emitted from ONE data structure so they cannot drift.

Ground-truth routes follow cr1's COMMITMENT_SCHEMA.md capture floor:
  book     -- forward-looking + specific + owned + consequential, owner-party
  review   -- hedged/ambiguous but consequential; a capture pending confirm
  observed -- third-party <-> third-party item (W4c observed tier)
  reject   -- fails the floor (vague, hypothetical, past-tense, retracted,
              live-action-on-call, unowned group talk)

Roster rules (G9): every full name is drawn from the live approved
Sample/Stone placeholder roster. People in the fixture use the Sample
surname; the Stone combinations are reserved as KNOWN-UNKNOWNS -- names that
are roster-legal but absent from entities.json, used to test
unknown-person handling. No other name bigrams are permitted.

Usage:
    python _generate_bench_transcripts.py [--fixtures-root PATH] [--check]

Deterministic: no wall clock, no randomness. Re-running is a no-op diff.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_ROOT = HERE.parent
DEFAULT_FIXTURES = (SKILL_ROOT.parent / "synthetic-workspace-runtime-test" / "fixtures"
                    / "clean_workspace")
OUT_DIR = SKILL_ROOT / "fixtures" / "bench_transcripts"

SET_VERSION = "1.0"
BASE_DATE = "2026-05-04"  # the Monday after the fixture BASE_DATE 2026-05-01

# Known-unknowns: approved-roster names deliberately absent from entities.json.
KNOWN_UNKNOWNS = ["Skyler Stone", "Rio Stone"]


# --------------------------------------------------------------------------
# The set. Every transcript is (id, title, attendees, turns, planted,
# mentions). Turns are (speaker_first_name, text). Planted items carry a
# keyphrase that must appear in exactly one transcript so the scorer can
# match model output rows to labels without judgment calls.
#
# {P} = primary user first name (Sam). Other first names are bound to the
# fixture roster at generation time; generation fails loudly if a name is
# missing from the roster.
# --------------------------------------------------------------------------

TRANSCRIPTS = [
    {
        "id": "bench_01",
        "title": "Weekly pipeline sync",
        "attendees": ["Sam", "Bo"],
        "turns": [
            ("Sam", "ok let's run the pipeline, top of the list is the Acme Co renewal"),
            ("Bo", "they asked for updated pricing before they'll sign anything"),
            ("Sam", "right, I'll send the revised pricing sheet to you by Tuesday so you can walk them through it"),
            ("Bo", "good, they go quiet fast when we sit on things"),
            ("Sam", "also you mentioned Cedar Works has a new finance lead"),
            ("Bo", "yes, can you introduce me to the Cedar Works finance lead this week? I want them in the loop before the proposal lands"),
            ("Sam", "sure, will do, I'll make the intro over email"),
            ("Bo", "we should probably rethink the whole onboarding flow at some point too"),
            ("Sam", "yeah, someday, let's circle back on that"),
            ("Bo", "and honestly a cleaner dashboard would be nice"),
            ("Bo", "one thing I owe you: I'll send you the Acme usage report by Friday so you have it for the renewal call"),
            ("Sam", "good. and I might be able to get the customer case study drafted before the renewal too, no promises"),
            ("Bo", "even a rough one helps"),
            ("Sam", "noted, ok that's the list"),
        ],
        "planted": [
            {"route": "book", "keyphrase": "revised pricing sheet",
             "gist": "send the revised pricing sheet to Bo by Tuesday",
             "owner": "Sam", "counterparty": "Bo", "due_hint": "Tuesday"},
            {"route": "book", "keyphrase": "Cedar Works finance lead",
             "gist": "introduce Bo to the Cedar Works finance lead",
             "owner": "Sam", "counterparty": "Bo", "due_hint": "this week"},
            {"route": "book", "keyphrase": "Acme usage report",
             "gist": "send Sam the Acme usage report by Friday",
             "owner": "Bo", "counterparty": "Sam", "due_hint": "Friday"},
            {"route": "review", "keyphrase": "customer case study",
             "gist": "draft the customer case study before the renewal",
             "owner": "Sam", "counterparty": "Bo",
             "why": "hedged (might be able to / no promises) but consequential"},
            {"route": "reject", "keyphrase": "rethink the whole onboarding flow",
             "why": "vague group intent, no owner, no deliverable"},
            {"route": "reject", "keyphrase": "cleaner dashboard would be nice",
             "why": "wishful, no owner"},
        ],
        "mentions": [
            {"surface": "Bo", "expected": "Bo Sample"},
            {"surface": "Cedar Works", "expected_org": "Cedar Works"},
        ],
    },
    {
        "id": "bench_02",
        "title": "Board prep",
        "attendees": ["Sam", "Mira"],
        "turns": [
            ("Sam", "board meeting is a week out, we need the materials moving"),
            ("Mira", "I'll pull the Q2 revenue numbers together by Thursday, finance already has the raw export"),
            ("Sam", "good. I'm going to draft the board deck by Friday so Quinn can sanity-check the hiring slide before it goes out"),
            ("Mira", "does the pre-read memo also go out this cycle?"),
            ("Sam", "I should be able to get the pre-read memo out ahead of the deck, I'll try for Wednesday"),
            ("Mira", "maybe we could add a customer-logo slide at some point"),
            ("Sam", "maybe. it would be nice to have a crisper story on churn too"),
            ("Mira", "one for the someday pile. two more things: I'll book the board dinner for Wednesday night, the usual place"),
            ("Sam", "do it"),
            ("Mira", "and Quinn told the auditors she'd send them the equity grants file by Tuesday, so that's moving"),
            ("Sam", "good, that closes us out"),
        ],
        "planted": [
            {"route": "book", "keyphrase": "Q2 revenue numbers",
             "gist": "pull the Q2 revenue numbers together by Thursday",
             "owner": "Mira", "counterparty": "Sam", "due_hint": "Thursday"},
            {"route": "book", "keyphrase": "draft the board deck",
             "gist": "draft the board deck by Friday",
             "owner": "Sam", "counterparty": "Mira", "due_hint": "Friday"},
            {"route": "review", "keyphrase": "pre-read memo",
             "gist": "get the pre-read memo out, aiming Wednesday",
             "owner": "Sam", "counterparty": "Mira",
             "why": "hedged (should be able to / try for) but consequential"},
            {"route": "reject", "keyphrase": "customer-logo slide",
             "why": "hypothetical, no owner"},
            {"route": "reject", "keyphrase": "crisper story on churn",
             "why": "wishful, no deliverable"},
            {"route": "book", "keyphrase": "board dinner",
             "gist": "book the board dinner for Wednesday night",
             "owner": "Mira", "counterparty": "Sam", "due_hint": "Wednesday",
             "kind": "scheduling"},
            {"route": "observed", "keyphrase": "equity grants file",
             "gist": "Quinn to send the auditors the equity grants file by Tuesday",
             "owner": "Quinn", "counterparty": None,
             "why": "third-party commitment to the auditors, relayed"},
        ],
        "mentions": [
            {"surface": "Quinn", "expected": "Quinn Sample"},
            {"surface": "Mira", "expected": "Mira Sample"},
        ],
    },
    {
        "id": "bench_03",
        "title": "Vendor contract call",
        "attendees": ["Sam", "Rio"],
        "turns": [
            ("Rio", "quick vendor update. Dustin is going to send the signed services contract over to Lyra tomorrow so her team can countersign"),
            ("Sam", "good, that one has dragged"),
            ("Rio", "and Bowie owes Lyra the security questionnaire, he told her end of week"),
            ("Sam", "fine. on our side, I'll get the vendor comparison matrix to you by Thursday so we can pick before the renewal date"),
            ("Rio", "perfect. oh and I already sent the W-9 last week, so that's done"),
            ("Sam", "great. now pull up the vendor portal and click the invite button real quick so I can see the flow"),
            ("Rio", "done, I'm in"),
            ("Sam", "nice. last thing on cleanup, anything on the old account?"),
            ("Rio", "I'll cancel the old vendor account before month end so we stop paying twice"),
            ("Sam", "good. we might want to consolidate the remaining vendors next year, but that's a later conversation"),
            ("Rio", "much later. that's all I needed"),
        ],
        "planted": [
            {"route": "observed", "keyphrase": "signed services contract",
             "gist": "Dustin to send the signed services contract to Lyra",
             "owner": "Dustin", "counterparty": "Lyra",
             "why": "third-party to third-party; workspace owner not a party"},
            {"route": "observed", "keyphrase": "security questionnaire",
             "gist": "Bowie owes Lyra the security questionnaire by end of week",
             "owner": "Bowie", "counterparty": "Lyra",
             "why": "third-party to third-party"},
            {"route": "book", "keyphrase": "vendor comparison matrix",
             "gist": "get the vendor comparison matrix to Rio by Thursday",
             "owner": "Sam", "counterparty": "Rio", "due_hint": "Thursday"},
            {"route": "reject", "keyphrase": "sent the W-9",
             "why": "past tense, already done"},
            {"route": "reject", "keyphrase": "click the invite button",
             "why": "live action completed on the call (J1 shape)"},
            {"route": "book", "keyphrase": "cancel the old vendor account",
             "gist": "cancel the old vendor account before month end",
             "owner": "Rio", "counterparty": "Sam", "due_hint": "month end"},
            {"route": "reject", "keyphrase": "consolidate the remaining vendors",
             "why": "deferred next-year intent, no commitment"},
        ],
        "mentions": [
            {"surface": "Dustin", "expected": "Dustin Sample"},
            {"surface": "Lyra", "expected": "Lyra Sample"},
            {"surface": "Bowie", "expected": "Bowie Sample"},
        ],
    },
    {
        "id": "bench_04",
        "title": "Hiring slate review",
        "attendees": ["Sam", "Quinn", "Aria"],
        "turns": [
            ("Sam", "hiring slate. where are the platform candidates?"),
            ("Quinn", "two finalists. I'll schedule the panel interviews for both candidates this week, calendars permitting"),
            ("Sam", "do it. I'll send you the offer template tonight so it's ready if Thursday goes well"),
            ("Quinn", "we still don't have a scoring rubric for the panel"),
            ("Aria", "someone should own the rubric... I guess I can take a stab at a draft"),
            ("Sam", "ok, loop me when there's something to react to"),
            ("Quinn", "we should also think about comp bands for next year at some point"),
            ("Sam", "not this week. anything else?"),
            ("Aria", "the team wants to look into a referral bonus eventually"),
            ("Sam", "someday. anything already in motion?"),
            ("Aria", "I already pinged the recruiter about the pipeline yesterday, waiting to hear back. and I'll post the job description for the data role tomorrow morning"),
            ("Sam", "good, done"),
        ],
        "planted": [
            {"route": "book", "keyphrase": "panel interviews",
             "gist": "schedule the panel interviews for both candidates this week",
             "owner": "Quinn", "counterparty": "Sam", "due_hint": "this week"},
            {"route": "book", "keyphrase": "offer template",
             "gist": "send Quinn the offer template tonight",
             "owner": "Sam", "counterparty": "Quinn", "due_hint": "tonight"},
            {"route": "review", "keyphrase": "stab at a draft",
             "gist": "Aria drafts the panel scoring rubric",
             "owner": "Aria", "counterparty": "Quinn",
             "why": "hedged self-assignment (I guess I can), consequential"},
            {"route": "reject", "keyphrase": "comp bands",
             "why": "vague group intent, deferred, no owner"},
            {"route": "reject", "keyphrase": "referral bonus",
             "why": "unowned team wish, someday"},
            {"route": "reject", "keyphrase": "pinged the recruiter",
             "why": "past tense, already done"},
            {"route": "book", "keyphrase": "job description for the data role",
             "gist": "post the job description for the data role tomorrow morning",
             "owner": "Aria", "counterparty": "Sam", "due_hint": "tomorrow"},
        ],
        "mentions": [
            {"surface": "Quinn", "expected": "Quinn Sample"},
            {"surface": "Aria", "expected": "Aria Sample"},
        ],
    },
    {
        "id": "bench_05",
        "title": "Data room walkthrough",
        "attendees": ["Sam", "Bo"],
        "turns": [
            ("Bo", "the export from the diligence folder is the missing piece, the historicals all live in that instance"),
            ("Sam", "I should be able to run the diligence folder export and get you the historicals on our check-in tomorrow"),
            ("Bo", "actually you don't need that instance, the shared drive export already covers the historicals"),
            ("Sam", "oh good, that saves a step"),
            ("Bo", "one real item: can you send the updated cap table to counsel by Wednesday? they're blocked on it"),
            ("Sam", "yes, will do, Wednesday at the latest"),
            ("Bo", "also met a sharp operator last week, Skyler Stone, might be worth a coffee sometime"),
            ("Sam", "put it on the someday list, we should focus. one real item on my side: I'll send the wire instructions to counsel today so closing isn't blocked on us"),
            ("Bo", "good. I could probably pull together an investor FAQ if the inbound keeps up, we'll see"),
            ("Sam", "keep it in your back pocket. last thing, open the diligence tracker and rename the June folder right now so we stop confusing versions"),
            ("Bo", "renamed. done here"),
        ],
        "planted": [
            {"route": "reject", "keyphrase": "diligence folder export",
             "why": "retracted in the same exchange (J2 shape) -- counterparty withdrew the need"},
            {"route": "book", "keyphrase": "updated cap table",
             "gist": "send the updated cap table to counsel by Wednesday",
             "owner": "Sam", "counterparty": "Bo", "due_hint": "Wednesday"},
            {"route": "reject", "keyphrase": "worth a coffee",
             "why": "vague someday intent, no deliverable"},
            {"route": "book", "keyphrase": "wire instructions",
             "gist": "send the wire instructions to counsel today",
             "owner": "Sam", "counterparty": "Bo", "due_hint": "today"},
            {"route": "review", "keyphrase": "investor FAQ",
             "gist": "Bo pulls together an investor FAQ if inbound keeps up",
             "owner": "Bo", "counterparty": "Sam",
             "why": "hedged conditional (could probably / we'll see)"},
            {"route": "reject", "keyphrase": "rename the June folder",
             "why": "live action completed on the call (J1 shape)"},
        ],
        "mentions": [
            {"surface": "Skyler Stone", "expected_unknown": True},
        ],
    },
    {
        "id": "bench_06",
        "title": "Partner renewal sync",
        "attendees": ["Sam", "Lyra"],
        "turns": [
            ("Lyra", "Northstar Partners renewal. Aria is going to send Northstar the renewal terms on Monday, she confirmed this morning"),
            ("Sam", "good. and their data feed issue?"),
            ("Lyra", "Bowie told the Northstar team he'd get them the corrected data feed by Friday"),
            ("Sam", "fine. I'll follow up with the Northstar Partners exec sponsor next week to make sure the renewal lands"),
            ("Lyra", "worth it, they're our biggest partner"),
            ("Sam", "anything else? we could theoretically bundle the Category Company pilot into the same paper someday"),
            ("Lyra", "theoretically. not this quarter. before I forget, I'll send you the partner health dashboard link tonight so you can watch the feed fix land"),
            ("Sam", "perfect. one day we should automate all this partner reporting"),
            ("Lyra", "one day"),
        ],
        "planted": [
            {"route": "observed", "keyphrase": "renewal terms on Monday",
             "gist": "Aria to send Northstar the renewal terms on Monday",
             "owner": "Aria", "counterparty": None,
             "why": "third-party to external org"},
            {"route": "observed", "keyphrase": "corrected data feed",
             "gist": "Bowie to get Northstar the corrected data feed by Friday",
             "owner": "Bowie", "counterparty": None,
             "why": "third-party to external org"},
            {"route": "book", "keyphrase": "exec sponsor next week",
             "gist": "follow up with the Northstar Partners exec sponsor",
             "owner": "Sam", "counterparty": "Lyra", "due_hint": "next week"},
            {"route": "reject", "keyphrase": "bundle the Category Company pilot",
             "why": "hypothetical (theoretically / someday)"},
            {"route": "book", "keyphrase": "partner health dashboard",
             "gist": "send Sam the partner health dashboard link tonight",
             "owner": "Lyra", "counterparty": "Sam", "due_hint": "tonight"},
            {"route": "reject", "keyphrase": "automate all this partner reporting",
             "why": "one-day musing, no owner"},
        ],
        "mentions": [
            {"surface": "Northstar", "expected_org": "Northstar Partners"},
            {"surface": "Aria", "expected": "Aria Sample"},
        ],
    },
    {
        "id": "bench_07",
        "title": "Ops standup",
        "attendees": ["Sam", "Dustin", "Bowie"],
        "turns": [
            ("Dustin", "migration status: I'll have the server inventory list finished by Wednesday, that unblocks the cutover plan"),
            ("Sam", "good. Bowie, the runbook?"),
            ("Bowie", "I'll write the cutover runbook by Friday and walk the team through it Monday"),
            ("Sam", "ok. who owns the customer comms?"),
            ("Dustin", "we'll get the comms drafted at some point before cutover"),
            ("Sam", "that's not an owner. park it for now"),
            ("Bowie", "we should probably also revisit the backup vendor eventually"),
            ("Sam", "eventually. status on the maintenance window?"),
            ("Dustin", "waiting on you. Mira also promised the datacenter vendor she'd sign the SOW by Thursday, so hardware is covered"),
            ("Sam", "then I'll approve the maintenance window request this afternoon so nothing slips"),
            ("Bowie", "zero-downtime would be great someday"),
            ("Sam", "someday. standup done"),
        ],
        "planted": [
            {"route": "book", "keyphrase": "server inventory list",
             "gist": "finish the server inventory list by Wednesday",
             "owner": "Dustin", "counterparty": "Sam", "due_hint": "Wednesday"},
            {"route": "book", "keyphrase": "cutover runbook",
             "gist": "write the cutover runbook by Friday",
             "owner": "Bowie", "counterparty": "Sam", "due_hint": "Friday"},
            {"route": "reject", "keyphrase": "comms drafted at some point",
             "why": "'we' with no named individual -- fails the owned test, and flagged so on the call"},
            {"route": "reject", "keyphrase": "revisit the backup vendor",
             "why": "vague group intent, eventually"},
            {"route": "observed", "keyphrase": "sign the SOW",
             "gist": "Mira to sign the datacenter vendor SOW by Thursday",
             "owner": "Mira", "counterparty": None,
             "why": "third-party promise to a vendor, relayed"},
            {"route": "book", "keyphrase": "maintenance window request",
             "gist": "approve the maintenance window request this afternoon",
             "owner": "Sam", "counterparty": "Dustin", "due_hint": "this afternoon"},
            {"route": "reject", "keyphrase": "zero-downtime",
             "why": "wishful, someday"},
        ],
        "mentions": [
            {"surface": "Dustin", "expected": "Dustin Sample"},
            {"surface": "Bowie", "expected": "Bowie Sample"},
        ],
    },
    {
        "id": "bench_08",
        "title": "Customer escalation",
        "attendees": ["Sam", "Mira"],
        "turns": [
            ("Mira", "the Acme Co outage hit their month-end close, their COO is upset"),
            ("Sam", "I'll call the Acme Co chief operating officer today, before five, this can't sit"),
            ("Mira", "I'll write the incident postmortem by Thursday and send it to their team, they asked for it in writing"),
            ("Sam", "good. anything on the credit?"),
            ("Mira", "Rio told their account manager he'd process the service credit this week"),
            ("Sam", "fine, keep me posted. you can reach me through mira.sample7@example.com threads if I'm slow on the main channel, just re-ping"),
            ("Mira", "ha, that's my address. I'll re-ping"),
            ("Sam", "two more from me. I'll send you the escalation contact sheet tonight so you're not guessing who to wake up"),
            ("Mira", "please"),
            ("Sam", "and I'll try to get an exec summary in front of their CEO this week, travel permitting"),
            ("Mira", "we should probably revisit the SLA tiers at some point after this settles"),
            ("Sam", "at some point. go"),
        ],
        "planted": [
            {"route": "book", "keyphrase": "chief operating officer today",
             "gist": "call the Acme Co COO today before five",
             "owner": "Sam", "counterparty": "Mira", "due_hint": "today"},
            {"route": "book", "keyphrase": "incident postmortem",
             "gist": "write the incident postmortem by Thursday and send it to Acme Co",
             "owner": "Mira", "counterparty": "Sam", "due_hint": "Thursday"},
            {"route": "observed", "keyphrase": "service credit",
             "gist": "Rio to process the Acme Co service credit this week",
             "owner": "Rio", "counterparty": None,
             "why": "third-party promise relayed secondhand"},
            {"route": "book", "keyphrase": "escalation contact sheet",
             "gist": "send Mira the escalation contact sheet tonight",
             "owner": "Sam", "counterparty": "Mira", "due_hint": "tonight"},
            {"route": "review", "keyphrase": "exec summary",
             "gist": "get an exec summary in front of the Acme Co CEO this week",
             "owner": "Sam", "counterparty": "Mira",
             "why": "hedged (try / travel permitting) but consequential"},
            {"route": "reject", "keyphrase": "SLA tiers",
             "why": "vague at-some-point group intent"},
        ],
        "mentions": [
            {"surface": "mira.sample7@example.com", "expected": "Mira Sample"},
            {"surface": "Acme Co", "expected_org": "Acme Co"},
        ],
    },
    {
        "id": "bench_09",
        "title": "Quarterly planning kickoff",
        "attendees": ["Sam", "Aria"],
        "turns": [
            ("Aria", "planning kickoff is in two weeks, what do you need from me?"),
            ("Sam", "I'll send you the planning template and last quarter's scorecard by end of day Friday"),
            ("Aria", "ok. I might try to get department pre-reads collected before kickoff, if the leads cooperate"),
            ("Sam", "that would help. no promises needed yet"),
            ("Aria", "it would be great if the whole thing fit in one week this year"),
            ("Sam", "wouldn't it. if we ever hire a chief of staff, planning is the first thing they take"),
            ("Aria", "dreams. two loose ends: I'll circulate the kickoff agenda by Monday so nobody claims surprise"),
            ("Sam", "good"),
            ("Aria", "and Bo told finance he'd close out the budget template by Friday, so the numbers side is handled"),
            ("Sam", "ok, I'm set"),
        ],
        "planted": [
            {"route": "book", "keyphrase": "planning template",
             "gist": "send Aria the planning template and scorecard by Friday EOD",
             "owner": "Sam", "counterparty": "Aria", "due_hint": "Friday"},
            {"route": "review", "keyphrase": "department pre-reads",
             "gist": "Aria collects department pre-reads before kickoff",
             "owner": "Aria", "counterparty": "Sam",
             "why": "hedged (might try), consequential if it happens"},
            {"route": "reject", "keyphrase": "fit in one week",
             "why": "wishful"},
            {"route": "reject", "keyphrase": "chief of staff",
             "why": "hypothetical (if we ever)"},
            {"route": "book", "keyphrase": "kickoff agenda",
             "gist": "circulate the kickoff agenda by Monday",
             "owner": "Aria", "counterparty": "Sam", "due_hint": "Monday"},
            {"route": "observed", "keyphrase": "budget template",
             "gist": "Bo to close out the budget template with finance by Friday",
             "owner": "Bo", "counterparty": None,
             "why": "third-party commitment to finance, relayed"},
        ],
        "mentions": [
            {"surface": "Aria", "expected": "Aria Sample"},
        ],
    },
    {
        "id": "bench_10",
        "title": "Fundraise check-in",
        "attendees": ["Sam", "Bo", "Quinn"],
        "turns": [
            ("Bo", "two investors asked for the data room this week"),
            ("Sam", "I'll send you both the data room checklist tomorrow so we populate it once, properly"),
            ("Quinn", "I'll update the financial model with the May actuals by Wednesday, the old version is embarrassing"),
            ("Sam", "good. legal?"),
            ("Bo", "Rio said he'll finish the legal review of the SAFE docs before the partner meeting"),
            ("Sam", "ok. and no, we are not redoing the brand ahead of the raise, whoever keeps floating that"),
            ("Quinn", "it does keep coming up. maybe a narrative workshop one day"),
            ("Sam", "one day. anything else before we break?"),
            ("Bo", "I'll schedule the partner meeting prep call for Monday morning, thirty minutes"),
            ("Quinn", "works. I might get the cohort analysis in before that partner meeting too, depends on the data pull"),
            ("Bo", "even directional helps. oh and I already refreshed the pitch deck last night, so that's current"),
            ("Sam", "good, done here"),
        ],
        "planted": [
            {"route": "book", "keyphrase": "data room checklist",
             "gist": "send Bo and Quinn the data room checklist tomorrow",
             "owner": "Sam", "counterparty": "Bo", "due_hint": "tomorrow"},
            {"route": "book", "keyphrase": "May actuals",
             "gist": "update the financial model with May actuals by Wednesday",
             "owner": "Quinn", "counterparty": "Sam", "due_hint": "Wednesday"},
            {"route": "observed", "keyphrase": "legal review of the SAFE",
             "gist": "Rio to finish the SAFE docs legal review before the partner meeting",
             "owner": "Rio", "counterparty": "Bo",
             "why": "third-party promise relayed by Bo"},
            {"route": "reject", "keyphrase": "narrative workshop",
             "why": "someday musing"},
            {"route": "book", "keyphrase": "partner meeting prep call",
             "gist": "schedule the partner meeting prep call for Monday morning",
             "owner": "Bo", "counterparty": "Sam", "due_hint": "Monday",
             "kind": "scheduling"},
            {"route": "review", "keyphrase": "cohort analysis",
             "gist": "Quinn gets the cohort analysis in before the partner meeting",
             "owner": "Quinn", "counterparty": "Bo",
             "why": "hedged (might / depends on the data pull)"},
            {"route": "reject", "keyphrase": "refreshed the pitch deck",
             "why": "past tense, already done"},
        ],
        "mentions": [
            {"surface": "Rio", "expected": "Rio Sample"},
        ],
    },
    {
        "id": "bench_11",
        "title": "Calendar and scheduling chatter",
        "attendees": ["Sam", "Dustin"],
        "turns": [
            ("Dustin", "we should grab time to go through the platform roadmap properly"),
            ("Sam", "agreed. can you grab thirty minutes on my calendar Thursday afternoon for the roadmap walkthrough?"),
            ("Dustin", "sure, I'll book the Thursday slot when we hang up"),
            ("Sam", "let's also do a team lunch sometime soon"),
            ("Dustin", "sometime, yes. and one day we should visit the Bluebird Group office, they keep offering"),
            ("Sam", "one day. also remind me, did the printer thing ever get fixed?"),
            ("Dustin", "it did, last month"),
            ("Sam", "almost. I'll send you the roadmap doc before the Thursday walkthrough so you're not reading it cold"),
            ("Dustin", "appreciated. we should really fix the conference room screen one of these days"),
            ("Sam", "one of these days. now we're done"),
        ],
        "planted": [
            {"route": "book", "keyphrase": "Thursday slot",
             "gist": "book 30 minutes Thursday afternoon for the roadmap walkthrough",
             "owner": "Dustin", "counterparty": "Sam", "due_hint": "Thursday",
             "kind": "scheduling"},
            {"route": "reject", "keyphrase": "team lunch",
             "why": "vague scheduling intent (sometime soon)"},
            {"route": "reject", "keyphrase": "visit the Bluebird Group office",
             "why": "one-day intent, no commitment"},
            {"route": "reject", "keyphrase": "printer thing",
             "why": "past, already resolved"},
            {"route": "book", "keyphrase": "roadmap doc",
             "gist": "send Dustin the roadmap doc before the Thursday walkthrough",
             "owner": "Sam", "counterparty": "Dustin", "due_hint": "Thursday"},
            {"route": "reject", "keyphrase": "conference room screen",
             "why": "one-of-these-days group gripe, no owner"},
        ],
        "mentions": [
            {"surface": "Bluebird Group", "expected_org": "Bluebird Group"},
        ],
    },
    {
        "id": "bench_12",
        "title": "All-hands recap",
        "attendees": ["Sam", "Lyra", "Bowie"],
        "turns": [
            ("Lyra", "recapping the all-hands follow-ups. Mira committed to publishing the OKR tracker to the whole team by Monday"),
            ("Sam", "good, that one matters"),
            ("Bowie", "and Quinn told the support leads she'd deliver the escalation training session next week"),
            ("Sam", "ok. my one item: I'll record the async QA video for the questions we didn't get to, this week"),
            ("Lyra", "people will appreciate that"),
            ("Bowie", "there was also the perennial ask for better snacks"),
            ("Sam", "the snack question survives every reorg. noted, not tracked"),
            ("Lyra", "and someone suggested we should explore a four-day week pilot eventually"),
            ("Sam", "eventually. Bowie, can you compile the open questions doc from the all-hands by tomorrow so nothing gets lost?"),
            ("Bowie", "yes, I'll have the questions doc out by tomorrow"),
            ("Sam", "then wrap it there. if we hit the number this quarter, spring offsite is back on the table"),
            ("Lyra", "motivating. wrapped"),
        ],
        "planted": [
            {"route": "observed", "keyphrase": "OKR tracker",
             "gist": "Mira to publish the OKR tracker to the team by Monday",
             "owner": "Mira", "counterparty": None,
             "why": "third-party commitment to the team, relayed"},
            {"route": "observed", "keyphrase": "escalation training",
             "gist": "Quinn to deliver the escalation training session next week",
             "owner": "Quinn", "counterparty": None,
             "why": "third-party commitment to support leads, relayed"},
            {"route": "book", "keyphrase": "async QA video",
             "gist": "record the async QA video this week",
             "owner": "Sam", "counterparty": "Lyra", "due_hint": "this week"},
            {"route": "reject", "keyphrase": "better snacks",
             "why": "explicitly declared not tracked on the call"},
            {"route": "reject", "keyphrase": "four-day week pilot",
             "why": "unowned suggestion, eventually"},
            {"route": "book", "keyphrase": "questions doc",
             "gist": "compile the all-hands open questions doc by tomorrow",
             "owner": "Bowie", "counterparty": "Sam", "due_hint": "tomorrow"},
            {"route": "reject", "keyphrase": "spring offsite",
             "why": "conditional on hitting the number (hypothetical)"},
        ],
        "mentions": [
            {"surface": "Lyra", "expected": "Lyra Sample"},
            {"surface": "Quinn", "expected": "Quinn Sample"},
        ],
    },
]


# --------------------------------------------------------------------------


def load_roster(fixtures_root: Path) -> dict:
    ents = json.loads((fixtures_root / "_hq" / "data" / "entities.json")
                      .read_text(encoding="utf-8"))
    people = {p["canonical_name"].split()[0]: p
              for p in ents["entities"]["people"]}
    orgs = {o["canonical_name"]: o for o in ents["entities"]["orgs"]}
    primary_id = (ents.get("workspace") or {}).get("primary_user_id")
    return {"people": people, "orgs": orgs, "primary_user_id": primary_id}


def full_name(roster: dict, first: str) -> str:
    if first not in roster["people"]:
        raise SystemExit(f"FATAL: first name '{first}' not in fixture roster "
                         f"({sorted(roster['people'])}). Regenerate fixtures or fix the set.")
    return roster["people"][first]["canonical_name"]


def render_transcript(t: dict, roster: dict) -> str:
    lines = [f"{full_name(roster, spk)}: {text}" for spk, text in t["turns"]]
    return "\n".join(lines) + "\n"


def build_labels(t: dict, roster: dict, text: str) -> dict:
    planted = []
    for i, item in enumerate(t["planted"], 1):
        row = {
            "label_id": f"{t['id']}_c{i}",
            "expected_route": item["route"],
            "keyphrase": item["keyphrase"],
        }
        if item["route"] != "reject":
            row["gist"] = item["gist"]
            row["owner_name"] = full_name(roster, item["owner"]) if item.get("owner") else None
            cp = item.get("counterparty")
            row["counterparty_name"] = full_name(roster, cp) if cp else None
            if item.get("due_hint"):
                row["due_hint"] = item["due_hint"]
            if item.get("kind"):
                row["kind"] = item["kind"]
        if item.get("why"):
            row["why"] = item["why"]
        planted.append(row)

    mentions = []
    for i, m in enumerate(t["mentions"], 1):
        row = {"label_id": f"{t['id']}_e{i}", "surface": m["surface"]}
        if m.get("expected_unknown"):
            row["expected"] = "UNKNOWN_PERSON"
            row["note"] = ("roster-legal name absent from entities.json; correct handling "
                           "is an unknown-person outcome (proposal/annotation), never a "
                           "silent bind to an existing person")
        elif m.get("expected_org"):
            row["expected_org"] = m["expected_org"]
        else:
            row["expected"] = m["expected"]
        mentions.append(row)

    return {
        "transcript_id": t["id"],
        "set_version": SET_VERSION,
        "title": t["title"],
        "meeting_date": BASE_DATE,
        "attendees": [full_name(roster, a) for a in t["attendees"]],
        "primary_user": full_name(roster, "Sam"),
        "planted": planted,
        "entity_mentions": mentions,
    }


def validate(roster: dict, rendered: dict[str, str], labels: dict[str, dict]) -> list[str]:
    errors: list[str] = []

    # 1. Every keyphrase appears in exactly one transcript, its own.
    for tid, lab in labels.items():
        for item in lab["planted"]:
            kp = item["keyphrase"].lower()
            hits = [t for t, txt in rendered.items() if kp in txt.lower()]
            if hits != [tid]:
                errors.append(f"{item['label_id']}: keyphrase '{kp}' found in {hits}, "
                              f"expected exactly ['{tid}']")
        for m in lab["entity_mentions"]:
            if m["surface"].lower() not in rendered[tid].lower():
                errors.append(f"{m['label_id']}: mention surface '{m['surface']}' "
                              f"not present in {tid}")

    # 2. Roster safety: every Capitalized-bigram name is roster or known-unknown.
    legal_names = {p["canonical_name"] for p in roster["people"].values()}
    legal_names |= set(KNOWN_UNKNOWNS)
    legal_orgs = set(roster["orgs"])
    bigram = re.compile(r"\b([A-Z][a-z]+) ([A-Z][a-z]+)\b")
    org_words = {w for o in legal_orgs for w in o.split()}
    for tid, txt in rendered.items():
        for m in bigram.finditer(txt):
            name = m.group(0)
            if name in legal_names or name in legal_orgs:
                continue
            if m.group(1) in org_words or m.group(2) in org_words:
                continue  # org fragments like "Cedar Works finance"
            errors.append(f"{tid}: name-shaped bigram '{name}' is neither roster, "
                          f"known-unknown, nor org")

    # 3. Route bookkeeping matches the declared distribution.
    counts: dict[str, int] = {}
    for lab in labels.values():
        for item in lab["planted"]:
            counts[item["expected_route"]] = counts.get(item["expected_route"], 0) + 1
    for route in ("book", "review", "observed", "reject"):
        if counts.get(route, 0) == 0:
            errors.append(f"route '{route}' has zero planted items")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixtures-root", default=str(DEFAULT_FIXTURES),
                    help="path to the clean_workspace fixture")
    ap.add_argument("--check", action="store_true", help="validate only; write nothing")
    args = ap.parse_args()

    roster = load_roster(Path(args.fixtures_root))
    rendered = {t["id"]: render_transcript(t, roster) for t in TRANSCRIPTS}
    labels = {t["id"]: build_labels(t, roster, rendered[t["id"]]) for t in TRANSCRIPTS}

    errors = validate(roster, rendered, labels)
    if errors:
        print("VALIDATION FAILED:")
        for e in errors:
            print("  -", e)
        return 1

    counts: dict[str, int] = {}
    for lab in labels.values():
        for item in lab["planted"]:
            counts[item["expected_route"]] = counts.get(item["expected_route"], 0) + 1
    n_mentions = sum(len(lab["entity_mentions"]) for lab in labels.values())

    print(f"transcripts : {len(TRANSCRIPTS)}")
    print(f"routes      : {dict(sorted(counts.items()))}")
    print(f"mentions    : {n_mentions}")

    if args.check:
        print("--check: validation passed, nothing written.")
        return 0

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "labels").mkdir(exist_ok=True)
    manifest = {
        "set_version": SET_VERSION,
        "generated_by": "_generate_bench_transcripts.py (deterministic; do not hand-edit)",
        "meeting_date": BASE_DATE,
        "transcript_count": len(TRANSCRIPTS),
        "route_counts": dict(sorted(counts.items())),
        "entity_mention_count": n_mentions,
        "known_unknowns": KNOWN_UNKNOWNS,
        "transcripts": [],
    }
    for t in TRANSCRIPTS:
        tid = t["id"]
        (OUT_DIR / f"{tid}.txt").write_text(rendered[tid], encoding="utf-8")
        (OUT_DIR / "labels" / f"{tid}.labels.json").write_text(
            json.dumps(labels[tid], indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        manifest["transcripts"].append({
            "id": tid, "title": t["title"],
            "attendees": labels[tid]["attendees"],
            "planted": len(labels[tid]["planted"]),
        })
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {len(TRANSCRIPTS)} transcripts + labels to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
