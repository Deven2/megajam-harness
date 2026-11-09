# Unreal MCP handles one call at a time

- **Date:** 2026-11-08
- **Area:** unreal-mcp
- **Vendor:** both

## Situation

Epic's documentation for Unreal MCP in UE 5.8 states that tool calls run serially on the game thread and that clients should not send overlapping calls.

## What went wrong

Nothing yet. This was found while designing the harness.

## What worked

Only `ue-editor-operator` is given the server, and the instructions forbid running two at once.

## Rule for next time

Parallel subagents are fine for code and research. Work inside the editor is a single queue.
