---
name: devlog
description: Write or publish a devlog entry about how the game is being built. Use at the end of a work day, after a milestone, or when someone mentions the devlog, progress notes or the Glass Box prize.
---

# Devlog

The devlog competes for the Glass Box prize and must be linked in the submission before the deadline. It lives in the harness repository because that repository becomes public.

1. Run `{{h}} devlog collect` for commits and the notes teammates left.
2. Ask the person one question: what surprised you today? Skip it if they are busy.
3. Delegate to `devlog-writer` with the data and the answer. It saves the draft to `.harness/devlog-draft.md`.
4. Show the title and a two-line summary, and let the person object.
5. Run `{{h}} devlog publish --title "<title>"`. Add `--media <file>` for screenshots.

Aim for one entry per jam day and one final entry.
