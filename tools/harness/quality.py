"""Static validation, behavioral evals and the harness contribution flow."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path
from typing import Any

from .common import HARNESS_ROOT, HarnessError, git, load_config, read_toml, run
from .core_model import load_agents, load_hooks, load_instructions, load_servers, load_skills, load_vendor
from .render import render
from .ship import ShipFlow, EXIT_CODES, freeze_message

NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
NON_ENGLISH = re.compile(r"[áéíóúñ¿¡ÁÉÍÓÚÑ]")
SECRET = re.compile(r"(ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|sk-[A-Za-z0-9_-]{24,}|-----BEGIN [A-Z ]*PRIVATE KEY-----)")
MAX_DESCRIPTION = 320
TEXT_SUFFIXES = {".md", ".toml", ".py", ".json", ".yml", ".yaml"}


def validate() -> list[str]:
    errors: list[str] = []
    skills = load_skills()
    agents = load_agents()
    servers = load_servers()
    claude = load_vendor("claude")
    codex = load_vendor("codex")

    for skill in skills:
        if skill.name != skill.directory.name or not NAME.match(skill.name):
            errors.append(f"skill {skill.directory.name}: name must be kebab-case and match its folder.")
        if len(skill.description) > MAX_DESCRIPTION:
            errors.append(f"skill {skill.name}: description is {len(skill.description)} chars, limit {MAX_DESCRIPTION}.")
        if len(skill.body.splitlines()) > 120:
            errors.append(f"skill {skill.name}: body is over 120 lines. Move detail to a reference file.")

    seen: set[str] = set()
    for agent in agents:
        if agent.name in seen or not NAME.match(agent.name):
            errors.append(f"agent {agent.name}: duplicate or invalid name.")
        seen.add(agent.name)
        if agent.path.stem != agent.name:
            errors.append(f"agent {agent.name}: file name must match.")
        if len(agent.description) > MAX_DESCRIPTION:
            errors.append(f"agent {agent.name}: description is {len(agent.description)} chars, limit {MAX_DESCRIPTION}.")
        if agent.tier not in claude["tiers"] or agent.tier not in codex["tiers"]:
            errors.append(f"agent {agent.name}: unknown tier {agent.tier}.")
        if agent.effort not in codex["effort_map"]:
            errors.append(f"agent {agent.name}: unknown effort {agent.effort}.")
        for capability in agent.capabilities:
            if capability not in claude["capabilities"]:
                errors.append(f"agent {agent.name}: unknown capability {capability}.")
        for server in agent.mcp:
            if server not in servers:
                errors.append(f"agent {agent.name}: unknown MCP server {server}.")

    for server_name, server in servers.items():
        if server.get("scope") not in ("agent", "session"):
            errors.append(f"server {server_name}: scope must be agent or session.")

    catalog = HARNESS_ROOT / "docs" / "catalog.md"
    if not catalog.is_file() or catalog.read_text(encoding="utf-8") != catalog_text():
        errors.append("docs/catalog.md is stale. Run `h catalog`.")

    known_actions = {"session-start", "guard", "ledger"}
    for hook in load_hooks():
        if hook["action"] not in known_actions:
            errors.append(f"hook {hook['event']}: unknown action {hook['action']}.")

    instructions = load_instructions()
    if len(instructions.splitlines()) > 110:
        errors.append("core/instructions is over 110 lines. It loads in every session, so keep it short.")

    for folder in ("core", "vendors", "knowledge", "docs", "tools", "devlog"):
        base = HARNESS_ROOT / folder
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in TEXT_SUFFIXES or "__pycache__" in path.parts:
                continue
            if path.name == "quality.py":
                continue
            text = path.read_text(encoding="utf-8")
            if SECRET.search(text):
                errors.append(f"{path.relative_to(HARNESS_ROOT)}: looks like a secret.")
            if NON_ENGLISH.search(text):
                errors.append(f"{path.relative_to(HARNESS_ROOT)}: project content must be in English.")

    for path in sorted((HARNESS_ROOT / "evals" / "cases").glob("*.toml")):
        case = tomllib.loads(path.read_text(encoding="utf-8"))
        if "prompt" not in case:
            errors.append(f"{path.name}: prompt is required.")
        if case.get("expect_skill") and case["expect_skill"] not in {skill.name for skill in skills}:
            errors.append(f"{path.name}: unknown skill {case['expect_skill']}.")
        if case.get("expect_agent") and case["expect_agent"] not in seen:
            errors.append(f"{path.name}: unknown agent {case['expect_agent']}.")

    with tempfile.TemporaryDirectory() as temp:
        for vendor in ("claude", "codex"):
            target = Path(temp) / vendor
            target.mkdir()
            try:
                written = render(vendor, target)
            except HarnessError as exc:
                errors.append(f"render {vendor}: {exc}")
                continue
            for path in written:
                try:
                    if path.suffix == ".json":
                        json.loads(path.read_text(encoding="utf-8"))
                    elif path.suffix == ".toml":
                        tomllib.loads(path.read_text(encoding="utf-8"))
                except ValueError as exc:
                    errors.append(f"render {vendor}: {path.name} is invalid: {exc}")
    return errors


def catalog_text() -> str:
    lines = ["# Catalog", "", "Generated by `h catalog`. Do not edit.", "", "## Skills", "", "| Skill | When it is used |", "| --- | --- |"]
    lines += [f"| `{skill.name}` | {skill.description} |" for skill in load_skills()]
    lines += ["", "## Subagents", "", "| Subagent | Tier | MCP | When it is used |", "| --- | --- | --- | --- |"]
    lines += [f"| `{agent.name}` | {agent.tier} | {', '.join(agent.mcp) or '-'} | {agent.description} |" for agent in load_agents()]
    return "\n".join(lines) + "\n"


def write_catalog() -> int:
    (HARNESS_ROOT / "docs" / "catalog.md").write_text(catalog_text(), encoding="utf-8", newline="\n")
    print("Catalog written.")
    return 0


def footprint() -> dict[str, int]:
    skills = load_skills()
    agents = load_agents()
    return {
        "skills": len(skills),
        "agents": len(agents),
        "description_chars": sum(len(s.description) for s in skills) + sum(len(a.description) for a in agents),
        "instruction_lines": len(load_instructions().splitlines()),
    }


def validate_command() -> int:
    errors = validate()
    print(json.dumps(footprint()))
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors))
        return 1
    print("Validation passed.")
    return 0


# --- Behavioral evals --------------------------------------------------------

BLOCKED_TOOLS = "Bash,PowerShell,Edit,Write,NotebookEdit,WebFetch,WebSearch"


def build_workspace(vendor: str, parent: Path) -> Path:
    workspace = parent / "workspace"
    workspace.mkdir()
    run(["git", "init", "-q"], cwd=workspace, check=True)
    render(vendor, workspace)
    settings = workspace / ".claude" / "settings.json"
    if settings.is_file():  # Evals measure routing, so hooks stay out of the sandbox.
        data = json.loads(settings.read_text(encoding="utf-8"))
        data.pop("hooks", None)
        settings.write_text(json.dumps(data), encoding="utf-8")
    hooks = workspace / ".codex" / "hooks.json"
    if hooks.is_file():
        hooks.unlink()
    return workspace


def run_claude(prompt: str, workspace: Path, max_turns: int) -> dict[str, Any]:
    model = load_vendor("claude")["tiers"]["fast"]
    command = [
        "claude", "-p", prompt, "--output-format", "stream-json", "--verbose", "--model", model,
        "--max-turns", str(max_turns), "--permission-mode", "dontAsk", "--strict-mcp-config",
        "--mcp-config", '{"mcpServers":{}}', "--disallowedTools", BLOCKED_TOOLS,
    ]
    result = run(command, cwd=workspace, timeout=240)
    skills: list[str] = []
    agents: list[str] = []
    tools: list[str] = []
    answer = ""
    cost = 0.0
    events = 0
    for line in result.stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        events += 1
        if event.get("type") == "result":
            cost = float(event.get("total_cost_usd") or 0)
        for block in (event.get("message") or {}).get("content", []) if isinstance(event.get("message"), dict) else []:
            if isinstance(block, dict) and block.get("type") == "text":
                answer = str(block.get("text", ""))
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tools.append(str(block.get("name", "")))
                if block.get("name") == "Skill":
                    skills.append(str(block.get("input", {}).get("skill", "")))
                if block.get("name") in ("Agent", "Task"):
                    agents.append(str(block.get("input", {}).get("subagent_type", "")))
    # Hitting the turn limit exits non-zero but is how these short runs normally end.
    error = result.stderr[-400:] if result.returncode and not events else ""
    return {"skills": skills, "agents": agents, "tools": tools, "answer": answer[:300], "cost_usd": cost, "output": result.stdout, "error": error}


def run_codex(prompt: str, workspace: Path, max_turns: int) -> dict[str, Any]:
    model = load_vendor("codex")["tiers"]["fast"]["model"]
    command = ["codex", "exec", "--json", "--sandbox", "read-only", "--skip-git-repo-check", "-m", model, prompt]
    result = run(command, cwd=workspace, timeout=240)
    skills = re.findall(r"\.agents[\\/]+skills[\\/]+([a-z0-9-]+)[\\/]+SKILL\.md", result.stdout)
    agents = re.findall(r'agent_type"?\s*[:=]\s*"([a-z0-9-]+)"', result.stdout)
    error = result.stderr[-400:] if result.returncode and not result.stdout.strip() else ""
    return {"skills": skills, "agents": agents, "tools": [], "answer": "", "cost_usd": 0.0, "output": result.stdout, "error": error}


def changed_paths() -> set[str]:
    result = git(["diff", "--name-only", "origin/dev"], HARNESS_ROOT, check=False)
    return set(result.stdout.splitlines()) if result.returncode == 0 else set()


def select_cases(selection: str) -> list[tuple[str, dict[str, Any]]]:
    cases = [(p.stem, read_toml(p)) for p in sorted((HARNESS_ROOT / "evals" / "cases").glob("*.toml"))]
    if selection == "all":
        return cases
    if selection != "changed":
        return [item for item in cases if item[0] == selection]
    changed = changed_paths()
    picked = []
    for name, case in cases:
        roots = []
        if case.get("expect_skill"):
            roots.append(f"core/skills/{case['expect_skill']}/")
        if case.get("expect_agent"):
            roots.append(f"core/agents/{case['expect_agent']}.md")
        if any(path.startswith(tuple(roots)) for path in changed) or any(path.startswith("core/instructions/") for path in changed):
            picked.append((name, case))
    return picked


def grade(case: dict[str, Any], outcome: dict[str, Any]) -> list[str]:
    failures = []
    if outcome["error"]:
        failures.append(f"run error: {outcome['error']}")
    if case.get("expect_skill") and case["expect_skill"] not in outcome["skills"]:
        failures.append(f"expected skill {case['expect_skill']}, saw {outcome['skills']}")
    if case.get("expect_agent") and case["expect_agent"] not in outcome["agents"]:
        failures.append(f"expected agent {case['expect_agent']}, saw {outcome['agents']}")
    for forbidden in case.get("forbid_skills", []):
        if forbidden in outcome["skills"]:
            failures.append(f"skill {forbidden} must not run")
    if case.get("expect_no_skill") and outcome["skills"]:
        failures.append(f"no skill should run, saw {outcome['skills']}")
    return failures


def run_evals(vendor: str, selection: str) -> int:
    cases = select_cases(selection)
    if not cases:
        print(json.dumps({"cases": 0, "note": "No eval covers the changed files."}))
        return 0
    runner = run_claude if vendor == "claude" else run_codex
    report = []
    total_cost = 0.0
    with tempfile.TemporaryDirectory() as temp:
        workspace = build_workspace(vendor, Path(temp))
        for name, case in cases:
            outcome = runner(case["prompt"], workspace, int(case.get("max_turns", 2)))
            failures = grade(case, outcome)
            total_cost += outcome["cost_usd"]
            entry = {"case": name, "passed": not failures, "skills": outcome["skills"], "agents": outcome["agents"]}
            if failures:
                entry.update(failures=failures, tools=outcome["tools"], answer=outcome["answer"])
            report.append(entry)
    print(json.dumps({"vendor": vendor, "passed": sum(item["passed"] for item in report), "total": len(report), "estimated_cost_usd": round(total_cost, 4), "cases": report}, indent=2))
    return 0 if all(item["passed"] for item in report) else 1


# --- Contribution flow -------------------------------------------------------

def unit_tests() -> bool:
    result = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-q"], cwd=HARNESS_ROOT, timeout=600)
    if result.returncode != 0:
        print(result.stdout + result.stderr)
    return result.returncode == 0


def contribute(options: dict[str, Any], vendor: str, skip_evals: bool, blocker: str | None = None) -> int:
    cfg = load_config()
    frozen = freeze_message(cfg, blocker)
    if frozen:
        print(json.dumps({"status": "harness-frozen", "message": frozen}, indent=2))
        return EXIT_CODES["harness-frozen"]
    if blocker:
        options = {**options, "body": f"{options.get('body') or ''}\n\nFreeze exception: {blocker}".strip()}
    errors = validate()
    if errors:
        print("\n".join(f"ERROR {error}" for error in errors))
        return 6
    if not unit_tests():
        return 6
    if not skip_evals and shutil.which(vendor):
        status = run_evals(vendor, "changed")
        if status != 0:
            return 6
    result = ShipFlow(HARNESS_ROOT, cfg, options).run()
    print(json.dumps(result, indent=2))
    return EXIT_CODES.get(result["status"], 1)
