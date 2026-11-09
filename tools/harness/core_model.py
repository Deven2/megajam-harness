"""Loads the vendor-neutral definitions stored in core/."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .common import HARNESS_ROOT, HarnessError, read_toml


@dataclass
class Agent:
    name: str
    description: str
    tier: str
    effort: str
    capabilities: list[str]
    mcp: list[str]
    max_turns: int
    body: str
    path: Path


@dataclass
class Skill:
    name: str
    description: str
    directory: Path
    body: str = field(repr=False, default="")


def parse_agent(path: Path) -> Agent:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"^\+\+\+\s*$", text, maxsplit=2, flags=re.MULTILINE)
    if len(parts) != 3 or parts[0].strip():
        raise HarnessError(f"{path}: expected +++ TOML front matter.")
    try:
        meta = tomllib.loads(parts[1])
    except tomllib.TOMLDecodeError as exc:
        raise HarnessError(f"{path}: invalid front matter: {exc}") from exc
    missing = {"name", "description", "tier", "effort", "capabilities"} - set(meta)
    if missing:
        raise HarnessError(f"{path}: missing fields: {sorted(missing)}")
    return Agent(
        name=meta["name"],
        description=meta["description"],
        tier=meta["tier"],
        effort=meta["effort"],
        capabilities=list(meta["capabilities"]),
        mcp=list(meta.get("mcp", [])),
        max_turns=int(meta.get("max_turns", 20)),
        body=parts[2].strip() + "\n",
        path=path,
    )


def parse_skill(directory: Path) -> Skill:
    path = directory / "SKILL.md"
    if not path.is_file():
        raise HarnessError(f"{directory}: SKILL.md is missing.")
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, flags=re.DOTALL)
    if not match:
        raise HarnessError(f"{path}: expected YAML front matter.")
    fields: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip().strip('"')
    if "name" not in fields or "description" not in fields:
        raise HarnessError(f"{path}: name and description are required.")
    return Skill(fields["name"], fields["description"], directory, match.group(2))


def load_agents(root: Path = HARNESS_ROOT) -> list[Agent]:
    return [parse_agent(path) for path in sorted((root / "core" / "agents").glob("*.md"))]


def load_skills(root: Path = HARNESS_ROOT) -> list[Skill]:
    skills_dir = root / "core" / "skills"
    return [parse_skill(path) for path in sorted(p for p in skills_dir.iterdir() if p.is_dir())]


def load_servers(root: Path = HARNESS_ROOT) -> dict[str, dict[str, Any]]:
    return read_toml(root / "core" / "mcp" / "servers.toml")["servers"]


def load_hooks(root: Path = HARNESS_ROOT) -> list[dict[str, Any]]:
    return read_toml(root / "core" / "hooks" / "hooks.toml")["hook"]


def load_instructions(root: Path = HARNESS_ROOT) -> str:
    fragments = sorted((root / "core" / "instructions").glob("*.md"))
    return "\n".join(path.read_text(encoding="utf-8").strip() + "\n" for path in fragments)


def load_vendor(name: str, root: Path = HARNESS_ROOT) -> dict[str, Any]:
    return read_toml(root / "vendors" / f"{name}.toml")
