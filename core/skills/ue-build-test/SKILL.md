---
name: ue-build-test
description: Compile the Unreal project and run its automation tests, or explain a build or test failure. Use for build errors, failing tests, CI failures, or to confirm that code works.
---

# Build and test

Delegate to the `ue-test-runner` subagent and ask for a short summary, not the log.

Commands, from the repository root:

```
powershell -File Build/Scripts/Build-Editor.ps1
powershell -File Build/Scripts/Test-Automation.ps1
```

- Close Unreal Editor before building, or use Live Coding from inside it. New `UFUNCTION` declarations need an editor restart.
- Logs are written to `Saved/Logs` and reports to `Saved/Automation`.
- Add a test in `Source/{{codename}}Tests` when a bug could return.
