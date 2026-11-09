# Guard and hooks

## The guard

`tools/harness/guard.py` runs before each shell command, file edit and MCP call. A blocked call returns a reason the agent can follow.

| Rule | Blocks |
| --- | --- |
| `raw-push`, `raw-commit`, `raw-merge` | Direct git writes. `h ship` is the path. |
| `no-verify`, `disable-hooks` | Skipping git hooks |
| `history-rewrite` | Rebase, hard reset, amending tags, reflog expiry |
| `destructive-git` | `git clean -f`, discarding all changes, LFS prune |
| `gh-admin` | Merging PRs, repository administration, write calls to the API |
| `secret-read`, `secret-write` | Tokens, `.env` files, environment dumps |
| `destructive-fs` | Recursive deletes of project roots |
| `binary-edit` | Editing binaries as text |
| `generated-dir` | Editing `Binaries`, `Intermediate`, `Saved`, `DerivedDataCache` |
| `rendered-file` | Editing generated harness files |
| `pre-jam-content` | Game content before the jam starts |
| `jam-submit` | Submitting the entry, or uploading to a public channel |

It parses commands instead of searching text, so `rg "git push" docs` is fine. It is a safety net for mistakes, not a security boundary, and it allows the call if it crashes.

## Git hooks

`.githooks/` applies to everyone, with or without an agent.

| Hook | Checks |
| --- | --- |
| `commit-msg` | Conventional Commits, plain ASCII |
| `pre-commit` | No direct commits to protected branches, generated folders, pre-jam content, asset names, secrets, large files outside LFS, runtime AI |
| `pre-push` | No force pushes, no direct pushes to protected branches, branch names, then LFS upload |
| `post-checkout`, `post-commit`, `post-merge` | Git LFS |

Emergency override for a person: `HARNESS_ALLOW_PROTECTED=1`. Bootstrapping a new repository: `HARNESS_BOOTSTRAP=1`.

## Rehearsing the jam phase

`HARNESS_NOW=2026-11-13T00:00:00Z` makes every tool act as if it were that moment. Use it only in a throwaway repository.
