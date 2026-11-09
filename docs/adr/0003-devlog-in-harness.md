# 0003: The devlog lives in this repository

**Status:** accepted, 2026-11-08

## Context

The Glass Box prize needs a dev log link that judges can open. The team chose to host it on GitHub. The game repository must stay private: it holds licensed assets, and a self-hosted runner is unsafe on a public repository. GitHub Pages is not available on private repositories in the Free plan.

## Decision

The devlog is Markdown in `devlog/` here. This repository holds no game content or licensed assets, so it can be made public. The link is `https://github.com/Deven2/megajam-harness/tree/dev/devlog`.

## Consequences

This repository must be public before the entry is submitted, and the submission check verifies that the link opens. The devlog also serves as documentation of how the harness was used.
