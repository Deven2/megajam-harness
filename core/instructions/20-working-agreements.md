## How work flows

- `{{h}} ship` is the only write path to shared branches. Direct `git commit`, `git push` and merges are blocked.
- Branches: `feature/*` from `{{integration}}`, `release/x.y.z` into `{{production}}`, `hotfix/*` from `{{production}}`.
- Commits use Conventional Commits in English: `feat(player): add dash`. Extra types: `art`, `audio`, `level`.
- `.uasset` and `.umap` cannot be merged. Warn before two people touch the same one.
- Keep logic in C++ and keep Blueprints thin. Binary assets are invisible to agents.
- Conventions live in `docs/`. Read the relevant page before guessing: naming, asset pipeline, C++, CI.
- If a tool call is blocked, read the reason and follow it. Never look for a workaround.
