# Positioning and brand: the working sheet

For Isabella and Erick, while Chalette is being rebranded and repositioned. Started 2026-10-26. Matthew decides every row.

**Almost nothing about the message is decided.** The look has six dated rulings from 2026-10-24. The words (what we call ourselves, the headline, the one-liner, the guarantee sentence, the story) are open or working drafts. This sheet is the source of truth for which is which until the rebrand is finished.

## How to read it

| Status | Means | What you do |
|---|---|---|
| **Ruled** | Matthew decided, on the date shown | Use it. Only Matthew reopens it |
| **Working** | The current best version, not final | Use it in drafts and internal work. Ask Matthew before it goes in front of anyone outside |
| **Open** | Undecided, often with two versions in circulation | Do not pick a side in anything public. Bring options to Matthew |
| **Retired** | Dropped on purpose | Never use it, even when an older file still says it |

**Which file wins.** For whether something is decided: this sheet. For the exact values and wording: the Chalette Design System artifact (below). Anything else, including the July positioning document, older decks and Erick's copy of the July positioning, is history for wording. If a file disagrees with this sheet, this sheet wins; tell Matthew so the file gets fixed.

## Where the brand lives

| What | Where | Note |
|---|---|---|
| The Chalette Design System | https://claude.ai/artifact/Eruzdf8JqM5UWsmkSuzjqi | The one editable copy of the brand: colours and type in `tokens.json`, names, voice, lines and claims in its README, twelve components. If you cannot open or edit it, ask Matthew for access (still on his list on 2026-10-25) |
| The brand skill | Plugin marketplace `ChaletteHQ/chalette-brand`, skill `chalette-brand` | Makes a chat read the design system first and change it cleanly, with your name and a note on every edit. Access to that repo also comes from Matthew |
| The website | `chaletteholdings/chalette-website` | Still on the old look. Isabella proposes by pull request; Matthew merges |
| The July positioning (version 4) | Matthew's workspace | History for wording. Its thesis has not been re-ruled. Do not draft new material from it |

## The look

| Item | Status | Detail |
|---|---|---|
| The design system above is the only brand source | Ruled 2026-10-24 | No personal copies; edits happen in the one artifact |
| The June brand kit (brass "C", Cormorant Garamond, cream pages, the numbered index bars) | Retired 2026-10-24 | Older decks and one-pagers still carry it. Rebuild before reuse |
| The logo | Ruled 2026-10-24 | The lowercase word "chalette" set in Libre Caslon Text, ending in an olive tick. No drawn version is planned |
| Avatar and favicon | Ruled 2026-10-24 | Ink disc with "c" and tick from 32px up; the tick alone at 16px |
| Olive text for labels in documents | Ruled 2026-10-24 | The brighter olive is for marks only |
| The dark (ink) stage | Ruled 2026-10-24 | Web bands, feed posts, and a deck's cover and closing slide. Everything else is white |
| Fonts outside the web | Ruled 2026-10-24 | PDFs embed the fonts. Word files are not a brand surface |
| Document signature | Ruled 2026-10-24 | "chalette \| Command Room" in the header or footer |
| Website restyle (colours, layout, the product page) | Open | Isabella's first read: the colours feel dull and the product page reads like a document. Timing and direction are Matthew's |

## Names and words

| Item | Status | Detail |
|---|---|---|
| Chalette is the company, Command Room the product | Working | "Command Room" takes no article. "chalette" in lowercase only in the logo |
| "Chalette Holdings" in public | Open | The design system says never. It collides with the web address, the LinkedIn page name and the legal name on invoices. What counts as "public" is Matthew's call |
| "Operator" | Open | The July positioning is built on it ("AI by operators, for operators"); the design system forbids it and says "business people" or "owners". Until ruled, leave it out of anything new |
| "Your Chalette advisor" for the person | Working | Command Room is the product doing the work; the advisor is the person beside the owner |
| Coaching language | Open | The design system says never use executive-coach or board-meeting framing; a service tier is currently called "AI Coaching". One ruling settles both |

## The message

| Item | Status | Detail |
|---|---|---|
| The headline | Open | Two in circulation. July: "An operating system, built around you and your business." Design system, used on the October sales pages: "AI for people who don't have time to learn to code. Consulting for people who are tired of consultants." Drafts use the second |
| The one-liner (what Chalette is, for a cold introduction) | Open | The hardest message, by everyone's account. Candidate Isabella preferred on 2026-10-20: "Chalette builds a system around the way you already run your business so you don't have to be the person everything has to go through." Another candidate uses "operator", which is itself open |
| The problem framing | Working | Owners know they need an AI strategy and nobody can tell them what one is; AI gets pointed at the cheap work instead of the expensive people at the top. Lines in the design system README ("Everyone wants an AI strategy...") |
| "Conductor" ("From doing it all, to conducting it all") | Open | Locked in July, not carried into the design system. Do not use in public until Matthew says |
| The guarantee | Working | Exactly "We guarantee value." If the refund comes up: "If you don't see it, we refund you." |
| Old guarantee wordings | Retired | "Real value by the second session or your money back", any count of sessions, "or we keep working free", and "never a refund" |
| Prices | Ruled | Never in public material. Pricing is for the conversation |
| Data and security | Working | "We don't have servers. We don't hold your data." Never "on our servers". A full written security answer does not exist yet; do not promise more than this line |
| What it is built on | Working | "Command Room runs on Claude, Anthropic's AI, in your own account." Never suggest Chalette made the model |
| Against ChatGPT and other chat tools | Working | Be fair: they remember bits of past conversations. The difference is the structured record, every fact with its source, the scheduled work and the advisor |

## Proof, numbers and stories

| Item | Status | Detail |
|---|---|---|
| The MIT "95% see no P&L impact" study | Working | Contested, so it never travels alone. Pair it with S&P Global (42% of companies abandoned AI initiatives before production) or Zapier (84% had a pilot that never shipped) |
| "McKinsey: 80% plus see no bottom-line movement" and "BCG: 74% cannot scale the value" | Retired | The first was never McKinsey's; the second has no source. Never reintroduce them |
| McKinsey's March 2025 report (80% plus see no enterprise-level profit impact) | Open | A real figure, but a different claim from the retired one. Matthew's call whether it is used |
| Client quotes and stories | Ruled | Real, approved by the client in writing, attributed by role and industry only. Illustrations are invented and stay consistent within a piece |
| Client names, logos or figures in a deck | Open, case by case | Needs Matthew's OK and the client's written OK each time. Never reuse a story or a number from an older deck without asking Matthew: several were found wrong and retired |
| Spanish material | Working | Same rules as English. Translations of the lines are drafts until Matthew reads them |

## How a row gets decided

1. Pick an Open or Working row. Draft the options: in the design system, on a page, or in a chat with Matthew.
2. Matthew rules.
3. The same day, in one pull request on this repo: change the row's status, add the date and his words. If the wording changed, the design system README changes too, through the brand skill.
4. Name what else still carries the old version (the website, a deck, a template) in the row's detail, so it gets fixed at the source and not only in the copy you are holding.

A decision that lives only in a chat does not count. Nothing goes public on a row that is not Ruled or Working.

## Waiting on Matthew (as of 2026-10-26)

- Rule on five rows: "Operator", the headline, coaching language, "Chalette Holdings" in public, and confirm the guarantee wording.
- Edit access for Isabella and Erick on the design system artifact, and read access to the `chalette-brand` marketplace.
- Website restyle: when, and who leads.
