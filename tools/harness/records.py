"""Devlog, asset ledger and submission checklist. None of these spend model tokens."""

from __future__ import annotations

import csv
import json
import re
import shutil
import sys
import urllib.error
import urllib.request
from datetime import timezone
from pathlib import Path
from typing import Any

from .common import (
    HARNESS_ROOT,
    HarnessError,
    contest_phase,
    find_marker_root,
    format_delta,
    git,
    load_config,
    now_utc,
    parse_utc,
    read_toml,
    repo_root,
    slugify,
)
from .ship import SHIP_ENV

LEDGER_RELATIVE = Path("docs") / "compliance" / "assets-ledger.csv"
LEDGER_HEADER = ["added_utc", "kind", "origin", "reference", "license", "commercial_use", "path", "notes"]
AI_USAGE_RELATIVE = Path("docs") / "compliance" / "ai-usage.md"
DEVLOG_DIR = HARNESS_ROOT / "devlog"
DEVLOG_TRAILER = re.compile(r"^Devlog:\s*(.+)$", re.MULTILINE)


# --- Devlog ---------------------------------------------------------------

def commits_since(root: Path, since: str, branch: str) -> list[dict[str, Any]]:
    fmt = "%h%x1f%an%x1f%aI%x1f%s%x1f%b%x1e"
    reference = f"origin/{branch}" if git(["rev-parse", "--verify", "--quiet", f"origin/{branch}"], root, check=False).returncode == 0 else "HEAD"
    output = git(["log", reference, f"--since={since}", "--no-merges", f"--format={fmt}"], root).stdout
    commits = []
    for record in filter(str.strip, output.split("\x1e")):
        sha, author, date, subject, body = record.strip().split("\x1f")
        commits.append({"sha": sha, "author": author, "date": date, "subject": subject, "notes": DEVLOG_TRAILER.findall(body)})
    return commits


def last_entry_date() -> str:
    entries = sorted((DEVLOG_DIR / "entries").glob("*.md"))
    return entries[-1].name[:10] if entries else "2026-11-08"


def devlog_collect(since: str | None, start: Path) -> int:
    cfg = load_config()
    moment = since or last_entry_date()
    branch = cfg["branches"]["integration"]
    data = {
        "since": moment,
        "game_commits": commits_since(repo_root(start), moment, branch),
        "harness_commits": commits_since(HARNESS_ROOT, moment, branch),
        "phase": contest_phase(cfg),
    }
    print(json.dumps(data, indent=2))
    return 0


def rebuild_devlog_index() -> None:
    entries = sorted((DEVLOG_DIR / "entries").glob("*.md"), reverse=True)
    lines = [
        "# Devlog",
        "",
        "How a three-person team built a game for the 2026 Epic AI MegaJam with a multi-agent harness.",
        "",
    ]
    for entry in entries:
        heading = entry.read_text(encoding="utf-8").splitlines()[0].lstrip("# ").strip()
        lines.append(f"- **{entry.name[:10]}** [{heading}](entries/{entry.name})")
    (DEVLOG_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def devlog_publish(title: str, draft: Path, media: list[Path]) -> int:
    cfg = load_config()
    if not draft.is_file():
        raise HarnessError(f"Draft not found: {draft}")
    branch = cfg["branches"]["harness_track"]
    if git(["remote", "get-url", "origin"], HARNESS_ROOT, check=False).returncode == 0:
        git(["pull", "--ff-only", "origin", branch], HARNESS_ROOT, env=SHIP_ENV, timeout=120)
    date = now_utc().astimezone(timezone.utc).strftime("%Y-%m-%d")
    target = DEVLOG_DIR / "entries" / f"{date}-{slugify(title)}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    body = draft.read_text(encoding="utf-8").lstrip()
    if not body.startswith("# "):
        body = f"# {title}\n\n{body}"
    target.write_text(body, encoding="utf-8", newline="\n")
    media_dir = DEVLOG_DIR / "media"
    media_dir.mkdir(parents=True, exist_ok=True)
    for item in media:
        shutil.copy2(item, media_dir / f"{date}-{item.name}")
    rebuild_devlog_index()
    git(["add", "--", "devlog"], HARNESS_ROOT)
    git(["commit", "-m", f"docs(devlog): {title}"], HARNESS_ROOT, env={**SHIP_ENV, "HARNESS_ALLOW_PROTECTED": "1"})
    pushed = False
    if git(["remote", "get-url", "origin"], HARNESS_ROOT, check=False).returncode == 0:
        git(["push", "origin", branch], HARNESS_ROOT, env={**SHIP_ENV, "HARNESS_ALLOW_PROTECTED": "1"}, timeout=120)
        pushed = True
    draft.unlink(missing_ok=True)
    print(json.dumps({"status": "published", "entry": str(target), "pushed": pushed}))
    return 0


# --- Asset ledger ----------------------------------------------------------

def append_ledger(root: Path, row: dict[str, str]) -> None:
    path = root / LEDGER_RELATIVE
    path.parent.mkdir(parents=True, exist_ok=True)
    is_new = not path.is_file()
    if not is_new:
        with path.open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            existing = list(reader)
            header = reader.fieldnames or []
        if header != LEDGER_HEADER:  # An older ledger lacks a column: rewrite it with the current header.
            with path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=LEDGER_HEADER, lineterminator="\n")
                writer.writeheader()
                for old in existing:
                    writer.writerow({key: old.get(key) or ("unknown" if key == "commercial_use" else "") for key in LEDGER_HEADER})
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LEDGER_HEADER, lineterminator="\n")
        if is_new:
            writer.writeheader()
        writer.writerow(row)


