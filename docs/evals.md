# Evals

Evals check that a natural request reaches the right skill. They build a temporary workspace with your tool's generated files, send the prompt headless with the fast model, and inspect which skill or subagent ran. Shell, edit and MCP tools are unavailable, so nothing real is touched.

## Running

```
python tools/h.py eval --vendor claude --cases changed
python tools/h.py eval --vendor codex --cases all
python tools/h.py eval --vendor claude --cases ship-spanish-artist
```

`changed` runs only the cases whose skill or subagent differs from `origin/dev`. Evals spend your own plan's usage, so `contribute` runs just those.

## Writing a case

Add `evals/cases/<name>.toml`:

```toml
prompt = "ya termine el modelo del barril, subilo al repo"
expect_skill = "ship"
forbid_skills = ["release"]
max_turns = 2
```

Other fields: `expect_agent`, `expect_no_skill`. Prompts may be in any language, because people will talk to the agents in any language.

## Why not `claude plugin eval`

It has richer graders and MCP mocks, but it only runs on Claude Code. Pablo uses Codex and needs to run the same cases before contributing.

## Levels of checking

| Check | Where | Cost |
| --- | --- | --- |
| `h validate` | Locally and in CI | Free |
| Unit and flow tests | Locally and in CI | Free |
| Evals | Locally | Plan usage |
