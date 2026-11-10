# 0006: Fixed formats for Trello cards and devlog entries

**Status:** accepted, 2026-11-10

## Context

Cards held one loose sentence, so a teammate could not tell why a task mattered or when it was done. Tasks that each of us must do on our own machine had no way to show who had finished. The devlog spoke only with the team's voice, while the Glass Box prize rewards an honest account of how the game was made.

## Decision

Every card description has three sections: `Need`, `Goal` and `Steps`. A task that each teammate does on their own gets an `Each member` checklist with one item per person, and all three of us as card members.

Every devlog entry starts with a personal comment from one teammate, requested by the agent, followed by a narrative summary of what changed since the previous entry. The agent translates the comment to English and edits it only to keep a public page professional, for example by removing profanity. The author approves the final text before it is published.

## Consequences

The Trello connector cannot add card members or assign checklist items, so a person adds the members by hand. See `knowledge/cases/trello-connector-limits.md`. Evals check that the right skill runs, not the format of what it writes, so the format depends on the instructions in `trello-scribe` and `devlog-writer`.
