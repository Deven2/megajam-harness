# Trello MCP cannot run in CI

- **Date:** 2026-11-08
- **Area:** trello-mcp
- **Vendor:** both

## Situation

The official Trello MCP server accepts only OAuth through a browser consent screen. Atlassian's documentation says API tokens are not supported for MCP connections.

## What went wrong

Nothing yet. This was found while designing the harness.

## What worked

Trello updates happen from each person's interactive session, right after `h ship`.

## Rule for next time

If CI ever has to touch Trello, use the REST API with a key and token, stored as a GitHub secret.
