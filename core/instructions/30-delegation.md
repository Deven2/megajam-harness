## Delegation and cost

Prefer the cheapest option that does the job: an `h` command, then a fast subagent, then a standard one. Usage limits are tight for part of the team.

| Work | Subagent |
| --- | --- |
| Commits, PRs, locks | `git-shipper` |
| Trello cards | `trello-scribe` |
| Builds, automation tests, log reading | `ue-test-runner` |
| Docs that follow a code change | `docs-keeper` |
| Asset naming, placement and ledger | `asset-importer` |
| C++ implementation | `ue-cpp-dev` |
| Anything inside Unreal Editor | `ue-editor-operator` |
| Anything inside Blender | `blender-operator` |
| Devlog entries | `devlog-writer` |
| Changes to the harness | `harness-curator` |
| Hard design or debugging, only when a person asks | `ue-architect` |

- Unreal MCP handles one call at a time, so run only one `ue-editor-operator` at once.
- Do not start a subagent for something a single command answers.
- Run at most two subagents in parallel.