def ledger_add(kind: str, origin: str, reference: str, license_name: str, commercial: str, asset_path: str, notes: str, start: Path) -> int:
    root = repo_root(start)
    append_ledger(root, {
        "added_utc": now_utc().isoformat(timespec="seconds"),
        "kind": kind, "origin": origin, "reference": reference,
        "license": license_name, "commercial_use": commercial, "path": asset_path, "notes": notes,
    })
    print(json.dumps({"status": "recorded", "path": asset_path, "kind": kind}))
    return 0


def read_ledger(root: Path) -> list[dict[str, str]]:
    path = root / LEDGER_RELATIVE
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def label(row: dict[str, str]) -> str:
    return row.get("path") or row.get("reference") or row.get("origin") or "?"


def not_commercial(rows: list[dict[str, str]]) -> list[str]:
    """Assets the jam may use but a commercial release could not, without a new license."""
    return [label(row) for row in rows if (row.get("commercial_use") or "unknown").strip().lower() != "yes"]


def ledger_check(start: Path) -> int:
    rows = read_ledger(repo_root(start))
    unknown = [row for row in rows if row["license"].strip().upper() in ("", "UNKNOWN")]
    print(json.dumps({
        "total": len(rows),
        "sourced": sum(row["kind"] == "sourced" for row in rows),
        "ai_generated": sum(row["kind"] == "ai-generated" for row in rows),
        "missing_license": [label(row) for row in unknown],
        "not_cleared_for_commercial_use": not_commercial(rows),
    }, indent=2))
    return 1 if unknown else 0


def hook_ledger() -> int:
    """PostToolUse: record assets the moment an agent creates or imports them."""
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        tool = str(payload.get("tool_name", ""))
        kind = {"import_asset": "sourced", "generate_3d": "ai-generated"}.get(tool.rsplit("__", 1)[-1])
        root, workspace = find_marker_root(Path(str(payload.get("cwd") or Path.cwd())))
        if kind is None or workspace != "game" or root is None:
            return 0
        tool_input = payload.get("tool_input") or {}
        origin = str(tool_input.get("provider") or tool_input.get("source") or "blender-mcp")
        append_ledger(root, {
            "added_utc": now_utc().isoformat(timespec="seconds"),
            "kind": kind,
            "origin": origin,
            "reference": json.dumps(tool_input, ensure_ascii=False)[:300],
            "license": "CC0" if "polyhaven" in origin.lower().replace(" ", "") else "UNKNOWN",
            "commercial_use": "yes" if "polyhaven" in origin.lower().replace(" ", "") else "unknown",
            "path": "",
            "notes": "Recorded automatically. Fill in the license and final Content path.",
        })
        print(f"[ledger] Recorded a {kind} asset in {LEDGER_RELATIVE.as_posix()}. Confirm its license before shipping.")
    except Exception as exc:  # Recording must never break the tool call.
        print(f"[ledger] could not record the asset: {exc}", file=sys.stderr)
    return 0


# --- Submission checklist ---------------------------------------------------

