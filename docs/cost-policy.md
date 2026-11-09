# Cost policy

Two teammates are on Claude Pro, which has a five-hour session limit and a weekly limit shared with chat and desktop use. One teammate is on ChatGPT Pro. Four days of intense work will reach those limits unless usage is deliberate.

## Order of preference

1. An `h` command or a hook. No model cost.
2. A `fast` subagent, for mechanical work.
3. A `standard` subagent, for real implementation.
4. A `deep` subagent, only when a person asks.

## Defaults

- Claude Code's main session runs on `sonnet`, set by the harness.
- Subagents cannot spawn more subagents.
- At most two subagents run in parallel.
- `ue-test-runner` reports summaries so logs never enter the main context.
- MCP tools for Unreal and Blender live only inside their subagents on Claude Code.

## Habits

- Start a new session between unrelated tasks.
- Give the agent paths and class names, not "look around".
- Do not ask for a review of something that compiled and passed tests.
- Plan the expensive work for when your five-hour window has just reset.
- Split heavy implementation among the three accounts instead of exhausting one.

## When limits run out

Claude Pro can enable usage credits to continue at pay-as-you-go rates, up to a limit you set. Partner credits for the jam may also appear: check the itch.io page before kickoff.
