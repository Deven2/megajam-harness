# 2026 Epic AI MegaJam: Rules Digest

Paraphrased digest for agents and teammates. **The Official Rules prevail over this file.**

- Official Rules version digested: last updated **2026-11-05** (16 pages, EN).
- Retrieved: 2026-11-08.
- Before submitting, re-read the Change Log on the last page of the Official Rules.

## Sources

- Official Rules (EN): https://epicgames.ent.box.com/s/a7xcgl07fqoieeb99sjtd3juhj4agc4z
- Jam page and submission: https://itch.io/jam/2026-epic-ai-megajam
- Announcement: https://www.unrealengine.com/news/2026-epic-ai-megajam
- Unreal MCP docs: https://dev.epicgames.com/documentation/unreal-engine/unreal-mcp-in-unreal-editor?lang=en-US
- Packaging docs: https://dev.epicgames.com/documentation/en-us/unreal-engine/packaging-your-project

Section numbers below (§) refer to the Official Rules.

## Key dates

November in the US is standard time: ET = UTC-5, PT = UTC-8.

| Event | Official time | UTC |
| --- | --- | --- |
| Kickoff livestream and theme reveal | Nov 11, 11:00 AM PST / 2:00 PM EST | Nov 11, 19:00 |
| Contest Period starts (§4) | Nov 12, 12:00 AM ET | Nov 12, 05:00 |
| Daily livestreams | 11:00 AM PST / 2:00 PM EST | 19:00 each day |
| Contest Period ends, submission deadline (§4) | Nov 15, 8:59 PM ET / 5:59 PM PST | Nov 16, 01:59 |
| Potential winners notified (§14) | On or about Jan 29, 2027 | 72 h to respond |

Total build window: 92 h 59 min. Late submissions are disqualified.

## Eligibility (§5)

- Team of 1 to 5 people, unlimited AI agents.
- Every entrant: 18+, legal resident of an Eligible Jurisdiction, active Epic Account that is not a Cabined Account.
- Restricted Jurisdictions: Iran, Iraq, North Korea, Somalia, Sudan, Syria, and the Crimea, Donetsk and Luhansk regions.
- Residents of Brazil may participate but cannot receive cash prizes.
- Excluded: employees, officers and directors of Epic; regular contractors of Epic; the same roles at prize providers and Partners; their immediate family and household members.
- Partners named in the announcement include Anthropic, Google, Meshy, OpenAI and SpaceXSI (list is not exhaustive).
- Student category: every team member must be currently enrolled at a higher-education institution.

## Submission requirements, Unreal Engine track (§1, §7, itch page)

- One submission per team. Choose UE or UEFN, not both.
- Packaged for Windows as a **development build** (itch page), playable on Windows 10 or 11, macOS, Android or iOS. Unpackaged projects are rejected.
- Zip named `TeamName_GameName`, under 1 GB for browser upload. Use butler or Blendo Itch Uploader for larger builds.
- Upload to the team's own itch.io account, then submit to the jam.
- Entry must include: team name, each member's full name and Epic-linked email, the designated Team Owner, game name, gameplay video link, list of sourced assets.
- Gameplay video: 30 to 60 seconds, 1920x1080 or higher.
- Optional dev log link, mandatory for the Glass Box prize and submitted with the entry during the Contest Period (§10).
- All content and entry information in English, including in-game text, audio and video (§7i).
- Must not require additional software to run (§7f).
- Must demonstrate the Contest Theme (§7g).
- Must not be an obvious extension of an official tutorial, and custom gameplay must exceed Epic's starter templates (§7d, §7e).
- Must be directly accessible by the Sponsor (§7b).

## Pre-jam boundary (§7h, itch page)

Allowed before Nov 12: AI tools, agent configurations, MCP settings, prompt libraries, scripts.

Must be created during the Contest Period: gameplay, levels, art assets (except noted sourced assets), all other game content.

