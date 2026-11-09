# 0001: One vendor-neutral core with renderers

**Status:** accepted, 2026-11-08

## Context

Two teammates use Claude Code and one uses Codex. Skills share an open standard, but subagents, hooks and MCP configuration differ.

## Decision

`core/` is the only place definitions are edited. A renderer writes each vendor's format into the game repository as git-ignored files.

## Consequences

A change reaches every tool at once. Vendor-only features are used only where the renderer can degrade them safely.
