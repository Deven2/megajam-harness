# 0007: Jam mode: frozen harness, CI fallback, a manual board

**Status:** accepted, 2026-11-10

## Context

The jam lasts four days, and every hour spent on tooling is an hour taken from the game. Debugging our own tools while working on something else has cost us time before. The CI runs on one teammate's PC and on GitHub, and either can fail. The Trello connector cannot assign people, and updating cards through an agent costs tokens and attention.

## Decision

- **Frozen harness.** From the jam start, `h contribute` and `h ship` in the harness repository refuse changes. A blocker with no simple workaround opens it with `--blocker "<what it blocks>"`, which goes into the pull request. Ideas go to the devlog instead. Devlog entries are published as usual.
- **CI fallback.** `h ship --ci-down "<reason>"` merges without waiting for checks and leaves the reason as a comment on the pull request. The local git hooks still run the same policy at commit and push. A person approves it, and it is never used against a check that found a real problem. Packages can always be built locally with `Build/Scripts/Package-Game.ps1`.
- **A manual board.** The team updates Trello by hand. Agents touch it only when asked, usually once at the end of the day.
- **Kickoff playbook.** The `kickoff` skill takes the team from the theme to a brief, owners and a scorecard against the judging criteria. Devlog entries link each decision to the criteria it serves.

## Consequences

The harness we submit is the one we built before the jam, which is the setup we declare. Problems found during the jam become devlog material and post-jam work. A merge made with `--ci-down` can hide a problem until the checks run again, so the team re-runs them on `dev` when CI is back.
