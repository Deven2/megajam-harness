"""Turns core/ into the files each vendor reads."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .common import HARNESS_ROOT, HarnessError, load_config, to_posix
from .core_model import Agent, load_agents, load_hooks, load_instructions, load_servers, load_skills, load_vendor

VENDORS = ("claude", "codex")
GENERATED = [
    "CLAUDE.md", "AGENTS.md", ".mcp.json",
    ".claude/agents", ".claude/skills", ".claude/settings.json",
    ".agents/skills",
    ".codex/agents", ".codex/config.toml", ".codex/hooks.json",
]


@dataclass
class RenderContext:
    vendor: str
    target: Path
    harness_root: Path
    config: dict[str, Any]
    shim_sh: str
    shim_cmd: str


def substitutions(ctx: RenderContext) -> dict[str, str]:
    project = ctx.config["project"]
    branches = ctx.config["branches"]
    return {
        "h": ".harness/h" if ctx.vendor == "claude" else r".\.harness\h.cmd",
        "codename": project["codename"],
        "vendor": ctx.vendor,
        "integration": branches["integration"],
        "production": branches["production"],
        "harness_path": to_posix(ctx.harness_root),
    }


def fill(text: str, subs: dict[str, str]) -> str:
    for key, value in subs.items():
        text = text.replace("{{" + key + "}}", value)
    if "{{" in text:
        start = text.index("{{")
        raise HarnessError(f"Unresolved placeholder near: {text[start:start + 40]!r}")
    return text


def write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return path


def clean(target: Path) -> None:
    for relative in GENERATED:
        path = target / relative
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()


def copy_skills(ctx: RenderContext, destination: Path, subs: dict[str, str]) -> list[Path]:
    written: list[Path] = []
    for skill in load_skills(ctx.harness_root):
        for source in skill.directory.rglob("*"):
            if source.is_dir():
                continue
            output = destination / skill.name / source.relative_to(skill.directory)
            if source.suffix in (".md", ".txt", ".toml", ".py", ".ps1"):
                written.append(write(output, fill(source.read_text(encoding="utf-8"), subs)))
            else:
                output.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, output)
                written.append(output)
    return written


def yaml_inline(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def claude_inline_server(name: str, server: dict[str, Any]) -> list[str]:
    lines = [f"  - {name}:", f"      type: {server['transport']}"]
    if server["transport"] == "http":
        lines.append(f"      url: {yaml_inline(server['url'])}")
    else:
        lines.append(f"      command: {yaml_inline(server['command'])}")
        lines.append(f"      args: {yaml_inline(server.get('args', []))}")
        if server.get("env"):
            lines.append(f"      env: {yaml_inline(server['env'])}")
    return lines


def render_claude_agent(agent: Agent, vendor: dict[str, Any], servers: dict[str, Any], subs: dict[str, str]) -> str:
    allowed = {tool for capability in agent.capabilities for tool in vendor["capabilities"][capability]}
    denied = [tool for tool in vendor["builtin_tools"] if tool not in allowed]
    lines = [
        "---",
        f"name: {agent.name}",
        f"description: {yaml_inline(agent.description)}",
        f"model: {vendor['tiers'][agent.tier]}",
        f"effort: {agent.effort}",
        f"maxTurns: {agent.max_turns}",
        f"disallowedTools: {', '.join(denied)}",
    ]
    if agent.mcp:
        lines.append("mcpServers:")
        for name in agent.mcp:
            server = servers[name]
            lines.extend(claude_inline_server(name, server) if server["scope"] == "agent" else [f"  - {name}"])
    lines.extend(["---", "", fill(agent.body, subs)])
    return "\n".join(lines)


def claude_mcp_json(servers: dict[str, Any], ctx: RenderContext) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for name, server in servers.items():
        if server["scope"] != "session":
            continue
        entry: dict[str, Any] = {"type": server["transport"], "url": server["url"]}
        if server.get("headers"):
            entry["headers"] = server["headers"]
        if server.get("auth") == "github-token":
            entry["headersHelper"] = f'"{ctx.shim_sh}" mcp-headers github'
        output[name] = entry
    return {"mcpServers": output}


def claude_hooks(ctx: RenderContext) -> dict[str, Any]:
    hooks: dict[str, Any] = {}
    for hook in load_hooks(ctx.harness_root):
        matcher = hook.get("matcher_claude", hook.get("matcher"))
        handler = {
            "type": "command",
            "command": f'"$CLAUDE_PROJECT_DIR/.harness/h" hook {hook["action"]}',
            "shell": "bash",
            "timeout": hook["timeout"],
        }
        group: dict[str, Any] = {"hooks": [handler]}
        if matcher:
            group["matcher"] = matcher
        hooks.setdefault(hook["event"], []).append(group)
    return hooks


def render_claude(ctx: RenderContext) -> list[Path]:
    vendor = load_vendor("claude", ctx.harness_root)
    subs = substitutions(ctx)
    servers = load_servers(ctx.harness_root)
    target = ctx.target
    written = [write(target / "CLAUDE.md", fill(load_instructions(ctx.harness_root), subs))]
    written += copy_skills(ctx, target / ".claude" / "skills", subs)
    for agent in load_agents(ctx.harness_root):
        written.append(write(target / ".claude" / "agents" / f"{agent.name}.md", render_claude_agent(agent, vendor, servers, subs)))
    written.append(write(target / ".mcp.json", json.dumps(claude_mcp_json(servers, ctx), indent=2) + "\n"))
    settings = {
        "model": vendor["main_model"],
        "permissions": {
            "defaultMode": vendor["permissions"]["default_mode"],
            "allow": vendor["permissions"]["allow"],
            "deny": vendor["permissions"]["deny"],
        },
        "enabledMcpjsonServers": [name for name, server in servers.items() if server["scope"] == "session"],
        "env": vendor["env"],
        "hooks": claude_hooks(ctx),
    }
    written.append(write(target / ".claude" / "settings.json", json.dumps(settings, indent=2) + "\n"))
    return written


def toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(toml_value(item) for item in value) + "]"
    if isinstance(value, dict):
        return "{ " + ", ".join(f"{json.dumps(k)} = {toml_value(v)}" for k, v in value.items()) + " }"
    raise HarnessError(f"Cannot serialize {value!r} as TOML.")


def render_codex_agent(agent: Agent, vendor: dict[str, Any], subs: dict[str, str]) -> str:
    tier = vendor["tiers"][agent.tier]
    lines = [
        f"name = {toml_value(agent.name)}",
        f"description = {toml_value(agent.description)}",
        f"model = {toml_value(tier['model'])}",
        f"model_reasoning_effort = {toml_value(vendor['effort_map'][agent.effort])}",
        f"developer_instructions = {toml_value(fill(agent.body, subs))}",
    ]
    if "shell" not in agent.capabilities:
        lines.extend(["", "[features]", "shell_tool = false"])
    return "\n".join(lines) + "\n"


def codex_config(servers: dict[str, Any], vendor: dict[str, Any], ctx: RenderContext) -> str:
    lines = [
        "# Generated by megajam-harness. Do not edit.",
        f"approval_policy = {toml_value(vendor['approval_policy'])}",
        f"sandbox_mode = {toml_value(vendor['sandbox_mode'])}",
        "",
        "[sandbox_workspace_write]",
        "network_access = true",
        f"writable_roots = {toml_value([to_posix(ctx.harness_root)])}",
        "",
        "[agents]",
        f"max_concurrent_threads_per_session = {vendor['max_concurrent_subagents']}",
    ]
    for name, server in servers.items():
        lines.extend(["", f"[mcp_servers.{name}]"])
        if server["transport"] == "http":
            lines.append(f"url = {toml_value(server['url'])}")
            if server.get("headers"):
                lines.append(f"http_headers = {toml_value(server['headers'])}")
            if server.get("auth") == "github-token":
                lines.append('bearer_token_env_var = "GITHUB_PAT"')
        else:
            lines.append(f"command = {toml_value(server['command'])}")
            lines.append(f"args = {toml_value(server.get('args', []))}")
            if server.get("env"):
                lines.append(f"env = {toml_value(server['env'])}")
    return "\n".join(lines) + "\n"


def codex_hooks(ctx: RenderContext) -> dict[str, Any]:
    hooks: dict[str, Any] = {}
    for hook in load_hooks(ctx.harness_root):
        matcher = hook.get("matcher_codex", hook.get("matcher"))
        handler = {
            "type": "command",
            "command": f'"{ctx.shim_sh}" hook {hook["action"]}',
            "commandWindows": f'"{ctx.shim_cmd}" hook {hook["action"]}' if " " in ctx.shim_cmd else f'{ctx.shim_cmd} hook {hook["action"]}',
            "timeout": hook["timeout"],
            "statusMessage": hook.get("status", "Running harness hook"),
        }
        group: dict[str, Any] = {"hooks": [handler]}
        if matcher:
            group["matcher"] = matcher
        hooks.setdefault(hook["event"], []).append(group)
    return {"description": "Generated by megajam-harness. Do not edit.", "hooks": hooks}


def render_codex(ctx: RenderContext) -> list[Path]:
    vendor = load_vendor("codex", ctx.harness_root)
    subs = substitutions(ctx)
    servers = load_servers(ctx.harness_root)
    target = ctx.target
    written = [write(target / "AGENTS.md", fill(load_instructions(ctx.harness_root), subs))]
    written += copy_skills(ctx, target / ".agents" / "skills", subs)
    for agent in load_agents(ctx.harness_root):
        written.append(write(target / ".codex" / "agents" / f"{agent.name}.toml", render_codex_agent(agent, vendor, subs)))
    written.append(write(target / ".codex" / "config.toml", codex_config(servers, vendor, ctx)))
    written.append(write(target / ".codex" / "hooks.json", json.dumps(codex_hooks(ctx), indent=2) + "\n"))
    return written


def render(vendor: str, target: Path, harness_root: Path = HARNESS_ROOT, config: dict[str, Any] | None = None) -> list[Path]:
    if vendor not in VENDORS:
        raise HarnessError(f"Unknown vendor: {vendor}")
    ctx = RenderContext(
        vendor=vendor,
        target=target,
        harness_root=harness_root,
        config=config or load_config(harness_root),
        shim_sh=to_posix(target / ".harness" / "h"),
        shim_cmd=str(target / ".harness" / "h.cmd"),
    )
    clean(target)
    return render_claude(ctx) if vendor == "claude" else render_codex(ctx)
