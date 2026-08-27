
### bench_01 — Weekly pipeline sync
    book=3 review=1 observed=0 skipped=0 floor_gated=1 deduped=0 fusion_inert=0
      BOOK     send Bo the revised Acme Co pricing sheet                      carries a due date or money — always surfaces
      BOOK     introduce Bo to the Cedar Works finance lead                   carries a due date or money — always surfaces
      BOOK     send Sam the Acme usage report for the renewal call            carries a due date or money — always surfaces
      REVIEW   draft the Acme customer case study before the renewal          discussed, never accepted as a commitment

### bench_02 — Board prep
    book=5 review=0 observed=0 skipped=0 floor_gated=0 deduped=0 fusion_inert=0
      BOOK     pull together the Q2 revenue numbers                           carries a due date or money — always surfaces
      BOOK     draft the board deck for Quinn to sanity-check                 carries a due date or money — always surfaces
      BOOK     send out the board pre-read memo ahead of the deck             carries a due date or money — always surfaces
      BOOK     book the board dinner for Wednesday night                      carries a due date or money — always surfaces
      BOOK     send the auditors the equity grants file                       carries a due date or money — always surfaces

### bench_03 — Vendor contract call
    book=3 review=1 observed=2 skipped=0 floor_gated=1 deduped=0 fusion_inert=0
      BOOK     send Lyra the signed services contract to countersign          carries a due date or money — always surfaces
      BOOK     send Lyra the security questionnaire                           carries a due date or money — always surfaces
      REVIEW   send Rio the vendor comparison matrix                          already done during the call, nothing left afterwards
      OBSERVED open the vendor portal and click the invite button             between other people
      OBSERVED introduce Lyra to the Cedar Works ops lead                     between other people
      BOOK     cancel the old vendor account so we stop paying twice          carries a due date or money — always surfaces

### bench_04 — Hiring slate review
    book=3 review=0 observed=1 skipped=0 floor_gated=0 deduped=0 fusion_inert=0
      BOOK     schedule the panel interviews for both platform finalists      carries a due date or money — always surfaces
      BOOK     send Quinn the offer template                                  carries a due date or money — always surfaces
      OBSERVED draft the panel scoring rubric                                 discussed, never accepted as a commitment
      BOOK     post the job description for the data role                     carries a due date or money — always surfaces

### bench_05 — Data room walkthrough
    book=3 review=1 observed=1 skipped=0 floor_gated=1 deduped=0 fusion_inert=0
      REVIEW   run the diligence folder export and send Bo the historicals    taken back later in the same conversation
      BOOK     send counsel the updated cap table                             carries a due date or money — always surfaces
      BOOK     send counsel the wire instructions so closing isn't blocked    carries a due date or money — always surfaces
      BOOK     pull together an investor FAQ                                  you are a party
      OBSERVED rename the June folder in the diligence tracker                nothing depends on it

### bench_06 — Partner renewal sync
    book=4 review=0 observed=1 skipped=0 floor_gated=0 deduped=0 fusion_inert=0
      BOOK     send Northstar Partners the renewal terms                      carries a due date or money — always surfaces
      BOOK     send the Northstar team the corrected data feed                carries a due date or money — always surfaces
      BOOK     follow up with the Northstar Partners exec sponsor on the rene carries a due date or money — always surfaces
      OBSERVED walk the Northstar team through the reporting portal           couldn't confidently tell whose this is
      BOOK     send Sam the partner health dashboard link                     carries a due date or money — always surfaces

### bench_07 — Ops standup
    book=5 review=0 observed=1 skipped=0 floor_gated=0 deduped=0 fusion_inert=0
      BOOK     finish the server inventory list to unblock the cutover plan   carries a due date or money — always surfaces
      BOOK     write the cutover runbook                                      carries a due date or money — always surfaces
      BOOK     walk the team through the cutover runbook                      carries a due date or money — always surfaces
      BOOK     sign the datacenter vendor SOW                                 carries a due date or money — always surfaces
      OBSERVED send the network vendor an updated contact list                retold from an earlier conversation, not committed here
      BOOK     approve the maintenance window request                         carries a due date or money — always surfaces

### bench_08 — Customer escalation
    book=5 review=0 observed=0 skipped=0 floor_gated=0 deduped=0 fusion_inert=0
      BOOK     call the Acme Co chief operating officer about the outage      carries a due date or money — always surfaces
      BOOK     write the incident postmortem and send it to the Acme Co team  carries a due date or money — always surfaces
      BOOK     process the Acme Co service credit                             carries a due date or money — always surfaces
      BOOK     send Mira the escalation contact sheet                         carries a due date or money — always surfaces
      BOOK     get an exec summary in front of the Acme Co CEO                you are a party

### bench_09 — Quarterly planning kickoff
    book=4 review=0 observed=0 skipped=0 floor_gated=0 deduped=0 fusion_inert=0
      BOOK     send Aria the planning template and last quarter's scorecard   carries a due date or money — always surfaces
      BOOK     collect department pre-reads before the planning kickoff       you are a party
      BOOK     circulate the planning kickoff agenda                          carries a due date or money — always surfaces
      BOOK     close out the budget template for finance                      carries a due date or money — always surfaces

### bench_10 — Fundraise check-in
    book=5 review=0 observed=0 skipped=0 floor_gated=0 deduped=0 fusion_inert=0
      BOOK     send Bo and Quinn the data room checklist                      carries a due date or money — always surfaces
      BOOK     update the financial model with the May actuals                carries a due date or money — always surfaces
      BOOK     finish the legal review of the SAFE docs before the partner me you are a party
      BOOK     schedule the partner meeting prep call                         carries a due date or money — always surfaces
      BOOK     run the cohort analysis before the partner meeting             you are a party

### bench_11 — Calendar and scheduling chatter
    book=2 review=0 observed=0 skipped=0 floor_gated=0 deduped=0 fusion_inert=0
      BOOK     book thirty minutes Thursday for the roadmap walkthrough       carries a due date or money — always surfaces
      BOOK     send Dustin the roadmap doc before the walkthrough             carries a due date or money — always surfaces

### bench_12 — All-hands recap
    book=4 review=0 observed=1 skipped=0 floor_gated=0 deduped=0 fusion_inert=0
      BOOK     publish the OKR tracker to the whole team                      carries a due date or money — always surfaces
      BOOK     deliver the escalation training session for the support leads  carries a due date or money — always surfaces
      BOOK     record the async QA video for the unanswered all-hands questio carries a due date or money — always surfaces
      OBSERVED run a tools walkthrough for the interns                        couldn't confidently tell whose this is
      BOOK     compile the open questions doc from the all-hands              carries a due date or money — always surfaces

==============================================================================
VERDICT TIERS: Counter({'book': 46, 'observed': 7, 'review': 3})
FUSION: Counter({'verified': 56})
FLOOR CODES: Counter({'FLOOR_NOT_ACCEPTED': 2, 'FLOOR_DONE_IN_MEETING': 1, 'FLOOR_SUPERSEDED_IN_MEETING': 1, 'FLOOR_NO_CONSEQUENCE': 1, 'FLOOR_RETOLD': 1})
TOTAL EVENTS TO APPEND: 56
  commitment: 49
  observed  : 7
batch written to batch.json
DRY RUN — nothing written to events.jsonl