def read_tools(root: Path) -> list[str]:
    """Tool names from the Tools table in ai-usage.md, pasted into the form's "Tools you used" field."""
    path = root / AI_USAGE_RELATIVE
    if not path.is_file():
        return []
    tools, in_section = [], False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_section = line.strip() == "## Tools"
            continue
        if in_section and line.startswith("|"):
            cell = line.strip().strip("|").split("|")[0].strip()
            if cell and cell != "Tool" and not set(cell) <= set("-: "):
                tools.append(cell)
    return tools


def normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def tools_missing_from_list(rows: list[dict[str, str]], tools: list[str]) -> list[str]:
    """Origins of AI-generated assets that the tools list does not mention."""
    names = [normalize(tool) for tool in tools if normalize(tool)]
    origins = sorted({row["origin"].strip() for row in rows if row.get("kind") == "ai-generated" and (row.get("origin") or "").strip()})
    return [origin for origin in origins if not any(normalize(origin) in name or name in normalize(origin) for name in names)]


def public_url_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(urllib.request.Request(url, method="GET"), timeout=10) as response:
            return response.status == 200
    except (urllib.error.URLError, ValueError):
        return False


def submission_check(zip_path: Path | None, start: Path) -> int:
    root = repo_root(start)
    cfg = load_config()
    data = read_toml(root / "docs" / "compliance" / "submission.toml")
    now = now_utc()
    deadline = parse_utc(cfg["contest"]["deadline_utc"])
    results: list[tuple[str, bool, str]] = []

    def add(name: str, ok: bool, detail: str = "") -> None:
        results.append((name, ok, detail))

    team, game = data.get("team_name", "TBD"), data.get("game_name", "TBD")
    add("team and game names set", "TBD" not in (team, game), f"{team} / {game}")
    add("video link set", bool(data.get("video_url")), data.get("video_url", ""))
    add("video reviewed: 30-60 s, 1080p or higher, gameplay first", bool(data.get("video_reviewed")))
    devlog_url = data.get("devlog_url", "")
    add("devlog publicly reachable", bool(devlog_url) and public_url_ok(devlog_url), devlog_url)
    add("pre-jam declaration completed", bool(data.get("declaration_complete")))
    add("content reviewed: Teen, English only, no third-party logos", bool(data.get("content_reviewed")))
    add("Theme clearly demonstrated", bool(data.get("theme_reviewed")))
    add("pre-jam-baseline tag exists", git(["rev-parse", "--verify", "--quiet", "pre-jam-baseline"], root, check=False).returncode == 0)
    rows = read_ledger(root)
    unknown = [row for row in rows if row["license"].strip().upper() in ("", "UNKNOWN")]
    add("every ledger entry has a license", not unknown, f"{len(unknown)} missing of {len(rows)}")
    tools = read_tools(root)
    missing_tools = tools_missing_from_list(rows, tools)
    add("tools list covers every AI asset source", bool(tools) and not missing_tools,
        f"add to {AI_USAGE_RELATIVE.as_posix()}: {', '.join(missing_tools)}" if missing_tools else f"{len(tools)} tools")
    if zip_path:
        expected = f"{team}_{game}.zip".replace(" ", "")
        add("zip name follows TeamName_GameName", zip_path.name == expected, f"expected {expected}, found {zip_path.name}")
        exists = zip_path.is_file()
        size = zip_path.stat().st_size / 2**30 if exists else 0
        limit = cfg["limits"]["itch_browser_upload_gib"]
        add("zip exists", exists, f"{size:.2f} GiB")
        if size > limit:
            add("zip fits browser upload", False, f"Above {limit} GiB: upload it with butler or Blendo Itch Uploader.")
    else:
        add("zip checked", False, "Run again with --zip <path>.")

    print(f"Time left: {format_delta(deadline - now)} (phase {contest_phase(cfg, now)})\n")
    for name, ok, detail in results:
        print(f"[{'x' if ok else ' '}] {name}" + (f"  ({detail})" if detail else ""))
    if tools:
        print(f"\nTools you used (paste into the form): {', '.join(tools)}")
        print("Partner prizes read this field: list Rodin for the Hyper3D pool, NvRTX for the NVIDIA RTX Award.")
    blocked = not_commercial(rows)
    if blocked:
        print(f"\nNote: {len(blocked)} assets are fine for the jam but not cleared for commercial use: {', '.join(blocked)}")
    print("\nA person must complete the itch.io form and press submit (rules section 17).")
    return 0 if all(ok for _, ok, _ in results) else 1
