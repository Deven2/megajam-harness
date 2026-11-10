---
name: harness-contribute
description: Improve the team's AI harness itself, such as a skill, subagent, hook, rule or MCP setting. Use when someone wants the agents to behave differently from now on, or reports a repeated mistake an instruction could prevent.
---

# Harness contribution

From the jam start the harness is frozen. Do not change it. Help the person find a workaround and note the idea for the devlog instead. Only a blocker with no simple workaround justifies a change, the person decides, and the command needs `--blocker "<what it blocks>"`.

Delegate to the `harness-curator` subagent. Give it the problem and a concrete example of what went wrong.

The change is made in `core/` of the harness clone at `{{harness_path}}`, never in the generated files here. The contribution then runs validation, unit tests and the evals for what changed before it can merge:

```
{{h}} contribute --type <type> --scope <scope> --summary "<summary>"
```

Run it with the harness clone as the current directory. After it merges, each teammate gets the update prompt in their next session.
