---
name: trello-sync
description: Read or update the team board (Trello, also called the board or task list). Use right away, without searching files, when someone starts a task, asks to note something on the board, asks what is pending or who does what, or after work ships. Any language.
---

# Trello sync

Delegate to the `trello-scribe` subagent. Give it the task in plain words, the person's name and the PR link if there is one.

Board: `MegaJam`. Lists: `Backlog`, `Doing`, `Review`, `Done`.

- Starting a task moves its card to `Doing` and assigns the person.
- Shipped work moves to `Done` with the PR link as a comment.
- Work that needs a teammate's decision moves to `Review`.
- If no card matches, create one. Card titles are short and in English.

The Trello connector cannot permanently delete cards, only archive them.
