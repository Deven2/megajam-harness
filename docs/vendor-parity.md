# Vendor parity

Verified against the official documentation on 2026-11-08.

| Feature | Claude Code | Codex | Harness approach |
| --- | --- | --- | --- |
| Instructions | `CLAUDE.md` | `AGENTS.md` | One source, rendered per vendor |
| Skills | `.claude/skills/` | `.agents/skills/` | Same `SKILL.md` format |
| Subagent file | Markdown with YAML | TOML | Rendered per vendor |
| Subagent model | Per agent | Per agent | Tier mapped in `vendors/` |
| Subagent tools | Per agent | `features.shell_tool` and skill toggles only | Guard and `h` commands |
| Subagent MCP scope | Per agent, inline | Inherited from the session | Inline on Claude, shared on Codex |
| Subagent sandbox | `permissionMode` per agent | Inherited, cannot be overridden | Guard and `h` commands |
| Hooks | `.claude/settings.json` | `.codex/hooks.json` | Same scripts, exit code 2 blocks |
| Hook trust | Project trust | Review with `/hooks`, repeated when hooks change | Documented at install |
| Hook shell on Windows | Git Bash, or `shell` field | `commandWindows` | Rendered per vendor |
| MCP over HTTP | `.mcp.json` | `[mcp_servers]` | Rendered per vendor |
| GitHub token | `headersHelper` runs `gh auth token` | `bearer_token_env_var` | Rendered per vendor |

## Tier mapping

| Tier | Claude Code | Codex |
| --- | --- | --- |
| fast | `haiku` | `gpt-6-luna` |
| standard | `sonnet` | `gpt-6.1-sol` |
| deep | `opus` | `gpt-6.1-sol`, high effort |

## Not verified on a real machine

Check these during Pablo's first install:

- The Windows shell Codex uses for `commandWindows`. Paths with spaces are the risk, so the doctor fails on them for Codex.
- That `PreToolUse` fires for Codex subagent tool calls. The documentation does not say so.
- That repository-scoped custom agents can be invoked by name. An issue from March 2026 reported a problem in tool-backed sessions.
- The `/mcp` sign-in flow for Trello in Codex.
