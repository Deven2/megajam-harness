---
name: ue-feature
description: Implement or change gameplay in Unreal C++. Use for new mechanics, classes, components, systems or bug fixes in the game code.
---

# Unreal feature

1. Check the SessionStart phase. Before the jam starts, gameplay code is not allowed: stop and say so.
2. State the smallest version that is playable. Scope small, then polish.
3. Delegate implementation to `ue-cpp-dev` with the goal, the affected classes and what done looks like.
4. Use `ue-architect` only when a person asks for design help, or after two failed attempts at the same bug.
5. Delegate verification to `ue-test-runner` through the ue-build-test skill.
6. Use the ship skill once it builds and the tests pass.

Prefer C++ for logic and expose only tuning values and asset references to thin Blueprints.
