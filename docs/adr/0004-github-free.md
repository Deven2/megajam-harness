# 0004: GitHub Free

**Status:** accepted, 2026-11-08

## Context

GitHub Team would add server-side rules on private repositories and more LFS. The team chose Free.

## Decision

Enforcement happens in git hooks, the guard and `pr-fast`. `h ship` waits for checks before merging. If no check starts, it leaves the pull request open.

## Consequences

Git LFS is limited to 10 GiB of storage and 10 GiB of monthly bandwidth, so the harness tracks usage and limits downloads. Upgrading remains a quick fallback if the quota runs out.
