---
name: next-task
description: Tell a teammate what is pending and what they should or could work on next, from the game's shared task list. Use when someone asks what is pending, what to do now, what they can pick up, what others are doing, or wants to claim, start, finish or add a task. Any language.
---

# Next task

The team works asynchronously. The shared to-do list is `docs/design/tasks.md` in the game repository. It is the source of truth for agents; the Trello board is updated by hand.

## Answer "what is pending" or "what should I work on"

1. Find who is asking: match the first name in `git config user.name` to a `[[team]]` entry in `harness.toml`. If it does not match, ask.
2. Get the latest state: `git pull --ff-only origin {{integration}}` when the working tree is clean. If it is not clean, read what is there and say the list may be out of date.
3. Read `docs/design/tasks.md`. Also check, without changing anything:
   - `docs/design/game-brief.md`, for the plan of the current day.
   - Open pull requests (`gh pr list`) and file locks (`git lfs locks`), so you do not suggest work someone is already doing.
4. Answer briefly, in the person's language, in this order:
   - What they have in progress (`doing`).
   - Their next task: their own `todo` rows for today whose `Needs` are `done`, highest in the list first.
   - Tasks with owner `anyone` they could take, matched to their duties in `harness.toml`.
   - What is `blocked` waiting on them, or on someone else, and who.
   - If everything for today is done, the next day's first task.
5. Offer to start one. Do not start without a yes.

## Claim, finish or add a task

Changes to the list travel through `{{h}} ship`, so the others see them after they pull.

- **Claim:** set the row's `Owner` to the person and `Status` to `doing`, then ship it alone right away with `{{h}} ship --type docs --scope tasks --summary "claim T07"`. A claim that waits for the work to be finished is invisible to the others.
- **Finish:** set `Status` to `done` in the same ship as the work.
- **Block:** set `Status` to `blocked` and write what it waits for in `Needs`.
- **Add:** append a row with the next free ID. Keep the task small enough for one person and one sitting, and write `Done when` as something someone else can check.

Never change another person's `doing` row without their yes. If a task looks abandoned, tell the person who asked and suggest they message its owner.
