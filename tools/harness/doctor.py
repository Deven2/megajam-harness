"""Checks that a machine is ready to work on the project."""

from __future__ import annotations

import json
import glob
import os
import re
import shutil
import socket
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from .common import has_tool, load_config, read_lock, run, git


@dataclass
class Check:
    name: str
    status: str  # ok, warn or fail
    detail: str
    fix: str = ""


def tool_check(name: str, fix: str, required: bool = True) -> Check:
    if has_tool(name):
        return Check(name, "ok", shutil.which(name) or "")
    return Check(name, "fail" if required else "warn", "not found", fix)


def engine_directory(version: str) -> str | None:
    override = os.environ.get("UE_ROOT")
    if override:
        return override
    if os.name != "nt":
        return None
    import winreg

    # The registry can be stale and Launcher installs may not appear in it, so verify each candidate.
    candidates: list[str] = []
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, rf"SOFTWARE\EpicGames\Unreal Engine\{version}") as key:
            candidates.append(str(winreg.QueryValueEx(key, "InstalledDirectory")[0]))
    except OSError:
        pass
    manifests = Path(os.environ.get("ProgramData", r"C:\ProgramData")) / "Epic" / "EpicGamesLauncher" / "Data" / "Manifests"
    for item in manifests.glob("*.item"):
        location = str(json.loads(item.read_text(encoding="utf-8")).get("InstallLocation", ""))
        if location.endswith(f"UE_{version}"):
            candidates.append(location)
    candidates.append(rf"C:\Program Files\Epic Games\UE_{version}")
    return next((c for c in candidates if (Path(c) / "Engine" / "Build" / "BatchFiles" / "Build.bat").is_file()), None)


def visual_studio_check() -> Check:
    vswhere = Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft Visual Studio" / "Installer" / "vswhere.exe"
    fix = "Install Visual Studio 2026 (recommended by Epic) or 2022 17.14+ with Game development with C++."
    if not vswhere.is_file():
        return Check("visual-studio", "fail", "vswhere not found", fix)
    output = run([str(vswhere), "-all", "-products", "*", "-format", "json"]).stdout
    versions = [item.get("installationVersion", "") for item in json.loads(output or "[]")]
    def supported(version: str) -> bool:
        parts = [int(p) for p in version.split(".")[:2]]
        return parts >= [17, 14]
    good = [v for v in versions if supported(v)]
    if good:
        return Check("visual-studio", "ok", ", ".join(good))
    return Check("visual-studio", "fail", f"found {versions or 'none'}", fix)


def blender_check(required: bool) -> Check:
    found = shutil.which("blender")
    if not found and os.name == "nt":
        matches = glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe")
        found = sorted(matches)[-1] if matches else None
    if found:
        return Check("blender", "ok", found)
    return Check("blender", "fail" if required else "warn", "not found", "winget install BlenderFoundation.Blender")


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def parse_size(text: str) -> float:
    match = re.search(r"\(([\d.]+)\s*([KMGT]?)B\)", text)
    if not match:
        return 0.0
    factor = {"": 1, "K": 1e3, "M": 1e6, "G": 1e9, "T": 1e12}[match.group(2)]
    return float(match.group(1)) * factor


def lfs_usage_bytes(root: Path) -> float:
    output = run(["git", "lfs", "ls-files", "--all", "--long", "--size"], cwd=root, timeout=20).stdout
    objects: dict[str, float] = {}
    for line in output.splitlines():
        oid = line.split(" ", 1)[0]
        objects[oid] = parse_size(line)
    return sum(objects.values())


