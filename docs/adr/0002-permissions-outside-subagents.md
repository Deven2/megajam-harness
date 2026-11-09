# 0002: Permissions live outside subagents

**Status:** accepted, 2026-11-08

## Context

Claude Code subagents can set their own tools, MCP servers and permission mode. Codex custom agents inherit sandbox, approvals and MCP servers from the parent and cannot override them. Codex hook input does not identify which agent made a tool call.

## Decision

Rules that must hold for everyone live in a shared guard hook, in `h` commands and in git hooks. Per-subagent tool limits are added on Claude Code as an extra layer.

## Consequences

Raw git writes are blocked for all agents, which forces one write path. Codex subagents have broader tool access than their Claude counterparts.
