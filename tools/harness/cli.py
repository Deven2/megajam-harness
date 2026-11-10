"""Argument parsing. Commands import their modules lazily so hooks stay fast."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from .common import HarnessError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="h", description="MegaJam harness tools")
    commands = parser.add_subparsers(dest="command", required=True)

    install = commands.add_parser("install", help="Install the harness into a game repository")
    install.add_argument("--vendor", choices=["claude", "codex"], required=True)
    install.add_argument("--game", required=True, help="Path of the game repository")
    install.add_argument("--role", choices=["dev", "art"], default="dev")
    install.add_argument("--clone", action="store_true", help="Clone the game repository if it is missing")

    commands.add_parser("update", help="Pull the latest harness and generate its files again")
    commands.add_parser("render", help="Generate the vendor files again")
    commands.add_parser("sync", help="Return to dev with the team's latest work")
    commands.add_parser("status", help="Print the session status block")

    doctor = commands.add_parser("doctor", help="Check this machine")
    doctor.add_argument("--vendor", choices=["claude", "codex"])
    doctor.add_argument("--role", choices=["dev", "art"], default="dev")
    doctor.add_argument("--live", action="store_true", help="Also probe the Unreal and Blender MCP ports")
    doctor.add_argument("--json", action="store_true")

    def add_change_arguments(sub: argparse.ArgumentParser) -> None:
        sub.add_argument("--type", choices=["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "art", "audio", "level"])
        sub.add_argument("--scope")
        sub.add_argument("--summary")
        sub.add_argument("--body")
        sub.add_argument("--note", help="One line for the devlog")
        sub.add_argument("--card", help="Trello card URL")
        sub.add_argument("--paths", nargs="*")
        sub.add_argument("--base")
        sub.add_argument("--keep-mine", action="store_true")
        sub.add_argument("--no-merge", action="store_true")
        sub.add_argument("--ci-down", metavar="REASON",
                         help="CI is broken, not the code: merge without waiting for checks and record why on the pull request")

    add_change_arguments(commands.add_parser("ship", help="Commit, open a PR, wait for CI and merge"))
    contribute = commands.add_parser("contribute", help="Validate, run evals and ship a harness change")
    add_change_arguments(contribute)
    contribute.add_argument("--skip-evals", action="store_true")
    contribute.add_argument("--blocker", metavar="REASON", help="During the jam: what this change unblocks. Required while the harness is frozen.")

    release = commands.add_parser("release", help="Release flow")
    release.add_argument("action", choices=["start", "finish"])
    release.add_argument("version")
    commands.add_parser("backmerge", help="Merge main back into dev after a hotfix")

    devlog = commands.add_parser("devlog", help="Devlog tools")
    devlog_commands = devlog.add_subparsers(dest="devlog_command", required=True)
    collect = devlog_commands.add_parser("collect")
    collect.add_argument("--since")
    publish = devlog_commands.add_parser("publish")
    publish.add_argument("--title", required=True)
    publish.add_argument("--draft", default=".harness/devlog-draft.md")
    publish.add_argument("--media", nargs="*", default=[])

    ledger = commands.add_parser("ledger", help="Asset ledger")
    ledger_commands = ledger.add_subparsers(dest="ledger_command", required=True)
    add = ledger_commands.add_parser("add")
    add.add_argument("--kind", choices=["sourced", "ai-generated", "original"], required=True)
    add.add_argument("--origin", required=True)
    add.add_argument("--reference", default="")
    add.add_argument("--license", required=True)
    add.add_argument("--commercial", choices=["yes", "no", "unknown"], default="unknown",
                     help="Whether the license also allows a commercial release")
    add.add_argument("--path", required=True)
    add.add_argument("--notes", default="")
    ledger_commands.add_parser("check")

    submission = commands.add_parser("submission-check", help="Print the submission checklist")
    submission.add_argument("--zip")

    commands.add_parser("validate", help="Validate core/ and both vendor outputs")
    commands.add_parser("catalog", help="Regenerate docs/catalog.md")
    evaluate = commands.add_parser("eval", help="Run behavioral evals")
    evaluate.add_argument("--vendor", choices=["claude", "codex"], required=True)
    evaluate.add_argument("--cases", default="changed", help="changed, all, or one case name")

    hook = commands.add_parser("hook", help="Internal: vendor hook entry points")
    hook.add_argument("action", choices=["session-start", "guard", "ledger"])

    headers = commands.add_parser("mcp-headers", help="Internal: credentials for the MCP client")
    headers.add_argument("server", choices=["github"])
    return parser


def change_options(args: argparse.Namespace) -> dict:
    return {key: getattr(args, key) for key in ("type", "scope", "summary", "body", "note", "card", "paths", "base", "keep_mine", "no_merge", "ci_down")}


def dispatch(args: argparse.Namespace) -> int:
    start = Path.cwd()
    name = args.command

    if name == "hook":
        if args.action == "guard":
            from .guard import hook_main
        elif args.action == "session-start":
            from .session import hook_main
        else:
            from .records import hook_ledger as hook_main
        return hook_main()

    if name == "mcp-headers":
        import json

        from .common import gh_command, run

        token = run([*gh_command(), "auth", "token"], check=True).stdout.strip()
        print(json.dumps({"Authorization": f"Bearer {token}"}))
        return 0

    if name in ("install", "update", "render"):
        from .common import repo_root
        from .install import install, rerender, update

        if name == "install":
            return install(args.vendor, Path(args.game), args.role, args.clone)
        return update(repo_root(start)) if name == "update" else rerender(repo_root(start))

    if name == "doctor":
        from .common import find_marker_root, read_lock
        from .doctor import doctor

        root, kind = find_marker_root(start)
        game = root if kind == "game" else None
        vendor = args.vendor or (read_lock(game).get("vendor") if game else None)
        return doctor(vendor, game, args.role, args.live, args.json)

    if name == "status":
        from .session import status_lines

        print("\n".join(status_lines(start)))
        return 0

    if name in ("ship", "sync", "release", "backmerge"):
        from . import ship as flows

        if name == "ship":
            return flows.ship(change_options(args), start)
        if name == "sync":
            return flows.sync(start)
        if name == "backmerge":
            return flows.backmerge(start)
        action = flows.release_start if args.action == "start" else flows.release_finish
        return action(args.version, start)

    if name == "devlog":
        from . import records

        if args.devlog_command == "collect":
            return records.devlog_collect(args.since, start)
        return records.devlog_publish(args.title, Path(args.draft), [Path(item) for item in args.media])

    if name == "ledger":
        from . import records

        if args.ledger_command == "check":
            return records.ledger_check(start)
        return records.ledger_add(args.kind, args.origin, args.reference, args.license, args.commercial, args.path, args.notes, start)

    if name == "submission-check":
        from .records import submission_check

        return submission_check(Path(args.zip) if args.zip else None, start)

    from . import quality

    if name == "validate":
        return quality.validate_command()
    if name == "catalog":
        return quality.write_catalog()
    if name == "eval":
        return quality.run_evals(args.vendor, args.cases)
    if name == "contribute":
        from .common import find_marker_root, read_lock

        root, kind = find_marker_root(start)
        vendor = (read_lock(root).get("vendor") if kind == "game" and root else None) or os.environ.get("HARNESS_VENDOR", "claude")
        return quality.contribute(change_options(args), vendor, args.skip_evals, args.blocker)
    raise HarnessError(f"Unknown command: {name}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return dispatch(args)
    except HarnessError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
