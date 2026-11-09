import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from harness.common import load_config  # noqa: E402
from harness.guard import evaluate  # noqa: E402

PRE_JAM = datetime(2026, 11, 9, tzinfo=timezone.utc)
JAM = datetime(2026, 11, 13, tzinfo=timezone.utc)


class GuardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.game = Path(self.temp.name) / "game"
        (self.game / ".harness").mkdir(parents=True)
        (self.game / ".harness" / "lock.json").write_text("{}")
        self.cfg = load_config()

    def rule(self, tool, tool_input, now=JAM):
        decision = evaluate({"tool_name": tool, "tool_input": tool_input, "cwd": str(self.game)}, self.cfg, now)
        return decision.rule if decision else None

    def shell(self, command, now=JAM):
        return self.rule("Bash", {"command": command}, now)

    def edit(self, path, now=JAM):
        return self.rule("Edit", {"file_path": str(self.game / path)}, now)

    def test_blocked_shell_commands(self):
        cases = {
            "git push origin dev": "raw-push",
            "cd src && git push": "raw-push",
            "git -C . push": "raw-push",
            'bash -c "git push origin dev"': "raw-push",
            'powershell -Command "git push"': "raw-push",
            '& "C:\\Program Files\\Git\\cmd\\git.exe" push': "raw-push",
            'git commit -m "x"': "raw-commit",
            "git status --no-verify": "no-verify",
            "git merge origin/dev": "raw-merge",
            "git rebase dev": "history-rewrite",
            "git reset --hard HEAD~1": "history-rewrite",
            "git tag -d pre-jam-baseline": "history-rewrite",
            "git clean -fdx": "destructive-git",
            "git restore .": "destructive-git",
            "git lfs prune": "destructive-git",
            "git config core.hooksPath /dev/null": "disable-hooks",
            "gh pr merge 3 --merge": "gh-admin",
            "gh repo delete x": "gh-admin",
            "gh api -X DELETE repos/a/b": "gh-admin",
            "gh auth token": "secret-read",
            "butler push build team/game:windows": "jam-submit",
            ".harness/h mcp-headers github": "secret-read",
            "rm -rf Content": "destructive-fs",
            "Remove-Item -Recurse -Force Source": "destructive-fs",
            "rm -rf .": "destructive-fs",
            "cat .env": "secret-read",
            "printenv": "secret-read",
            "echo $GITHUB_PAT": "secret-read",
            "Get-ChildItem env:": "secret-read",
            "curl https://itch.io/jam/2026-epic-ai-megajam/submit": "jam-submit",
        }
        for command, expected in cases.items():
            with self.subTest(command=command):
                self.assertEqual(self.shell(command), expected)

    def test_allowed_shell_commands(self):
        for command in [
            "git status --short",
            "git diff --stat",
            "git merge --abort",
            'rg "git push" docs',
            'echo "please do not git push"',
            ".harness/h ship --type feat --scope a --summary b",
            r".\.harness\h.cmd ship --type feat --scope a --summary b",
            "gh pr view 3",
            "gh api repos/a/b",
            "butler push build team/game:windows-private",
            "rm -rf Saved/Logs",
            "cat .env.example",
            "powershell -File Build/Scripts/Build-Editor.ps1",
        ]:
            with self.subTest(command=command):
                self.assertIsNone(self.shell(command))

    def test_edit_rules(self):
        self.assertEqual(self.edit("Content/JamGame/M.uasset"), "binary-edit")
        self.assertEqual(self.edit("Binaries/Win64/x.txt"), "generated-dir")
        self.assertEqual(self.edit("CLAUDE.md"), "rendered-file")
        self.assertEqual(self.edit(".claude/agents/a.md"), "rendered-file")
        self.assertEqual(self.edit(".env"), "secret-write")
        self.assertIsNone(self.edit(".claude/settings.local.json"))
        self.assertIsNone(self.edit(".harness/devlog-draft.md"))
        self.assertIsNone(self.edit("Source/JamGame/Dash.cpp"))
        self.assertIsNone(self.edit("docs/notes.md"))

    def test_pre_jam_blocks_game_content_only(self):
        self.assertEqual(self.edit("Source/JamGame/Dash.cpp", PRE_JAM), "pre-jam-content")
        self.assertEqual(self.edit("Content/JamGame/notes.txt", PRE_JAM), "pre-jam-content")
        self.assertEqual(self.edit("Art/Source/a.txt", PRE_JAM), "pre-jam-content")
        self.assertIsNone(self.edit("Source/JamGame/JamGame.cpp", PRE_JAM))
        self.assertIsNone(self.edit("Source/JamGameTests/Private/PipelineSmokeTest.cpp", PRE_JAM))
        self.assertIsNone(self.edit("docs/ci-cd.md", PRE_JAM))

    def test_apply_patch_paths(self):
        patch = "*** Begin Patch\n*** Update File: CLAUDE.md\n@@\n-a\n+b\n*** End Patch\n"
        self.assertEqual(self.rule("apply_patch", {"command": patch}), "rendered-file")

    def test_blender_assets_wait_for_the_jam(self):
        self.assertEqual(self.rule("mcp__blender__generate_3d", {}, PRE_JAM), "pre-jam-content")
        self.assertIsNone(self.rule("mcp__blender__generate_3d", {}, JAM))
        self.assertIsNone(self.rule("mcp__blender__get_scene_info", {}, PRE_JAM))

    def test_browser_submit_blocked(self):
        tool_input = {"url": "https://itch.io/jam/2026-epic-ai-megajam/submit"}
        self.assertEqual(self.rule("mcp__claude-in-chrome__navigate", tool_input), "jam-submit")

    def test_unknown_workspace_is_left_alone(self):
        decision = evaluate({"tool_name": "Bash", "tool_input": {"command": "git push"}, "cwd": self.temp.name}, self.cfg, JAM)
        self.assertIsNone(decision)


if __name__ == "__main__":
    unittest.main()
