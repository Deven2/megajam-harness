# The Trello connector cannot add card members or assign checklist items

- **Date:** 2026-11-10
- **Area:** trello-mcp
- **Vendor:** both

## Situation

Cards for tasks that each teammate does on their own needed all three of us as members, plus one checklist item per person.

## What went wrong

The connector has no action to add a member to a card. Adding a checklist item with a member returned `"due"/"memberId" are not enabled`.

## What worked

Creating the `Each member` checklist with one item named after each teammate, and asking a person to add the card members in Trello.

## Rule for next time

Never promise to assign people through the connector. Name the members to add and let a person do it. A teammate must also join the workspace before anyone can add them to a card.
