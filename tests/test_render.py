import json
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from harness.core_model import load_agents, load_skills  # noqa: E402
from harness.quality import validate  # noqa: E402
from harness.render import render  # noqa: E402


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.target = Path(self.temp.name)

    def test_core_is_valid(self):
        self.assertEqual(validate(), [])

    def test_claude_output(self):
        render("claude", self.target)
        for skill in load_skills():
            self.assertTrue((self.target / ".claude" / "skills" / skill.name / "SKILL.md").is_file())
        for agent in load_agents():
            self.assertTrue((self.target / ".claude" / "agents" / f"{agent.name}.md").is_file())
        settings = json.loads((self.target / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertEqual(settings["model"], "sonnet")
        self.assertIn("PreToolUse", settings["hooks"])
        servers = json.loads((self.target / ".mcp.json").read_text(encoding="utf-8"))["mcpServers"]
        self.assertEqual(set(servers), {"github", "trello"})
        operator = (self.target / ".claude" / "agents" / "ue-editor-operator.md").read_text(encoding="utf-8")
        self.assertIn("  - unreal-mcp:", operator)
        self.assertIn("127.0.0.1:8765/mcp", operator)
        shipper = (self.target / ".claude" / "agents" / "git-shipper.md").read_text(encoding="utf-8")
        self.assertIn("model: haiku", shipper)
        self.assertIn(".harness/h ship", shipper)
        self.assertIn("Agent", shipper.split("disallowedTools:")[1].splitlines()[0])

    def test_codex_output(self):
        render("codex", self.target)
        config = tomllib.loads((self.target / ".codex" / "config.toml").read_text(encoding="utf-8"))
        self.assertEqual(set(config["mcp_servers"]), {"unreal-mcp", "blender", "github", "trello"})
        self.assertEqual(config["mcp_servers"]["github"]["bearer_token_env_var"], "GITHUB_PAT")
        agent = tomllib.loads((self.target / ".codex" / "agents" / "git-shipper.toml").read_text(encoding="utf-8"))
        self.assertEqual(agent["model"], "gpt-6-luna")
        self.assertIn(r".\.harness\h.cmd ship", agent["developer_instructions"])
        readonly = tomllib.loads((self.target / ".codex" / "agents" / "ue-architect.toml").read_text(encoding="utf-8"))
        self.assertFalse(readonly["features"]["shell_tool"])
        hooks = json.loads((self.target / ".codex" / "hooks.json").read_text(encoding="utf-8"))
        self.assertIn("commandWindows", hooks["hooks"]["PreToolUse"][0]["hooks"][0])
        self.assertTrue((self.target / ".agents" / "skills" / "ship" / "SKILL.md").is_file())

    def test_switching_vendor_removes_the_old_files(self):
        render("claude", self.target)
        render("codex", self.target)
        self.assertFalse((self.target / "CLAUDE.md").exists())
        self.assertFalse((self.target / ".claude" / "agents").exists())
        self.assertTrue((self.target / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
