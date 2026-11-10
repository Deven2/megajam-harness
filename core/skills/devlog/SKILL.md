---
name: devlog
description: Write or publish a devlog entry about how the game is being built. Use at the end of a work day, after a milestone, or when someone mentions the devlog, progress notes or the Glass Box prize.
---

# Devlog

The devlog competes for the Glass Box prize and must be linked in the submission before the deadline. It lives in the harness repository because that repository becomes public.

Each entry has two parts: a personal comment from one teammate, then a narrative summary of what changed since the previous entry.

1. Run `{{h}} devlog collect` for commits and the notes teammates left. During the jam, also read the latest rows of the game's `docs/design/scorecard.md`, where the team scores the game against the judging criteria.
2. Ask the person for their comment: how this stretch went for them, in their own words and in any language. Ask their name if you do not know it. If they do not want to write one, ask which teammate will. An entry needs a comment.
3. Delegate to `devlog-writer` with the data, the comment, the scorecard rows and the author's name. It saves the draft to `.harness/devlog-draft.md`.
4. Show the author their comment exactly as it will be published, with the list of edits, plus the title and a two-line summary. Publish only after the author agrees.
5. Run `{{h}} devlog publish --title "<title>"`. Add `--media <file>` for screenshots.

Entries before the jam tell how the harness was built. From the jam start they tell how the game is being made, and mention the harness only where it changed how we worked.

Aim for one entry per jam day and one final entry. Rotate the author so each teammate writes at least one comment.
