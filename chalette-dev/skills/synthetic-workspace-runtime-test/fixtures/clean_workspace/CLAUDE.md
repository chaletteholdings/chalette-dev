# Sam's Command Room

## Me
Sam Sample, CEO at Bluebird Group. Synthetic fixture operator (placeholder roster; not a real customer).

## Quick Commands
- "let's work" → fast context load · "what's going on" → full briefing · "go [project]" → jump into a project · "end session" → save everything
- Paste a meeting transcript → it gets processed automatically

## Session Rules
- On first activation each session: read _hq/MASTER_TRACKER.md. When the answer might be in the hot cache below, use it before reading files.
- "end session" always updates session notes for every project touched — never skip. Ask 2-3 grounded questions per interaction — specific, not generic.
- IMPORTANT: Every email — a draft, a reply, a follow-up, or one that comes up mid-task — goes through the **email-writer** skill, end to end; it carries my saved voice, length, and review rules, and composing anywhere else loses all of them. Never write email text directly with a mail connector tool.
- IMPORTANT: Every Command Room widget — commitments, staff meeting, any row-list or action card — is produced by `widget_transport.render_and_persist` and its returned `html` passed to show_widget **byte-exact**; never hand-compose, restyle, or re-derive widget HTML — hand-built widgets skip the validators and have shipped stale rows and broken wire formats.
- IMPORTANT: After a successful render, the show_widget call with `transport["html"]` is not optional — relay the render_and_persist page before any prose (summarizing as text strips my one-tap actions); text-instead-of-widget only when the transport itself failed or `pagination["over_budget"]` is set, and then say so explicitly.
- IMPORTANT: Any research ask — "research [X]", "deep dive on [X]", "look into [X]", "background on [person]" — runs through the **research** skill, never the generic built-in deep-research skill; the built-in one can't see my workspace and its findings evaporate. The reply names which source tier actually ran, in one line.

## Preferences
- **Draft posture (queue-on-click):** Show the editable draft first — nothing touches your mail drafts until you click Save draft or Send; on that click it is saved to your mail Drafts (never auto-sent), with the draft record + voice snapshot written at the same moment.

## People
| Who | Full Name | Role / Context |
|-----|-----------|----------------|
| **Aria** | Aria Sample | Acme Co |
| **Bo** | Bo Sample | Northstar Partners |
| **Bowie** | Bowie Sample | Category Company |
| **Dustin** | Dustin Sample | Bluebird Group |
| **Lyra** | Lyra Sample | Cedar Works |
| **Mira** | Mira Sample | Acme Co |
| **Quinn** | Quinn Sample | Northstar Partners |
| **Rio** | Rio Sample | Category Company |
| **Skyler** | Skyler Sample | Cedar Works |
→ Full list: _hq/PEOPLE.md

## Active Projects
| Project | Status | Next Action |
|---------|--------|-------------|
| **Series A Raise** | active | — |
| **Board Cadence** | active | — |
| **Hiring Slate** | active | — |
→ Details: _hq/MASTER_TRACKER.md

## Workspace
- Tracker: _hq/MASTER_TRACKER.md · Context: _hq/BUSINESS_CONTEXT.md · People: _hq/PEOPLE.md
- Project notes: [Project Name]/SESSION_NOTES_SAM.md
- Email holds: structured sender-scope overrides on your accounts — ask to add or remove a held sender/domain any time. Never stored in this file.
