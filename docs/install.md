# Install

Open a clone of this repository in Claude Code or Codex and ask it to install the harness. `AGENTS.md` tells the agent what to do. The command it runs:

```
python tools/h.py install --vendor <claude|codex> --game <path> --role <dev|art> --clone
```

## What it does

1. Clones the game repository if it is missing.
2. Sets local git options: hooks path, long paths, fast-forward pulls, writable lockable files. Git signs in through the GitHub CLI, and commits use your private GitHub address (`<id>+<login>@users.noreply.github.com`), because this repository becomes public before submission.
3. On `dev` machines, excludes `Art/Source/**` from LFS downloads to save the bandwidth quota.
4. Writes the `.harness/` shims.
5. Generates the configuration for your tool.
6. On Codex, saves your GitHub token in the `GITHUB_PAT` user variable. Claude Code reads it on demand through `gh`.
7. Runs the doctor and prints the remaining steps.

## Doctor

```
.harness/h doctor --live
```

Checks Python, Git, Git LFS, GitHub CLI and sign-in, uv, your AI tool, Unreal Engine 5.8, Visual Studio, Blender, repository paths, free disk, git hooks, LFS usage and the MCP ports.

## Updates

Each session compares your clone with `origin/dev`. If it is behind, the agent offers the harness-update skill, which runs `h update`. Restart the session afterward, because skills and agents load at startup.

## Switching tools

Run install again with the other `--vendor`. Generated files for the previous tool are removed.
