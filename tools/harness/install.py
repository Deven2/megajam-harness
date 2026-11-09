"""Installs the harness into a game repository and keeps it current."""

from __future__ import annotations

import json
import os
import shutil
import stat
import sys
from datetime import timezone
from pathlib import Path
from typing import Any

from .common import HARNESS_ROOT, HarnessError, LOCK_RELATIVE, git, git_out, gh_command, has_tool, load_config, now_utc, read_lock, repo_root, run, to_posix
from .doctor import collect_checks, print_checks
from .render import render


def make_lockable_files_writable(root: Path) -> None:
    """Git LFS marks lockable files read-only on checkout, which blocks saving from the editor."""
    for relative in git(["ls-files", "--", "*.uasset", "*.umap"], root).stdout.splitlines():
        path = root / relative
        if path.is_file():
            path.chmod(stat.S_IREAD | stat.S_IWRITE)


def use_github_cli_for_git(root: Path) -> None:
    """Git for Windows defaults to Credential Manager, which opens its own sign-in and may pick another account."""
    gh_path = shutil.which("gh")
    if not gh_path:
        return
    key = "credential.https://github.com.helper"
    git(["config", "--local", "--unset-all", key], root, check=False)
    git(["config", "--local", "--add", key, ""], root)
    git(["config", "--local", "--add", key, f'!"{to_posix(gh_path)}" auth git-credential'], root)


def set_private_identity(root: Path) -> None:
    """Commit with GitHub's private address, because the harness repository becomes public before submission."""
    if not has_tool("gh"):
        return
    result = run([*gh_command(), "api", "user", "--jq", ".login, .id"])
    fields = result.stdout.split()
    if result.returncode != 0 or len(fields) != 2:
        return
    login, user_id = fields
    git(["config", "--local", "user.email", f"{user_id}+{login}@users.noreply.github.com"], root)
    if not git(["config", "user.name"], root, check=False).stdout.strip():
        git(["config", "--local", "user.name", login], root)


def configure_repo(root: Path, role: str | None = None) -> None:
    settings = {
        "core.hooksPath": ".githooks",
        "core.longpaths": "true",
        "pull.ff": "only",
        "lfs.setlockablereadonly": "false",
    }
    for key, value in settings.items():
        git(["config", "--local", key, value], root)
    use_github_cli_for_git(root)
    set_private_identity(root)
    make_lockable_files_writable(root)
    if role == "dev":
        git(["config", "--local", "lfs.fetchexclude", "Art/Source/**"], root)
    elif role == "art":
        git(["config", "--local", "--unset-all", "lfs.fetchexclude"], root, check=False)


def write_shims(game_root: Path) -> None:
    folder = game_root / ".harness"
    folder.mkdir(parents=True, exist_ok=True)
    python = Path(sys.executable).resolve()
    entry = HARNESS_ROOT / "tools" / "h.py"
    (folder / "python.txt").write_text(to_posix(python), encoding="utf-8", newline="\n")
    (folder / "h").write_text(
        f'#!/bin/sh\nPYTHONUTF8=1 exec "{to_posix(python)}" "{to_posix(entry)}" "$@"\n',
        encoding="utf-8",
        newline="\n",
    )
    (folder / "h.cmd").write_text(
        f'@echo off\r\nset PYTHONUTF8=1\r\n"{python}" "{entry}" %*\r\n',
        encoding="utf-8",
        newline="",
    )


def write_lock(game_root: Path, vendor: str, role: str) -> None:
    lock = {
        "vendor": vendor,
        "role": role,
        "harness_path": to_posix(HARNESS_ROOT),
        "harness_sha": git(["rev-parse", "HEAD"], HARNESS_ROOT, check=False).stdout.strip(),
        "rendered_utc": now_utc().astimezone(timezone.utc).isoformat(),
    }
    (game_root / LOCK_RELATIVE).write_text(json.dumps(lock, indent=2) + "\n", encoding="utf-8", newline="\n")


def set_user_env(name: str, value: str) -> None:
    import winreg

    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def clone_game(destination: Path, cfg: dict[str, Any]) -> None:
    project = cfg["project"]
    if project["owner"] == "REPLACE_OWNER":
        raise HarnessError("Set project.owner in harness.toml before cloning.")
    url = f"https://github.com/{project['owner']}/{project['game_repo']}.git"
    destination.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "-c", "lfs.setlockablereadonly=false", "clone", url, str(destination)], check=True, timeout=3600)


def install(vendor: str, game: Path, role: str, clone: bool) -> int:
    cfg = load_config()
    game = game.resolve()
    if not game.exists():
        if not clone:
            raise HarnessError(f"{game} does not exist. Pass --clone to clone the game repository there.")
        clone_game(game, cfg)
    root = repo_root(game)
    configure_repo(root, role)
    configure_repo(HARNESS_ROOT)
    run(["git", "lfs", "install", "--local", "--skip-repo"], cwd=root)
    write_shims(root)
    written = render(vendor, root)
    write_lock(root, vendor, role)

    next_steps: list[str] = []
    if vendor == "codex":
        if has_tool("gh"):
            token = run([*gh_command(), "auth", "token"]).stdout.strip()
            if token and os.name == "nt":
                set_user_env("GITHUB_PAT", token)
                next_steps.append("GITHUB_PAT was saved in your user environment. Restart the terminal.")
        next_steps.append("Open Codex in the game folder and run /hooks once to trust the harness hooks.")
    next_steps.append("Inside the agent, connect Trello through /mcp (browser sign-in).")
    next_steps.append("Open the Unreal project before starting your AI tool. Unreal MCP starts with the editor.")
    next_steps.append("In Blender: run `uvx mcp-for-blender install-addon` and click Start MCP Server.")

    print(f"Installed for {vendor} in {root} ({len(written)} files generated).\n")
    checks = collect_checks(vendor, root, role)
    print_checks(checks)
    print("\nNext steps:")
    for step in next_steps:
        print(f"  - {step}")
    return 0


def rerender(game_root: Path) -> int:
    lock = read_lock(game_root)
    if not lock:
        raise HarnessError("This repository has no harness installed. Run `h install` first.")
    write_shims(game_root)
    written = render(lock["vendor"], game_root)
    write_lock(game_root, lock["vendor"], lock.get("role", "dev"))
    print(f"Rendered {len(written)} files for {lock['vendor']}.")
    return 0


def update(game_root: Path) -> int:
    cfg = load_config()
    lock = read_lock(game_root)
    branch = cfg["branches"]["harness_track"]
    before = git_out(["rev-parse", "HEAD"], HARNESS_ROOT)
    if git(["status", "--porcelain"], HARNESS_ROOT).stdout.strip():
        raise HarnessError("The harness clone has local changes. Contribute or discard them first.")
    git(["fetch", "origin", branch], HARNESS_ROOT, timeout=120)
    git(["switch", branch], HARNESS_ROOT)
    git(["merge", "--ff-only", f"origin/{branch}"], HARNESS_ROOT)
    after = git_out(["rev-parse", "HEAD"], HARNESS_ROOT)
    rerender(game_root)
    hooks_changed = bool(git(["diff", "--name-only", before, after, "--", "core/hooks", "vendors"], HARNESS_ROOT).stdout.strip())
    print(f"Harness updated: {before[:8]} -> {after[:8]}.")
    if lock.get("vendor") == "codex" and hooks_changed:
        print("Hooks changed. Run /hooks in Codex to trust them again.")
    print("Restart the agent session to load the new version.")
    return 0
