# Contributing

Any teammate can improve the harness by telling their agent what should change. The harness-contribute skill handles it.

## Rules

- Edit `core/` or `vendors/`, never generated files.
- Everything is in English.
- It must work for both Claude Code and Codex. See [vendor-parity.md](vendor-parity.md).
- Skill and subagent descriptions load in every session. The limit is 320 characters.
- Always-loaded instructions are limited to 110 lines. Skills are limited to 120 lines. Move detail into a `references/` file.
- Change a behavior, change or add an eval.

## Adding a skill

Create `core/skills/<name>/SKILL.md` with `name` and `description` front matter. Write the description around what a person would say, in any language. Use `{{h}}` for the harness command.

## Adding a subagent

Create `core/agents/<name>.md` with TOML front matter between `+++` lines:

```
+++
name = "my-agent"
description = "What it does and when to use it."
tier = "fast"            # fast, standard or deep
effort = "low"           # low, medium or high
capabilities = ["read"]  # read, edit, shell, web
mcp = ["trello"]         # optional
max_turns = 10
+++
```

Default to `fast`. Move up only if an eval shows that the cheaper tier fails.

## Adding a hard rule

Put it in `tools/harness/guard.py` for agents and `.githooks/impl/policy.py` for git, and add a test for each.

## Shipping

From the harness folder:

```
python tools/h.py validate
python tools/h.py contribute --type feat --scope skills --summary "teach ship about X"
```

`contribute` runs validation, unit tests and the evals for what changed, then opens and merges the pull request.

## Regenerating the catalog

`python tools/h.py catalog` rewrites `docs/catalog.md`. Validation fails if it is stale.
