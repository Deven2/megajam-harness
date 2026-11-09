# megajam-harness

The AI harness of a three-person team in the 2026 Epic AI MegaJam. It works with Claude Code and Codex.

Speak with each person in the language they use. Everything saved in this repository is in English.

## If the user asks to install or set up the harness

Do these steps in order. Run the commands yourself and explain results in plain words, because the person may not be a developer.

1. Work out which AI tool is running here: Claude Code (`claude`) or Codex (`codex`). Ask if unsure.
2. Ask their role: `dev` (programming) or `art` (art and Unreal). The art role also downloads the heavy Blender sources.
3. Ask where the game should live. Recommend a short path without spaces, such as `C:\Repos\MegaJam\game`.
4. Check `python --version`. It must be 3.11 or newer. If it is missing, run `winget install astral-sh.uv` and replace `python tools/h.py` with `uv run --python 3.12 tools/h.py` below.
5. Run `python tools/h.py install --vendor <claude|codex> --game <path> --role <dev|art> --clone`.
6. Read the report. For each `FAIL` line, show its fix and offer to run it. The person must do anything that needs a browser sign-in, such as `gh auth login --scopes workflow`.
7. After fixes, run `python tools/h.py install` again with the same arguments.
8. Walk them through the next steps it printed, then tell them to open their AI tool in the game folder.

## If the user wants to change the harness

Read `docs/contributing.md`. Edit `core/` or `vendors/`, then ship with `python tools/h.py contribute`. Do not run `git commit` or `git push` directly.

## Map

- `core/`: vendor-neutral skills, subagents, hooks, MCP servers and instructions.
- `vendors/`: how `core/` maps to Claude Code and Codex.
- `tools/`: the `h` command line.
- `knowledge/`: jam rules and real cases.
- `evals/`: behavior tests run before a contribution merges.
- `devlog/`: the public devlog.
- `docs/`: how all of this works.
