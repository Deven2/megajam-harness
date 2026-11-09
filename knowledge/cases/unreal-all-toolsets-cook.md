# All Toolsets breaks the cook without a Game Features rule

- **Date:** 2026-11-08
- **Area:** unreal-mcp
- **Vendor:** both

## Situation

The first full package of the blank project on UE 5.8.4 compiled and passed its tests, then failed while cooking.

## What went wrong

All Toolsets enables the Game Features plugin. That plugin requires a `GameFeatureData` rule in the Asset Manager settings. Without the rule the cook reports two errors and exits with code 25.

Separately, Unreal MCP has `Runtime` modules and is marked `NoRedist`, so enabling it plainly would compile it into the game target.

## What worked

- Adding `+PrimaryAssetTypesToScan` for `GameFeatureData` in `Config/DefaultGame.ini`.
- Setting `"TargetAllowList": ["Editor"]` on the plugin in `JamGame.uproject`.

The blank build then packaged to a 428 MB zip and passed its smoke test, with no Unreal MCP files in the output.

## Rule for next time

Package early and before anything depends on it. A green compile says little about the cook.
