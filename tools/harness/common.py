"""Helpers shared by every harness command."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Sequence

HARNESS_ROOT = Path(__file__).resolve().parents[2]
LOCK_RELATIVE = Path(".harness") / "lock.json"

BINARY_EXTENSIONS = {
    ".uasset", ".umap", ".ubulk", ".uexp",
    ".blend", ".blend1", ".fbx", ".glb", ".gltf", ".obj", ".abc",
    ".png", ".jpg", ".jpeg", ".tga", ".exr", ".hdr", ".psd", ".tif", ".tiff",
    ".wav", ".ogg", ".mp3", ".flac", ".mp4", ".mov", ".webm",
    ".ttf", ".otf", ".zip", ".7z",
}
LOCKABLE_EXTENSIONS = {".uasset", ".umap"}


class HarnessError(RuntimeError):
    """An expected failure that should be reported without a traceback."""


def load_config(root: Path = HARNESS_ROOT) -> dict[str, Any]:
    return tomllib.loads((root / "harness.toml").read_text(encoding="utf-8"))


def read_toml(path: Path) -> dict[str, Any]:
    return tomllib.loads(path.read_text(encoding="utf-8"))


def run(
    cmd: Sequence[str],
    cwd: Path | str | None = None,
    env: dict[str, str] | None = None,
    input_text: str | None = None,
    timeout: float | None = None,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    try:
        result = subprocess.run(
            list(cmd),
            cwd=str(cwd) if cwd else None,
            env=merged,
            input=input_text if input_text is not None else "",
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise HarnessError(f"Command not found: {cmd[0]}") from exc
    if check and result.returncode != 0:
        raise HarnessError(f"{' '.join(cmd)} failed:\n{result.stdout}{result.stderr}".strip())
    return result


def git(args: Sequence[str], cwd: Path, env: dict[str, str] | None = None, check: bool = True, timeout: float | None = None):
    return run(["git", *args], cwd=cwd, env=env, check=check, timeout=timeout)


def git_out(args: Sequence[str], cwd: Path) -> str:
    return git(args, cwd).stdout.strip()


def gh_command() -> list[str]:
    """Return the GitHub CLI command. HARNESS_GH (a JSON list) replaces it in tests."""
    override = os.environ.get("HARNESS_GH")
    if override:
        return json.loads(override)
    return ["gh"]


def has_tool(name: str) -> bool:
    return shutil.which(name) is not None


def repo_root(start: Path) -> Path:
    result = git(["rev-parse", "--show-toplevel"], cwd=start, check=False)
    if result.returncode != 0:
        raise HarnessError(f"{start} is not inside a git repository.")
    return Path(result.stdout.strip()).resolve()


def find_marker_root(start: Path) -> tuple[Path | None, str]:
    """Walk upward and classify the workspace without spawning git."""
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / LOCK_RELATIVE).is_file():
            return candidate, "game"
        if (candidate / "harness.toml").is_file() and (candidate / "core").is_dir():
            return candidate, "harness"
    return None, "unknown"


def read_lock(game_root: Path) -> dict[str, Any]:
    path = game_root / LOCK_RELATIVE
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def now_utc() -> datetime:
    """Return the current time. HARNESS_NOW replaces it in tests and rehearsals."""
    override = os.environ.get("HARNESS_NOW")
    if override:
        return parse_utc(override)
    return datetime.now(timezone.utc)


def contest_phase(cfg: dict[str, Any], now: datetime | None = None) -> str:
    moment = now or now_utc()
    contest = cfg["contest"]
    start = parse_utc(contest["start_utc"])
    deadline = parse_utc(contest["deadline_utc"])
    freeze = deadline - timedelta(hours=contest["freeze_hours_before_deadline"])
    if moment < start:
        return "pre-jam"
    if moment < freeze:
        return "jam"
    if moment <= deadline:
        return "freeze"
    return "post-jam"


def format_delta(delta: timedelta) -> str:
    total = int(delta.total_seconds())
    sign = "-" if total < 0 else ""
    total = abs(total)
    hours, remainder = divmod(total, 3600)
    return f"{sign}{hours}h{remainder // 60:02d}m"


def slugify(text: str, limit: int = 40) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:limit].strip("-") or "change"


def to_posix(path: Path | str) -> str:
    return str(path).replace("\\", "/")