def collect_checks(vendor: str | None, game_root: Path | None, role: str = "dev", live: bool = False) -> list[Check]:
    cfg = load_config()
    checks: list[Check] = []
    version_ok = sys.version_info >= (3, 11)
    checks.append(Check("python", "ok" if version_ok else "fail", sys.version.split()[0], "" if version_ok else "winget install astral-sh.uv"))
    checks.append(tool_check("git", "winget install Git.Git"))
    checks.append(tool_check("git-lfs", "winget install GitHub.GitLFS"))
    gh = tool_check("gh", "winget install GitHub.cli")
    checks.append(gh)
    if gh.status == "ok":
        auth = run(["gh", "auth", "status"])
        checks.append(Check("gh-auth", "ok" if auth.returncode == 0 else "fail", "signed in" if auth.returncode == 0 else "not signed in", "gh auth login --scopes workflow"))
    checks.append(tool_check("uv", "winget install astral-sh.uv"))
    if vendor == "claude":
        checks.append(tool_check("claude", "irm https://claude.ai/install.ps1 | iex"))
    elif vendor == "codex":
        checks.append(tool_check("codex", "npm install -g @openai/codex"))

    engine = engine_directory("5.8")
    checks.append(Check("unreal-5.8", "ok" if engine else "fail", engine or "not installed", "" if engine else "Install Unreal Engine 5.8 from the Epic Games Launcher."))
    checks.append(visual_studio_check() if os.name == "nt" else Check("visual-studio", "warn", "Windows only"))
    checks.append(blender_check(required=role == "art"))

    if game_root:
        path_text = str(game_root)
        if " " in path_text:
            checks.append(Check("game-path", "fail" if vendor == "codex" else "warn", f"{path_text} contains spaces", "Clone to a short path without spaces, for example C:\\Repos\\MegaJam\\game."))
        elif len(path_text) > 60:
            checks.append(Check("game-path", "warn", f"{path_text} is long", "Use a shorter path to avoid Windows path limits."))
        else:
            checks.append(Check("game-path", "ok", path_text))
        free_gib = shutil.disk_usage(game_root).free / 2**30
        checks.append(Check("disk", "ok" if free_gib >= 50 else "warn", f"{free_gib:.0f} GiB free", "" if free_gib >= 50 else "Keep at least 50 GiB free for builds and caches."))
        hooks = git(["config", "--local", "core.hooksPath"], game_root, check=False).stdout.strip()
        checks.append(Check("git-hooks", "ok" if hooks == ".githooks" else "fail", hooks or "not set", "" if hooks == ".githooks" else "Run `h install` again."))
        lfs_limit = cfg["limits"]["lfs_storage_gib"] * 2**30
        used = lfs_usage_bytes(game_root)
        ratio = used / lfs_limit
        status = "ok" if ratio < cfg["limits"]["lfs_warn_ratio"] else "warn"
        checks.append(Check("lfs-storage", status, f"{used / 2**30:.2f} GiB of {cfg['limits']['lfs_storage_gib']} GiB (all versions)", "" if status == "ok" else "Stop pushing large binaries and warn the team."))
        lock = read_lock(game_root)
        if lock:
            head = git(["rev-parse", "HEAD"], Path(lock["harness_path"]), check=False).stdout.strip()
            current = head == lock.get("harness_sha")
            checks.append(Check("harness-render", "ok" if current else "warn", lock.get("harness_sha", "")[:8], "" if current else "Run `h render`."))
    if live:
        checks.append(Check("unreal-mcp-port", "ok" if port_open(8000) else "warn", "127.0.0.1:8000", "Open the editor and start the MCP server."))
        checks.append(Check("blender-mcp-port", "ok" if port_open(9876) else "warn", "127.0.0.1:9876", "Open Blender and click Start MCP Server."))
    return checks


def print_checks(checks: list[Check]) -> None:
    icons = {"ok": "[ ok ]", "warn": "[warn]", "fail": "[FAIL]"}
    for check in checks:
        line = f"{icons[check.status]} {check.name}: {check.detail}"
        print(line)
        if check.fix and check.status != "ok":
            print(f"       fix: {check.fix}")


def doctor(vendor: str | None, game_root: Path | None, role: str, live: bool, as_json: bool) -> int:
    checks = collect_checks(vendor, game_root, role, live)
    if as_json:
        print(json.dumps([asdict(check) for check in checks], indent=2))
    else:
        print_checks(checks)
    return 1 if any(check.status == "fail" for check in checks) else 0