Anything made earlier must be declared. The Sponsor may request these materials or the version control history to verify compliance.

## AI use and IP (§7a, §9, §15, §17)

- AI use is optional. The extent of disclosed AI use is context only and does not change the score by itself.
- AI-generated content is allowed and is **not** a sourced asset, so it is judged as the team's own work.
- Sourced assets must be noted on submission, are not reviewed or scored, and the team must hold all needed clearances.
- Entrants warrant they hold all rights in the submission. Possible copyright infringement leads to disqualification.
- No trademarks or logos, except the Unreal Engine logo under Epic's branding guidelines.
- The entry itself must be submitted by a person, never by an AI agent or automated means.
- The team keeps ownership and grants Epic a broad license to use the submission to publicize the contest.

## Content restrictions (§8)

Teen-appropriate (13+). No disparagement of Epic, people or products. No infringing, hateful, obscene or illegal material, no nudity, no animal cruelty.

## Judging (§9)

Seven criteria, up to 5 points each: Ambition and Innovation, Use of Theme, Fun Factor, Gameplay, Visuals, Level Design, Audio. Ties are re-scored with double weight on Fun Factor.

## Prizes (§10, §11, §13)

| Category | Amount (USD) |
| --- | --- |
| Best Overall: Unreal Engine | 7,500 / 5,000 / 2,500 |
| Best Student Project (UE or UEFN) | 7,500 / 5,000 / 2,500 |
| Best Team (2+ members) | 5,000 |
| Render Royalty (visuals) | 2,500 |
| Glass Box (dev log) | 2,500 |
| Pocket Powerhouse (mobile, UE winner) | 2,500 |
| Solo Driver | 2,500 |

- At most one main prize and one modifier prize per submission.
- Prizes go to the Team Owner through Hyperwallet. The Team Owner handles the split and the tax form (W-9, W-8BEN or W-8BENE).
- Development Continuation Grants (up to 50,000 / 25,000 / 10,000 for UE) are invitation-only, separate from prizes, and not guaranteed.

## Constraints agents must enforce

Team interpretations are marked. When in doubt, take the conservative reading and ask a human.

| ID | Constraint | Basis |
| --- | --- | --- |
| C-01 | No gameplay, levels or art in the game repo before contest start. The repo holds a blank project, config, CI and docs only. | §7h, team interpretation of "blank" |
| C-02 | Tag the pre-jam state as `pre-jam-baseline` and keep a declaration file listing everything made earlier. | §7h, itch page |
| C-03 | Never rewrite shared history. No force-push. Use merge commits, not squash. | §7h, team interpretation |
| C-04 | All game content, commits, code, docs and entry data in English. | §7i, team choice |
| C-05 | Agents prepare the package and checklist. A person submits the entry. | §17 |
| C-06 | Log every sourced asset with origin, license and path in a ledger. | §1, §15c |
| C-07 | Confirm the license of any AI-generation provider before using its output. | §15a, team interpretation |
| C-08 | No runtime dependency on extra software. No API keys inside builds. | §7f, security |
| C-09 | Release config is Win64 Development, zip named `TeamName_GameName`. | itch page |
| C-10 | Teen rating, no third-party logos, nothing reusing tutorial content. | §7d, §8, §15d |
| C-11 | Dev log is published and linked before the deadline. | §10 |
| C-12 | Content freeze and packaging finish well before the deadline. | Team rule |

## Open items

- Contest Theme: revealed at kickoff on Nov 11.
- AI tool credits from partners: claiming details not yet published as of retrieval.
- Engine version: the rules do not mandate one. The team targets UE 5.8.

## Source differences to keep in mind

- The rules say the theme arrives at the start of the Contest Period. The itch page and announcement schedule the reveal at the Nov 11 kickoff.
- "Development build" appears on the itch page. The rules only say packaged for Windows. Follow the stricter itch wording.
- The rules cite a different Box URL as the canonical location for rule changes than the link shared with the team. Check both before submitting.
