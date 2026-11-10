---
name: perf-check
description: Measure frame rate or check assets and Blueprints against the performance budget (60 fps at 1080p). Use when the game feels slow, stutters or drops frames, before a release, or when someone asks whether assets, meshes, textures or Blueprints fit the budget. Any language.
---

# Performance check

The budget is in the game repository's `docs/performance-budget.md`: a 95th percentile frame time of at most 16.67 ms at 1920x1080 in the packaged build, plus limits for textures, meshes, materials and Blueprints.

Delegate to the `ue-test-runner` subagent, with the editor closed:

- Assets and Blueprints: `powershell -File Build/Scripts/Validate-Assets.ps1`
- Frame time: `powershell -File Build/Scripts/Test-Performance.ps1 -BuildDir <packaged Windows folder>`. The latest builds are in `C:\MegaJamBuilds\<sha>\Archive\Windows` on the runner host. Package first with `Build/Scripts/Package-Game.ps1` if there is none.

Explain the result in plain words: which resolution failed, and whether the game thread, the render thread or the GPU is the slowest. Then suggest the matching fix from the "Fixing a failure" section of the budget. For an asset error, name the asset and the limit it breaks.

Before the jam starts, there is no game content to measure. The checks still run on the blank project.
