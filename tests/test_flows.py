"""End-to-end tests of hooks and `h ship` against a local bare remote."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS / "tools"))

from harness.common import load_config  # noqa: E402
from harness.ship import ShipFlow  # noqa: E402

JAM = "2026-11-13T00:00:00Z"
PRE_JAM = "2026-11-09T00:00:00Z"
POLICY = """
[repo]
kind = "game"
protected_branches = ["main", "dev"]
[contest]
start_utc = "2026-11-12T05:00:00Z"
[prejam]
blocked = ["Content/*", "Art/*"]
allowed = ["Art/README.md"]
gameplay_root = "Source/JamGame/"
gameplay_allowed = ["Source/JamGame/JamGame.cpp"]
[limits]
max_non_lfs_mib = 5
[naming]
exempt = ["Content/ThirdParty/"]
prefixes = ["SM_", "M_"]
"""
ATTRIBUTES = "* text=auto\n*.umap filter=lfs diff=lfs merge=lfs -text lockable\n*.uasset filter=lfs diff=lfs merge=lfs -text lockable\n"
OPTIONS = {"type": "feat", "scope": "player", "summary": "add dash", "paths": None, "body": None, "note": None, "card": None, "base": None, "keep_mine": False, "no_merge": False}


def git(cwd, *args, env=None, check=True):
    merged = {**os.environ, **(env or {})}
    return subprocess.run(["git", *args], cwd=cwd, env=merged, check=check, text=True, capture_output=True, encoding="utf-8")


class FlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base_temp = tempfile.TemporaryDirectory()
        cls.base = Path(cls.base_temp.name)
        cls.remote = cls.base / "remote.git"
        git(cls.base, "init", "--bare", "-q", "-b", "main", str(cls.remote))
        cls.url = cls.remote.as_uri()
        seed = cls.base / "seed"
        git(cls.base, "clone", "-q", cls.url, str(seed))
        cls.configure(seed)
        shutil.copytree(HARNESS / ".githooks", seed / ".githooks")
        (seed / ".githooks" / "policy.toml").write_text(POLICY, encoding="utf-8")
        (seed / ".gitattributes").write_text(ATTRIBUTES, encoding="utf-8")
        (seed / "README.md").write_text("seed\n", encoding="utf-8")
        bootstrap = {"HARNESS_BOOTSTRAP": "1"}
        git(seed, "add", "-A")
        git(seed, "commit", "-m", "chore: seed", env=bootstrap)
        git(seed, "push", "origin", "main", env=bootstrap)
        git(seed, "push", "origin", "main:dev", env=bootstrap)
        cls.server = cls.base / "server"
        git(cls.base, "clone", "-q", cls.url, str(cls.server), env={"GIT_LFS_SKIP_SMUDGE": "1"})
        git(cls.server, "config", "user.email", "server@example.test")
        git(cls.server, "config", "user.name", "Server")
        git(cls.server, "branch", "-q", "dev", "origin/dev")
        cls.state = cls.base / "gh_state.json"

    @classmethod
    def tearDownClass(cls):
        subprocess.run(["git", "gc", "-q"], cwd=cls.remote, check=False)
        cls.base_temp.cleanup()

    @staticmethod
    def configure(path):
        git(path, "config", "user.email", "test@example.test")
        git(path, "config", "user.name", "Tester")
        git(path, "config", "core.hooksPath", ".githooks")
        git(path, "config", "lfs.setlockablereadonly", "false")

    def clone(self, name):
        path = self.base / name
        if path.exists():
            shutil.rmtree(path, ignore_errors=True)
        git(self.base, "-c", "lfs.setlockablereadonly=false", "clone", "-q", "-b", "dev", self.url, str(path))
        self.configure(path)
        return path

    def environment(self, now=JAM):
        return {
            "HARNESS_NOW": now,
            "HARNESS_GH": json.dumps([sys.executable, str(HARNESS / "tests" / "fixtures" / "gh_stub.py")]),
            "HARNESS_CHECK_WAIT": "0",
            "HARNESS_ASSUME_EDITOR": "0",
            "GH_STUB_STATE": str(self.state),
            "GH_STUB_SERVER": str(self.server),
        }

    def ship(self, path, now=JAM, **overrides):
        with mock.patch.dict(os.environ, self.environment(now)):
            return ShipFlow(path, load_config(), {**OPTIONS, **overrides}).run()

    def write(self, path, relative, text="content\n"):
        target = path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")

    def test_ship_merges_with_a_merge_commit(self):
        work = self.clone("ship_ok")
        self.write(work, "Source/JamGame/Dash1.cpp")
        result = self.ship(work, summary="add first dash")
        self.assertEqual(result["status"], "shipped", result)
        self.assertEqual(result["branch"], "dev")
        self.assertEqual(git(work, "branch", "--show-current").stdout.strip(), "dev")
        self.assertTrue((work / "Source/JamGame/Dash1.cpp").exists())
        subject = git(work, "log", "-1", "--format=%s").stdout.strip()
        self.assertTrue(subject.startswith("Merge pull request"), subject)
        body = git(work, "log", "--no-merges", "-1", "--format=%B").stdout
        self.assertIn("feat(player): add first dash", body)

    def test_missing_checks_stop_the_merge(self):
        work = self.clone("no_checks")
        self.write(work, "Source/JamGame/DashNoChecks.cpp")
        with mock.patch.dict(os.environ, {"GH_STUB_NO_CHECKS": "1"}):
            result = self.ship(work, summary="add unchecked dash")
        self.assertEqual(result["status"], "checks-missing", result)
        self.assertEqual(json.loads(self.state.read_text())[result["branch"]]["state"], "OPEN")

    def test_pre_jam_content_is_rejected_then_allowed_at_start(self):
        work = self.clone("prejam")
        self.write(work, "Source/JamGame/Dash2.cpp")
        result = self.ship(work, now=PRE_JAM, summary="add early dash")
        self.assertEqual(result["status"], "policy-rejected", result)
        self.assertIn("C-01", result["output"])
        result = self.ship(work, summary="add dash at start")
        self.assertEqual(result["status"], "shipped", result)

    def test_nothing_to_ship(self):
        work = self.clone("nothing")
        self.assertEqual(self.ship(work)["status"], "nothing-to-ship")

    def test_bad_asset_name_is_rejected(self):
        work = self.clone("badname")
        self.write(work, "Content/JamGame/Barrel.uasset")
        result = self.ship(work, type="art", summary="add barrel")
        self.assertEqual(result["status"], "policy-rejected", result)
        self.assertIn("prefix", result["output"])

    def test_binary_conflict_stops_and_keep_mine_resolves(self):
        first = self.clone("binary_a")
        self.write(first, "Content/JamGame/M_Shared.uasset", "base\n")
        self.assertEqual(self.ship(first, type="art", summary="add shared material")["status"], "shipped")
        ours = self.clone("binary_b")
        theirs = self.clone("binary_c")
        self.write(theirs, "Content/JamGame/M_Shared.uasset", "theirs\n")
        self.assertEqual(self.ship(theirs, type="art", summary="tweak material from c")["status"], "shipped")
        self.write(ours, "Content/JamGame/M_Shared.uasset", "ours\n")
        result = self.ship(ours, type="art", summary="tweak material from b")
        self.assertEqual(result["status"], "binary-conflict", result)
        self.assertEqual(result["files"], ["Content/JamGame/M_Shared.uasset"])
        result = self.ship(ours, type="art", summary="tweak material from b", keep_mine=True)
        self.assertEqual(result["status"], "shipped", result)

    def test_editor_open_stops_incoming_content(self):
        first = self.clone("editor_a")
        second = self.clone("editor_b")
        self.write(first, "Source/JamGame/Incoming.cpp")
        self.assertEqual(self.ship(first, summary="add incoming")["status"], "shipped")
        self.write(second, "docs/note.md")
        environment = {**self.environment(), "HARNESS_ASSUME_EDITOR": "1"}
        with mock.patch.dict(os.environ, environment):
            result = ShipFlow(second, load_config(), {**OPTIONS, "type": "docs", "summary": "add note"}).run()
        self.assertEqual(result["status"], "close-editor", result)
        result = self.ship(second, type="docs", summary="add note")
        self.assertEqual(result["status"], "shipped", result)

    def test_hooks_reject_direct_commit_and_bad_message(self):
        work = self.clone("hooks")
        env = {"HARNESS_NOW": JAM}
        self.write(work, "docs/a.md")
        git(work, "add", "-A")
        direct = git(work, "commit", "-m", "docs: add a", env=env, check=False)
        self.assertNotEqual(direct.returncode, 0)
        self.assertIn("Do not commit directly", direct.stderr)
        git(work, "switch", "-c", "feature/hooks")
        spanish = git(work, "commit", "-m", "docs: agrego la pagina numero 2 aca", env=env, check=False)
        self.assertEqual(spanish.returncode, 0, "ASCII Spanish cannot be detected, only accents.")
        self.write(work, "docs/b.md")
        git(work, "add", "-A")
        accent = git(work, "commit", "-m", "docs: agregué otra página", env=env, check=False)
        self.assertNotEqual(accent.returncode, 0)
        malformed = git(work, "commit", "-m", "updated stuff", env=env, check=False)
        self.assertNotEqual(malformed.returncode, 0)

    def test_hooks_reject_secret_and_force_push(self):
        work = self.clone("secrets")
        env = {"HARNESS_NOW": JAM}
        git(work, "switch", "-c", "feature/secrets")
        self.write(work, "docs/a.md", "token ghp_" + "a" * 36 + "\n")
        git(work, "add", "-A")
        leaked = git(work, "commit", "-m", "docs: add a", env=env, check=False)
        self.assertNotEqual(leaked.returncode, 0)
        self.assertIn("secret", leaked.stderr)
        self.write(work, "docs/a.md", "clean\n")
        git(work, "add", "-A")
        git(work, "commit", "-m", "docs: add a", env=env)
        git(work, "push", "-q", "origin", "feature/secrets", env=env)
        git(work, "reset", "-q", "--hard", "HEAD~1")
        self.write(work, "docs/b.md", "other\n")
        git(work, "add", "-A")
        git(work, "commit", "-m", "docs: add b", env=env)
        forced = git(work, "push", "--force", "origin", "feature/secrets", env=env, check=False)
        self.assertNotEqual(forced.returncode, 0)
        self.assertIn("Non fast-forward", forced.stderr)

    def test_hook_rejects_direct_push_to_dev(self):
        work = self.clone("pushdev")
        env = {"HARNESS_NOW": JAM, "HARNESS_ALLOW_PROTECTED": "1"}
        self.write(work, "docs/x.md")
        git(work, "add", "-A")
        git(work, "commit", "-m", "docs: add x", env=env)
        pushed = git(work, "push", "origin", "dev", env={"HARNESS_NOW": JAM}, check=False)
        self.assertNotEqual(pushed.returncode, 0)
        self.assertIn("Direct pushes", pushed.stderr)


if __name__ == "__main__":
    unittest.main()
