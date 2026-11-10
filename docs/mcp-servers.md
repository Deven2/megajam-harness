# MCP servers

## Unreal MCP

Epic's plugin, experimental in UE 5.8. Internal name `ModelContextProtocol`.

- **Setup:** none. The game project enables Unreal MCP and All Toolsets, limits the server to the Editor target and starts it automatically.
- **Endpoint:** `http://127.0.0.1:8765/mcp`. No authentication, loopback only. The plugin defaults to 8000, which other software often takes, so the game sets `ServerPortNumber=8765` in `Config/DefaultEditorPerProjectUserSettings.ini`.
- **Tools:** tool search is on by default, so the client sees `list_toolsets`, `describe_toolset` and `call_tool`.
- **Limit:** calls run serially on the game thread. Never overlap them.
- **Extending:** `meta = (AICallable)` on a `UFUNCTION`, then `ModelContextProtocol.RefreshTools`. New declarations need an editor restart.
- **Verify:** `npx @modelcontextprotocol/inspector`, then connect over Streamable HTTP.

Start the AI tool after the editor. The harness generates this configuration, so `GenerateClientConfig` is not needed.

The plugin logs that data it sends to an LLM service is Licensed Technology under the UE EULA, section 6(e), and that the user must ensure the provider does not train on it. Every teammate turns off model training in their account before connecting.

## Blender MCP

Package `mcp-for-blender`, run with `uvx`.

- **Setup:** `uvx mcp-for-blender install-addon`. Enable Interface: MCP for Blender, press N, open the tab and click Start MCP Server.
- **Connection:** `localhost:9876`, no authentication. Never expose it.
- **Telemetry:** disabled by the harness with `DISABLE_TELEMETRY=true`.
- **Limit:** one client at a time.
- **Risk:** `execute_blender_code` runs arbitrary Python. Save first. `BLENDER_MCP_SAFE_MODE=1` screens scripts if needed.
- **Asset tools:** `generate_3d` and `import_asset` reach Poly Haven, Sketchfab, Hyper3D, Hunyuan3D and others. Most need their own keys. Check each provider's license.

## GitHub MCP

- **Endpoint:** `https://api.githubcopilot.com/mcp/`, with toolsets limited through `X-MCP-Toolsets`.
- **Auth:** a token from `gh auth login --scopes workflow`.
- **Use:** pull requests, issues and CI logs.
- **Limit:** it cannot commit a local working tree with LFS files, so `h ship` uses local git and the GitHub CLI.

## Trello MCP

Official server at `https://mcp.trello.com/v1`.

- **Auth:** OAuth in a browser only. API tokens are not supported.
- **Setup:** connect from your AI tool (`/mcp`), choose the workspace and approve read, write and search.
- **Limits:** archives but never deletes. Cannot upload local files or create labels yet. CI cannot use it.
