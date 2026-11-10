# Building a jumping character through Unreal MCP

- **Date:** 2026-11-10
- **Area:** unreal-mcp
- **Vendor:** both

## Situation

Before the jam, in a throwaway project outside the game repository, an agent built a Character Blueprint that jumps with the space bar, placed it with a camera and started Play In Editor. It used only Unreal MCP tools, with no manual editor work.

## What went wrong

- The server never started on one machine: port 8000, the plugin default, was taken by another program. A new project also has the plugin off until it is enabled in the `.uproject`.
- `write_graph_dsl` accepts only `event` or `fn` at the top level, so a keyboard event such as `Input|KeyboardEvents|SpaceBar` could not be written with it.
- `set_properties` failed when `values` was an object: it expects a JSON string. `get_properties` takes `instance` and `properties`.
- `add_to_scene_from_class` with `snap_to_ground` left the actor at its requested height.
- `SlateInspectorToolset.PressKey` returned success but the character did not jump: simulated keys reach the focused Slate widget, not reliably the game.
- `CaptureViewport` rejected a call without `captureTransform`.
- In the DSL, a positional argument on a node with a `self` pin went into `self`: `(Pawn|Input|AddControllerYawInput dx)` failed to connect.
- `Pawn|GetControlRotation` matches two node types. The DSL picked the `Controller` one, so the Blueprint failed to compile with "Target must have a connection". The log did not name the node.

## What worked

- `BlueprintTools.create` with parent `/Script/Engine.Character`. Jump, gravity and the capsule come with the class.
- The DSL for named events like `EventBeginPlay`, and `create_node` plus `connect_pins` for key events. `get_node_infos` confirms the wiring.
- `set_properties` on the class default object (`Default__<Name>_C`) and its `CharMoveComp` subobject, for `AutoPossessPlayer` and `JumpZVelocity`.
- `trace_world` straight down to find the ground, then `ActorTools.set_actor_transform`.
- `CaptureEditorImage` with no arguments to see the PIE result.

## Rule for next time

Read each tool's schema with `describe_toolset` before calling it. Prove wiring by reading it back, and leave input tests to a person or an automation test. The team runs Unreal MCP on port 8765.
