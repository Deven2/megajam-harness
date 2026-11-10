# Architecture

## One source, two outputs

`core/` is vendor-neutral. `h render` turns it into what each tool reads, inside the game repository:

| `core/` | Claude Code output | Codex output |
| --- | --- | --- |
| `instructions/*.md` | `CLAUDE.md` | `AGENTS.md` |
| `skills/<name>/` | `.claude/skills/<name>/` | `.agents/skills/<name>/` |
| `agents/<name>.md` | `.claude/agents/<name>.md` | `.codex/agents/<name>.toml` |
| `hooks/hooks.toml` | `.claude/settings.json` | `.codex/hooks.json` |
| `mcp/servers.toml` | `.mcp.json` and inline in subagents | `.codex/config.toml` |

Generated files are git-ignored in the game repository, so each person gets the output for their own tool and paths.

## Layers of control

| Layer | Examples | Costs model tokens? | Can be ignored by an agent? |
| --- | --- | --- | --- |
| Instructions and skills | Conventions, delegation | Yes | Yes |
| Guard hook | Blocks raw pushes, secrets, pre-jam content | No | No |
| `h` commands | `ship`, `ledger`, `devlog` | No | Only path to shared branches |
| Git hooks | Commit format, names, history | No | Not without `--no-verify`, which the guard blocks |
| CI | `pr-fast` | No | No |

A rule that must always hold belongs in the lower layers.

## Workspace

```
C:\Repos\MegaJam\
  megajam-harness\   clone of this repository
  megajam-game\      clone of the game repository, where the AI tool runs
```

Each folder is named after its repository, which is also what `git clone` uses by default.

The game folder holds a small `.harness/` directory with shims pointing back at the harness clone.

## Session lifecycle

1. `SessionStart` runs `h hook session-start`: jam phase, countdown, stale harness, LFS usage.
2. Each tool call passes through `h hook guard`.
3. Blender imports and generations pass through `h hook ledger`.
4. Finished work leaves through `h ship`.

## Branches

The same model as the game repository. Installed copies follow `dev`, whose merges have passed validation and evals. Devlog entries go straight to `dev` through `h devlog publish`.
