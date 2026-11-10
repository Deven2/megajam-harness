"""The single write path to shared branches: stage, commit, PR, CI, merge.

Every outcome is a JSON object so an agent can explain it to the person
asking, in that person's language.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from pathlib import Path
from typing import Any

from .common import (
    BINARY_EXTENSIONS,
    HARNESS_ROOT,
    LOCKABLE_EXTENSIONS,
    contest_phase,
    HarnessError,
    gh_command,
    git,
    git_out,
    has_tool,
    load_config,
    read_lock,
    repo_root,
    run,
    slugify,
)

COMMIT_TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "art", "audio", "level")
SHIP_ENV = {"HARNESS_SHIP": "1", "PYTHONUTF8": "1"}
EXIT_CODES = {
    "shipped": 0, "pr-open": 0, "pushed": 0, "nothing-to-ship": 0,
    "binary-conflict": 3, "locked-by-other": 3, "text-conflict": 3,
    "close-editor": 4, "checks-failed": 5, "checks-missing": 5, "policy-rejected": 6, "harness-frozen": 7,
}
CONTENT_PREFIXES = ("Content/", "Source/", "Config/", "Plugins/")
CHECK_START_ATTEMPTS = 12  # About two minutes for GitHub to register the first check.


def freeze_message(cfg: dict[str, Any], blocker: str | None, now: Any = None) -> str | None:
    """The harness is frozen from the jam start: only blockers with no simple workaround may change it."""
    if contest_phase(cfg, now) not in ("jam", "freeze") or (blocker or "").strip():
        return None
    return ("The harness is frozen during the jam (docs/adr/0007-harness-freeze.md). Use a workaround and note the idea "
            "for the devlog. If this blocks the game and no simple workaround exists, run again with --blocker \"<what it blocks>\".")



class Stop(Exception):
    def __init__(self, status: str, **details: Any) -> None:
        super().__init__(status)
        self.status = status
        self.details = details


def editor_running() -> bool:
    forced = os.environ.get("HARNESS_ASSUME_EDITOR")
    if forced is not None:
        return forced == "1"
    if os.name != "nt":
        return False
    output = run(["tasklist", "/FI", "IMAGENAME eq UnrealEditor.exe", "/NH"]).stdout
    return "UnrealEditor.exe" in output


def is_binary(path: str) -> bool:
    return Path(path).suffix.lower() in BINARY_EXTENSIONS


def is_lockable(path: str) -> bool:
    return Path(path).suffix.lower() in LOCKABLE_EXTENSIONS


def gh_available() -> bool:
    return bool(os.environ.get("HARNESS_GH")) or has_tool("gh")


class ShipFlow:
    def __init__(self, root: Path, cfg: dict[str, Any], options: dict[str, Any]) -> None:
        self.root = root
        self.cfg = cfg
        self.options = options
        self.integration = cfg["branches"]["integration"]
        self.production = cfg["branches"]["production"]
        self.protected = {self.integration, self.production}
        self.base = options.get("base") or self.integration
        self.branch = git_out(["branch", "--show-current"], root)
        self.has_origin = bool(git(["remote", "get-url", "origin"], root, check=False).stdout.strip())
        self.acquired_locks: list[str] = []
        self.staged: list[tuple[str, str]] = []

    def run(self) -> dict[str, Any]:
        try:
            result = self._run()
        except Stop as stop:
            result = {"status": stop.status, **stop.details}
        result.setdefault("branch", self.branch)
        if self.acquired_locks and result["status"] != "shipped":
            result["locks_held"] = self.acquired_locks
        return result

    def _subject(self) -> str:
        kind, scope, summary = (self.options.get(key) for key in ("type", "scope", "summary"))
        if not (kind and scope and summary):
            raise HarnessError("--type, --scope and --summary are required when there are changes to ship.")
        return f"{kind}({scope}): {summary}"

    def _run(self) -> dict[str, Any]:
        if self.root.resolve() == HARNESS_ROOT.resolve():
            frozen = freeze_message(self.cfg, self.options.get("blocker"))
            if frozen:
                return {"status": "harness-frozen", "message": frozen}
        git_dir = Path(git_out(["rev-parse", "--absolute-git-dir"], self.root))
        if (git_dir / "MERGE_HEAD").exists():
            self._finish_merge()
        elif git(["status", "--porcelain"], self.root).stdout.strip():
            self._prepare_branch()
            self._stage()
            if not self.staged:
                return {"status": "nothing-to-ship"}
            self._check_binaries()
            self._commit()
        elif self.branch in self.protected or not self._ahead_of_base():
            return {"status": "nothing-to-ship"}
        self._integrate_base()
        if not self.has_origin:
            return {"status": "pushed", "note": "No origin remote is configured, so nothing left this machine."}
        git(["push", "-u", "origin", self.branch], self.root, env=SHIP_ENV, timeout=3600)
        if not gh_available():
            return {"status": "pushed", "note": "GitHub CLI is not available, so no pull request was opened."}
        return self._pull_request()

    def _ahead_of_base(self) -> bool:
        reference = f"origin/{self.base}" if self.has_origin else self.base
        count = git(["rev-list", "--count", f"{reference}..HEAD"], self.root, check=False).stdout.strip()
        return count.isdigit() and int(count) > 0

    def _prepare_branch(self) -> None:
        if self.branch not in self.protected:
            return
        subject = self._subject()
        prefix = "hotfix" if self.base == self.production else "feature"
        base_name = f"{prefix}/{slugify(self.options['scope'], 16)}-{slugify(self.options['summary'])}"
        name = base_name
        suffix = 2
        while git(["rev-parse", "--verify", "--quiet", f"refs/heads/{name}"], self.root, check=False).returncode == 0:
            name = f"{base_name}-{suffix}"
            suffix += 1
        git(["switch", "-c", name], self.root)
        self.branch = name
        _ = subject

    def _stage(self) -> None:
        paths = self.options.get("paths") or []
        git(["add", "-A", "--", *(paths or ["."])], self.root)
        output = git(["diff", "--cached", "--name-status", "--no-renames"], self.root).stdout
        self.staged = [(line.split("\t", 1)[0], line.split("\t", 1)[1]) for line in output.splitlines() if "\t" in line]

    def _check_binaries(self) -> None:
        if not self.has_origin:
            return
        git(["fetch", "origin", self.base], self.root, timeout=600)
        merge_base = git_out(["merge-base", "HEAD", f"origin/{self.base}"], self.root)
        upstream = set(git(["diff", "--name-only", merge_base, f"origin/{self.base}"], self.root).stdout.splitlines())
        conflicts = [path for _, path in self.staged if is_binary(path) and path in upstream]
        if conflicts and not self.options.get("keep_mine"):
            git(["reset", "-q"], self.root)
            raise Stop("binary-conflict", files=conflicts, message="Someone else changed these binary files. Ask the user which version to keep, then rerun with --keep-mine or discard the local change.")
        self._acquire_locks()

    def _acquire_locks(self) -> None:
        modified = [path for status, path in self.staged if status != "A" and is_lockable(path)]
        if not modified:
            return
        verify = run(["git", "lfs", "locks", "--verify", "--json"], cwd=self.root, timeout=60)
        if verify.returncode != 0:
            return  # The remote has no lock API, for example a local test remote.
        locks = json.loads(verify.stdout or "{}")
        theirs = {item["path"]: item.get("owner", {}).get("name", "someone") for item in locks.get("theirs", [])}
        ours = {item["path"] for item in locks.get("ours", [])}
        blocked = {path: theirs[path] for path in modified if path in theirs}
        if blocked:
            git(["reset", "-q"], self.root)
            raise Stop("locked-by-other", files=blocked, message="Another teammate holds these locks. Ask them to finish first.")
        for path in modified:
            if path not in ours and run(["git", "lfs", "lock", path], cwd=self.root, timeout=60).returncode == 0:
                self.acquired_locks.append(path)

    def _commit(self) -> None:
        trailers = [f"AI-Assisted-By: {read_lock(self.root).get('vendor', 'none')}"]
        if self.options.get("card"):
            trailers.append(f"Card: {self.options['card']}")
        if self.options.get("note"):
            trailers.append(f"Devlog: {self.options['note']}")
        body = self.options.get("body") or ""
        message = "\n\n".join(part for part in (self._subject(), body, "\n".join(trailers)) if part) + "\n"
        result = run(["git", "commit", "-F", "-"], cwd=self.root, input_text=message, env=SHIP_ENV)
        if result.returncode != 0:
            git(["reset", "-q"], self.root)
            raise Stop("policy-rejected", output=(result.stdout + result.stderr).strip())

    def _finish_merge(self) -> None:
        git(["add", "-A"], self.root)
        result = run(["git", "commit", "--no-edit"], cwd=self.root, env=SHIP_ENV)
        if result.returncode != 0:
            raise Stop("policy-rejected", output=(result.stdout + result.stderr).strip())

    def _integrate_base(self) -> None:
        if not self.has_origin:
            return
        git(["fetch", "origin", self.base], self.root, timeout=600)
        reference = f"origin/{self.base}"
        if git(["merge-base", "--is-ancestor", reference, "HEAD"], self.root, check=False).returncode == 0:
            return
        incoming = git(["diff", "--name-only", f"HEAD...{reference}"], self.root).stdout.splitlines()
        if editor_running() and any(path.startswith(CONTENT_PREFIXES) for path in incoming):
            raise Stop("close-editor", files=incoming[:30], message="Close Unreal Editor so incoming files can be written, then ship again.")
        merged = run(["git", "merge", "--no-edit", reference], cwd=self.root, env=SHIP_ENV)
        if merged.returncode == 0:
            return
        conflicted = git(["diff", "--name-only", "--diff-filter=U"], self.root).stdout.splitlines()
        binaries = [path for path in conflicted if is_binary(path)]
        if binaries and not self.options.get("keep_mine"):
            git(["merge", "--abort"], self.root)
            raise Stop("binary-conflict", files=binaries, message="Binary files conflict with the team's version. Ask the user which version to keep.")
        for path in binaries:
            git(["checkout", "--ours", "--", path], self.root)
            git(["add", "--", path], self.root)
        remaining = [path for path in conflicted if path not in binaries]
        if remaining:
            raise Stop("text-conflict", files=remaining, message="Resolve the conflict markers in these files, then run ship again.")
        self._finish_merge()

    def _pull_request(self) -> dict[str, Any]:
        gh = gh_command()
        subject = git_out(["log", "-1", "--format=%s", "--no-merges"], self.root)
        body = self.options.get("body") or subject
        if self.options.get("card"):
            body += f"\n\nCard: {self.options['card']}"
        pr = self._view_pr(gh)
        if not pr or pr.get("state") != "OPEN":
            run([*gh, "pr", "create", "--base", self.base, "--head", self.branch, "--title", subject, "--body", body], cwd=self.root, check=True, timeout=120)
            pr = self._view_pr(gh)
        if not pr:
            raise HarnessError("The pull request was created but could not be read back.")
        if self.options.get("no_merge"):
            return {"status": "pr-open", "pr": pr["url"]}
        ci_down = self.options.get("ci_down")
        if ci_down:
            # Fallback for broken CI infrastructure. The local git hooks already ran the same policy at commit and push.
            comment = f"Merged without waiting for CI: {ci_down}\n\nRe-run the checks on `{self.base}` when CI is back."
            run([*gh, "pr", "comment", str(pr["number"]), "--body", comment], cwd=self.root, timeout=120)
        else:
            self._wait_for_checks(gh, pr)
        run([*gh, "pr", "merge", str(pr["number"]), "--merge"], cwd=self.root, check=True, timeout=120)
        git(["push", "origin", "--delete", self.branch], self.root, env=SHIP_ENV, check=False, timeout=120)
        for path in self.acquired_locks:
            run(["git", "lfs", "unlock", path], cwd=self.root, timeout=60)
        released = list(self.acquired_locks)
        self.acquired_locks.clear()
        note = self._return_to_base()
        result: dict[str, Any] = {"status": "shipped", "pr": pr["url"], "merged_into": self.base, "locks_released": released}
        if ci_down:
            result["ci_skipped"] = ci_down
        if note:
            result["note"] = note
        return result

    def _view_pr(self, gh: list[str]) -> dict[str, Any] | None:
        view = run([*gh, "pr", "view", self.branch, "--json", "number,url,state"], cwd=self.root, timeout=60)
        return json.loads(view.stdout) if view.returncode == 0 and view.stdout.strip() else None

    def _wait_for_checks(self, gh: list[str], pr: dict[str, Any]) -> None:
        delay = float(os.environ.get("HARNESS_CHECK_WAIT", "10"))
        for _ in range(CHECK_START_ATTEMPTS):
            time.sleep(delay)
            try:
                checks = run([*gh, "pr", "checks", str(pr["number"]), "--watch", "--interval", "10"], cwd=self.root, timeout=1500)
            except subprocess.TimeoutExpired as exc:
                raise Stop("checks-failed", pr=pr["url"], output="Timed out waiting for CI.") from exc
            combined = checks.stdout + checks.stderr
            if checks.returncode == 0:
                return
            if "no checks" not in combined.lower():
                raise Stop("checks-failed", pr=pr["url"], output=combined[-1500:])
        raise Stop("checks-missing", pr=pr["url"], message="CI never started, so the pull request stayed open and nothing was merged.")

    def _return_to_base(self) -> str | None:
        feature = self.branch
        git(["fetch", "origin", self.base], self.root, timeout=600)
        incoming = git(["diff", "--name-only", "HEAD", f"origin/{self.base}"], self.root).stdout.splitlines()
        if editor_running() and any(path.startswith(CONTENT_PREFIXES) for path in incoming):
            return f"Unreal Editor is open, so the local copy stayed on {feature}. Close it and run `h sync`."
        switched = run(["git", "switch", self.base], cwd=self.root)
        if switched.returncode != 0:
            return f"Could not return to {self.base}: {switched.stderr.strip()}"
        git(["merge", "--ff-only", f"origin/{self.base}"], self.root, env=SHIP_ENV)
        self.branch = self.base
        git(["branch", "-D", feature], self.root, check=False)
        return None


def ship(options: dict[str, Any], start: Path | None = None) -> int:
    root = repo_root(start or Path.cwd())
    result = ShipFlow(root, load_config(), options).run()
    print(json.dumps(result, indent=2))
    return EXIT_CODES.get(result["status"], 1)


def sync(start: Path | None = None) -> int:
    root = repo_root(start or Path.cwd())
    cfg = load_config()
    base = cfg["branches"]["integration"]
    if editor_running():
        print(json.dumps({"status": "close-editor", "message": "Close Unreal Editor first."}))
        return 4
    if git(["status", "--porcelain"], root).stdout.strip():
        print(json.dumps({"status": "dirty", "message": "Ship or set aside local changes first."}))
        return 3
    feature = git_out(["branch", "--show-current"], root)
    git(["fetch", "origin", base], root, timeout=600)
    git(["switch", base], root)
    git(["merge", "--ff-only", f"origin/{base}"], root, env=SHIP_ENV)
    if feature != base and git(["merge-base", "--is-ancestor", feature, base], root, check=False).returncode == 0:
        git(["branch", "-D", feature], root, check=False)
    print(json.dumps({"status": "synced", "branch": base, "head": git_out(["rev-parse", "--short", "HEAD"], root)}))
    return 0


VERSION = re.compile(r"^\d+\.\d+\.\d+$")


def set_project_version(root: Path, version: str) -> None:
    path = root / "Config" / "DefaultGame.ini"
    text = path.read_text(encoding="utf-8")
    path.write_text(re.sub(r"^ProjectVersion=.*$", f"ProjectVersion={version}", text, flags=re.MULTILINE), encoding="utf-8", newline="")


def release_start(version: str, start: Path | None = None) -> int:
    if not VERSION.match(version):
        raise HarnessError("Use a version like 0.1.0.")
    root = repo_root(start or Path.cwd())
    cfg = load_config()
    integration = cfg["branches"]["integration"]
    branch = f"release/{version}"
    git(["fetch", "origin", integration], root, timeout=600)
    git(["switch", "-c", branch, f"origin/{integration}"], root)
    set_project_version(root, version)
    git(["add", "Config/DefaultGame.ini"], root)
    git(["commit", "-m", f"chore(release): prepare {version}"], root, env=SHIP_ENV)
    git(["push", "-u", "origin", branch], root, env=SHIP_ENV, timeout=600)
    print(json.dumps({"status": "release-started", "branch": branch, "next": "The package workflow is building it. Verify the build, then run `h release finish`."}))
    return 0


def merge_pr(root: Path, head: str, base: str, title: str) -> str:
    gh = gh_command()
    run([*gh, "pr", "create", "--base", base, "--head", head, "--title", title, "--body", title], cwd=root, check=True, timeout=120)
    view = json.loads(run([*gh, "pr", "view", head, "--json", "number,url,state"], cwd=root, check=True, timeout=60).stdout)
    run([*gh, "pr", "merge", str(view["number"]), "--merge"], cwd=root, check=True, timeout=120)
    return str(view["url"])


def release_finish(version: str, start: Path | None = None) -> int:
    root = repo_root(start or Path.cwd())
    cfg = load_config()
    branch = f"release/{version}"
    production = cfg["branches"]["production"]
    integration = cfg["branches"]["integration"]
    to_production = merge_pr(root, branch, production, f"chore(release): {version}")
    to_integration = merge_pr(root, branch, integration, f"chore(release): merge {version} back")
    git(["fetch", "origin", production], root, timeout=600)
    git(["tag", "-a", f"v{version}", "-m", f"Release {version}", f"origin/{production}"], root)
    git(["push", "origin", f"v{version}"], root, env=SHIP_ENV, timeout=120)
    print(json.dumps({"status": "released", "tag": f"v{version}", "prs": [to_production, to_integration]}))
    return 0


def backmerge(start: Path | None = None) -> int:
    root = repo_root(start or Path.cwd())
    cfg = load_config()
    url = merge_pr(root, cfg["branches"]["production"], cfg["branches"]["integration"], "chore: merge hotfix back into dev")
    print(json.dumps({"status": "merged", "pr": url}))
    return 0
