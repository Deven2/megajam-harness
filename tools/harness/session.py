"""SessionStart hook: one short status block with no model cost."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .common import HARNESS_ROOT, contest_phase, find_marker_root, format_delta, git, load_config, now_utc, parse_utc, read_lock
from .doctor import lfs_usage_bytes


def harness_drift(cfg: dict) -> str | None:
    branch = cfg["branches"]["harness_track"]
    try:
        remote = git(["ls-remote", "origin", f"refs/heads/{branch}"], HARNESS_ROOT, check=False, timeout=4).stdout.split()
    except subprocess.TimeoutExpired:
        return None
    if not remote:
        return None
    local = git(["rev-parse", "HEAD"], HARNESS_ROOT, check=False).stdout.strip()
    if remote[0] != local:
        return f"The harness is out of date (local {local[:8]}, origin/{branch} {remote[0][:8]}). Tell the user and offer the harness-update skill."
    return None


def status_lines(cwd: Path) -> list[str]:
    root, kind = find_marker_root(cwd)
    if kind != "game" or root is None:
        return []
    cfg = load_config()
    now = now_utc()
    phase = contest_phase(cfg, now)
    start = parse_utc(cfg["contest"]["start_utc"])
    deadline = parse_utc(cfg["contest"]["deadline_utc"])
    branch = git(["branch", "--show-current"], root, check=False).stdout.strip()
    timing = f"starts in {format_delta(start - now)}" if phase == "pre-jam" else f"deadline in {format_delta(deadline - now)}"
    lines = [f"[harness] phase={phase} ({timing}) vendor={read_lock(root).get('vendor')} branch={branch}"]
    if phase == "pre-jam":
        lines.append("[harness] PRE-JAM: no gameplay, levels or art may be created yet (constraint C-01).")
    if phase == "freeze":
        lines.append("[harness] CONTENT FREEZE: only fixes and packaging. A person must submit the entry.")
    drift = harness_drift(cfg)
    if drift:
        lines.append(f"[harness] {drift}")
    if read_lock(root).get("harness_sha") != git(["rev-parse", "HEAD"], HARNESS_ROOT, check=False).stdout.strip():
        lines.append("[harness] The generated files are behind the local harness clone. Offer the harness-update skill.")
    try:
        used = lfs_usage_bytes(root)
        limit = cfg["limits"]["lfs_storage_gib"] * 2**30
        if used / limit >= cfg["limits"]["lfs_warn_ratio"]:
            lines.append(f"[harness] LFS storage at {used / limit:.0%} of the free quota. Warn the team before pushing more binaries.")
    except (subprocess.TimeoutExpired, OSError):
        pass
    return lines


def hook_main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        cwd = Path(str(payload.get("cwd") or Path.cwd()))
        lines = status_lines(cwd)
    except Exception as exc:  # A status message must never block a session.
        print(f"[harness] status unavailable: {exc}")
        return 0
    if lines:
        print("\n".join(lines))
    return 0
