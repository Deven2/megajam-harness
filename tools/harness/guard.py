"""Tool-call policy shared by every vendor.

Runs on PreToolUse. It is a safety net for agent mistakes, not a security
boundary: git hooks and CI apply the same rules a second time.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from .common import contest_phase, find_marker_root, load_config

SHIP_HINT = "Use the ship skill, which runs `h ship`."
SHELL_WRAPPERS = {"bash", "sh", "zsh", "cmd", "powershell", "pwsh"}
RM_COMMANDS = {"rm", "remove-item", "ri", "del", "erase", "rd", "rmdir"}
READ_COMMANDS = {"cat", "type", "get-content", "gc", "head", "tail", "less", "more", "bat", "strings"}
PROTECTED_ROOTS = {
    ".", "./", "*", "/", "~", "..", "content", "source", "config", "art", "docs",
    ".git", ".github", "build", "plugins", "core", "knowledge", "tools", "devlog",
}
SECRET_ENV_NAMES = ("GITHUB_PAT", "GH_TOKEN", "GITHUB_TOKEN", "BUTLER_API_KEY", "TRELLO_TOKEN", "TRELLO_API_KEY")
SECRET_PATH = re.compile(
    r"(^|/)(\.env(\.(?!example$)[\w.-]+)?|credentials(\.json)?|\.credentials\.json|[^/]*\.(pem|pfx|p12|key)|id_rsa|id_ed25519|\.netrc)$",
    re.IGNORECASE,
)
BINARY_PATH = re.compile(r"\.(uasset|umap|ubulk|uexp|blend|fbx|glb|png|tga|exr|wav)$", re.IGNORECASE)
GENERATED_DIRS = ("Binaries/", "Intermediate/", "DerivedDataCache/", "Saved/")
RENDERED_PATHS = ("CLAUDE.md", "AGENTS.md", ".mcp.json")
RENDERED_DIRS = (".claude/", ".agents/", ".codex/", ".harness/")
RENDERED_EXCEPTIONS = {".claude/settings.local.json", ".harness/devlog-draft.md"}
PRE_JAM_BLOCKED_MCP = re.compile(r"^mcp__blender__(generate_3d|import_asset)$")
APPLY_PATCH_FILE = re.compile(r"^\*\*\* (?:Add|Update|Delete) File: (.+)$", re.MULTILINE)


@dataclass(frozen=True)
class Decision:
    rule: str
    reason: str


def split_segments(command: str) -> list[str]:
    """Split a shell command on control operators, respecting quotes."""
    segments: list[str] = []
    current: list[str] = []
    quote: str | None = None
    index = 0

    def flush() -> None:
        text = "".join(current).strip()
        if text:
            segments.append(text)
        current.clear()

    while index < len(command):
        char = command[index]
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            index += 1
        elif char in "\"'":
            quote = char
            current.append(char)
            index += 1
        elif command.startswith(("&&", "||"), index):
            flush()
            index += 2
        elif char in ";|&\n":
            flush()
            index += 1
        else:
            current.append(char)
            index += 1
    flush()
    return segments


def tokenize(segment: str) -> list[str]:
    lexer = shlex.shlex(segment, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = ""
    lexer.escape = ""
    try:
        return list(lexer)
    except ValueError:
        return segment.split()


def executable_name(token: str) -> str:
    name = re.split(r"[\\/]", token)[-1].lower()
    return re.sub(r"\.(exe|cmd|bat|ps1)$", "", name)


def strip_prefixes(tokens: list[str]) -> list[str]:
    index = 0
    while index < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[index]):
        index += 1
    return tokens[index:]


def parse_git(tokens: list[str]) -> tuple[str, list[str]]:
    args = tokens[1:]
    index = 0
    while index < len(args):
        token = args[index]
        if token in ("-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"):
            index += 2
        elif token.startswith("-"):
            index += 1
        else:
            return token, args[index + 1 :]
    return "", []


def check_git(tokens: list[str]) -> Decision | None:
    if "--no-verify" in tokens:
        return Decision("no-verify", "Bypassing git hooks is not allowed. Fix what the hook reported.")
    sub, args = parse_git(tokens)
    if sub == "push":
        return Decision("raw-push", f"Direct pushes are blocked. {SHIP_HINT}")
    if sub == "commit":
        return Decision("raw-commit", f"Direct commits are blocked so every commit follows the convention. {SHIP_HINT}")
    if sub == "merge" and "--abort" not in args:
        return Decision("raw-merge", f"Direct merges are blocked. {SHIP_HINT}")
    if sub in ("rebase", "filter-branch", "filter-repo", "update-ref"):
        return Decision("history-rewrite", "Git history must stay intact because Epic may request it (constraint C-03).")
    if sub == "reset" and "--hard" in args:
        return Decision("history-rewrite", "`git reset --hard` can destroy work. Ask a person first.")
    if sub == "clean" and any(re.match(r"^-[a-z]*f", a) for a in args):
        return Decision("destructive-git", "`git clean -f` deletes untracked work. Ask a person first.")
    if sub == "branch" and any(a in ("-D", "--delete", "-d") for a in args):
        return Decision("destructive-git", "Branch cleanup is handled by `h ship`.")
    if sub in ("checkout", "restore") and ("." in args or "*" in args):
        return Decision("destructive-git", "Discarding every local change is blocked. Name the exact file and confirm with the user.")
    if sub == "stash" and args[:1] and args[0] in ("drop", "clear"):
        return Decision("destructive-git", "Dropping stashes can lose work. Ask a person first.")
    if sub == "tag" and any(a in ("-d", "--delete", "-f", "--force") for a in args):
        return Decision("history-rewrite", "Tags are evidence of the pre-jam baseline. Do not move or delete them.")
    if sub == "reflog" and args[:1] == ["expire"]:
        return Decision("history-rewrite", "Reflog expiry is blocked.")
    if sub == "lfs" and args[:1] and args[0] in ("prune", "migrate"):
        return Decision("destructive-git", f"`git lfs {args[0]}` is blocked. Ask a person first.")
    if sub == "lfs" and args[:1] == ["unlock"] and "--force" in args:
        return Decision("destructive-git", "Forcing someone else's lock is blocked. Ask that person.")
    if sub == "config" and any("hookspath" in a.lower() for a in args):
        return Decision("disable-hooks", "Changing core.hooksPath is blocked.")
    return None


def check_gh(tokens: list[str]) -> Decision | None:
    args = tokens[1:]
    head = args[:2]
    if head[:1] in (["repo"], ["release"], ["secret"], ["variable"]) and head[1:] not in (["view"], ["list"]):
        return Decision("gh-admin", "Repository administration is reserved for people.")
    if head == ["pr", "merge"]:
        return Decision("gh-admin", f"Merges happen after CI. {SHIP_HINT}")
    if head == ["auth", "token"]:
        return Decision("secret-read", "Reading tokens is blocked.")
    if head[:1] == ["api"]:
        method_write = any(
            args[i] in ("-X", "--method") and i + 1 < len(args) and args[i + 1].upper() != "GET" for i in range(len(args))
        )
        field_write = any(a in ("-f", "-F", "--field", "--raw-field", "--input") for a in args)
        if method_write or field_write:
            return Decision("gh-admin", "Write calls through `gh api` are blocked.")
    return None


def check_butler(tokens: list[str]) -> Decision | None:
    if "push" not in tokens:
        return None
    channel = next((t for t in tokens if ":" in t and "/" in t and not t.startswith("-")), "")
    if "private" not in channel.lower():
        return Decision("jam-submit", "Agents may only upload to a channel with 'private' in its name (constraint C-05).")
    return None


def check_remove(tokens: list[str]) -> Decision | None:
    recursive = any(re.match(r"^(-[a-z]*r[a-z]*f?[a-z]*|-recurse|/s)$", t, re.IGNORECASE) for t in tokens[1:])
    if not recursive:
        return None
    for token in tokens[1:]:
        if token.startswith(("-", "/s", "/q")) and token not in ("/", "./"):
            continue
        normalized = token.replace("\\", "/").rstrip("/").lower() or "/"
        if normalized in PROTECTED_ROOTS or re.match(r"^[a-z]:$", normalized):
            return Decision("destructive-fs", f"Recursive delete of `{token}` is blocked.")
    return None


def check_secrets(tokens: list[str]) -> Decision | None:
    name = executable_name(tokens[0])
    if any(secret in token for token in tokens for secret in SECRET_ENV_NAMES):
        return Decision("secret-read", "Commands that touch secret variables are blocked.")
    if name in READ_COMMANDS and any(SECRET_PATH.search(t.replace("\\", "/")) for t in tokens[1:]):
        return Decision("secret-read", "Reading secret files is blocked.")
    if name == "printenv" or (name == "env" and len(tokens) == 1):
        return Decision("secret-read", "Dumping the environment is blocked.")
    if name in ("get-childitem", "gci", "dir", "ls") and any(t.lower().startswith("env:") for t in tokens[1:]):
        return Decision("secret-read", "Dumping the environment is blocked.")
    return None


def check_segment(segment: str) -> Decision | None:
    tokens = strip_prefixes(tokenize(segment))
    if not tokens:
        return None
    name = executable_name(tokens[0])

    if name == "h":
        if tokens[1:2] == ["mcp-headers"]:
            return Decision("secret-read", "`h mcp-headers` prints credentials and is reserved for the MCP client.")
        return None

    if name in SHELL_WRAPPERS:
        for index, token in enumerate(tokens[1:], start=1):
            if token.lower() in ("-c", "/c", "-command") and index + 1 < len(tokens):
                return check_command(" ".join(tokens[index + 1 :]))
        return None

    for check in (check_secrets,):
        decision = check(tokens)
        if decision:
            return decision

    if name == "git":
        return check_git(tokens)
    if name == "gh":
        return check_gh(tokens)
    if name == "butler":
        return check_butler(tokens)
    if name in RM_COMMANDS:
        return check_remove(tokens)
    if "$(" in segment or "`" in segment:
        if re.search(r"\bgit\b[^\"'|;&]*\bpush\b", segment):
            return Decision("raw-push", f"Direct pushes are blocked. {SHIP_HINT}")
    return None


def check_command(command: str) -> Decision | None:
    if re.search(r"itch\.io/jam/[^\s\"']*(submit|entries/new)", command, re.IGNORECASE):
        return Decision("jam-submit", "A person must submit the entry (rules section 17).")
    for segment in split_segments(command):
        decision = check_segment(segment)
        if decision:
            return decision
    return None


def relative_path(path: str, root: Path | None, cwd: Path) -> str:
    raw = path.replace("\\", "/")
    if root is None:
        return raw
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = cwd / candidate
    try:
        relative = os.path.relpath(candidate, root)
    except ValueError:
        return raw
    return relative.replace("\\", "/")


def check_path(rel: str, kind: str, phase: str, cfg: dict[str, Any]) -> Decision | None:
    if SECRET_PATH.search(rel):
        return Decision("secret-write", "Secret files are not edited by agents.")
    if kind != "game":
        return None
    if BINARY_PATH.search(rel):
        return Decision("binary-edit", "Binary assets cannot be edited as text. Use the Unreal or Blender operator.")
    if rel.startswith(GENERATED_DIRS):
        return Decision("generated-dir", "That folder is generated by the engine.")
    if (rel in RENDERED_PATHS or rel.startswith(RENDERED_DIRS)) and rel not in RENDERED_EXCEPTIONS:
        return Decision("rendered-file", "That file is generated by the harness. Change core/ in the harness and contribute it.")
    if phase == "pre-jam":
        codename = cfg["project"]["codename"]
        boilerplate = {f"Source/{codename}/{codename}{suffix}" for suffix in (".Build.cs", ".h", ".cpp")}
        if rel.startswith("Content/") or (rel.startswith("Art/") and rel != "Art/README.md"):
            return Decision("pre-jam-content", "Game content cannot exist before the jam starts (constraint C-01).")
        if rel.startswith(f"Source/{codename}/") and rel not in boilerplate:
            return Decision("pre-jam-content", "Gameplay code cannot exist before the jam starts (constraint C-01).")
    return None


def edited_paths(tool: str, tool_input: dict[str, Any]) -> list[str]:
    if tool == "apply_patch":
        return [match.strip() for match in APPLY_PATCH_FILE.findall(str(tool_input.get("command", "")))]
    for key in ("file_path", "path", "notebook_path"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return [value]
    return []


def evaluate(payload: dict[str, Any], cfg: dict[str, Any], now: datetime | None = None) -> Decision | None:
    tool = str(payload.get("tool_name", ""))
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        tool_input = {}
    cwd = Path(str(payload.get("cwd") or os.getcwd()))
    root, kind = find_marker_root(cwd)
    if kind == "unknown":
        return None
    phase = contest_phase(cfg, now)

    if tool.startswith("mcp__"):
        if phase == "pre-jam" and PRE_JAM_BLOCKED_MCP.match(tool):
            return Decision("pre-jam-content", "Assets cannot be created or imported before the jam starts (constraint C-01).")
        dumped = json.dumps(tool_input).lower()
        if "itch.io/jam/" in dumped and "submit" in dumped:
            return Decision("jam-submit", "A person must submit the entry (rules section 17).")
        return None

    paths = edited_paths(tool, tool_input)
    if paths:
        for path in paths:
            decision = check_path(relative_path(path, root, cwd), kind, phase, cfg)
            if decision:
                return decision
        return None

    command = tool_input.get("command")
    if isinstance(command, list):
        command = " ".join(str(part) for part in command)
    if isinstance(command, str):
        return check_command(command)
    return None


def hook_main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        decision = evaluate(payload, load_config())
    except Exception as exc:  # Fail open: git hooks and CI still apply the rules.
        print(f"[guard] internal error, allowing call: {exc}", file=sys.stderr)
        return 0
    if decision is None:
        return 0
    print(f"[guard:{decision.rule}] {decision.reason}", file=sys.stderr)
    return 2
