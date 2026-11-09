---
name: ue-editor-task
description: Do something inside the open Unreal Editor, such as placing actors, adjusting lighting, creating material instances, building levels or inspecting the scene.
---

# Unreal Editor task

Delegate to the `ue-editor-operator` subagent. Only one may run at a time because Unreal MCP executes calls serially on the game thread.

Before delegating, make sure the editor is open with Unreal MCP running. If it is not, ask the person to open it. Setup is in `docs/getting-started.md`.

Levels are shared binary files. Warn before editing a map someone else may have open. Use One File Per Actor for new levels.

Ship the result with the ship skill, after saving in the editor.
