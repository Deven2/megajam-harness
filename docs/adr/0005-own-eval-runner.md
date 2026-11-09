# 0005: Our own eval runner

**Status:** accepted, 2026-11-08

## Context

`claude plugin eval` offers graders, MCP mocks and cost ceilings, but it runs only on Claude Code. Contributions must be testable by every teammate.

## Decision

A small runner uses the same case files for both vendors, and grades which skill or subagent ran.

## Consequences

Coverage is limited to routing, which is the most common failure in natural-language use. Output quality is not graded automatically.
