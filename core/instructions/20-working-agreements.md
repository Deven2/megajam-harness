## How work flows

- `{{h}} ship` is the only write path to shared branches. Direct `git commit`, `git push` and merges are blocked.
- Branches: `feature/*` from `{{integration}}`, `release/x.y.z` into `{{production}}`, `hotfix/*` from `{{production}}`.
- Commits use Conventional Commits in English: `feat(player): add dash`. Extra types: `art`, `audio`, `level`.
- `.uasset` and `.umap` cannot be merged. Warn before two people touch the same one.
- Keep logic in C++ and keep Blueprints thin. Binary assets are invisible to agents.
- Conventions live in `docs/`. Read the relevant page before guessing: naming, asset pipeline, C++, CI.
- If a tool call is blocked, read the reason and follow it. Never look for a workaround.

## During the jam

- The harness is frozen from the jam start. Do not edit it or propose changes. If it gets in the way, find a simple workaround and note the idea for the devlog. Only a blocker with no simple workaround justifies `{{h}} contribute --blocker "<what it blocks>"`, and a person decides that.
- Broken CI must never stop the game. If the checks never start or fail for a reason unrelated to the change, such as an outage, a runner offline or a timeout, a person can approve `{{h}} ship --ci-down "<reason>"`. It merges without waiting and leaves the reason on the pull request. Never use it to get past a check that found a real problem.
- The team updates the Trello board by hand. Use the board only when a person asks.
