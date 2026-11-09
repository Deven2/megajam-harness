# Codex subagents cannot narrow their own permissions

- **Date:** 2026-11-08
- **Area:** subagent
- **Vendor:** codex

## Situation

Codex custom agents inherit sandbox, approval policy and MCP servers from the parent session. The agent file cannot override them. Claude Code subagents can set their own tools, MCP servers and permission mode.

## What went wrong

A design that placed permissions inside subagents would have protected only half of the team.

## What worked

Every write goes through `h` commands. A PreToolUse guard shared by both vendors blocks the direct alternatives, and git hooks repeat the rules.

## Rule for next time

Put a rule in the guard or in an `h` command when it must hold for everyone. Instructions are advice.
