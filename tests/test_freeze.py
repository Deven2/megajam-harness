"""The harness freeze during the jam and the fallback for broken CI."""

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS / "tools"))

from harness import ship  # noqa: E402
from harness.common import load_config  # noqa: E402


def at(text):
    return datetime.fromisoformat(text).replace(tzinfo=timezone.utc)


class FreezeTests(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config()

    def test_open_before_the_jam(self):
        self.assertIsNone(ship.freeze_message(self.cfg, None, at("2026-11-11T20:00:00")))

    def test_frozen_during_the_jam_without_a_blocker(self):
        self.assertIn("frozen", ship.freeze_message(self.cfg, None, at("2026-11-13T12:00:00")))
        self.assertIn("frozen", ship.freeze_message(self.cfg, "  ", at("2026-11-15T20:00:00")))

    def test_a_blocker_opens_it(self):
        self.assertIsNone(ship.freeze_message(self.cfg, "Ship fails on every content PR", at("2026-11-13T12:00:00")))


class CiDownTests(unittest.TestCase):
    def flow(self, options):
        flow = ship.ShipFlow.__new__(ship.ShipFlow)
        flow.root, flow.cfg, flow.base, flow.branch = Path("."), {}, "dev", "feature/x"
        flow.options, flow.acquired_locks = options, []
        flow._view_pr = lambda gh: {"number": 7, "url": "https://example.test/pr/7", "state": "OPEN"}
        flow._return_to_base = lambda: None
        return flow

    def run_flow(self, options):
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        flow = self.flow(options)
        with mock.patch.object(ship, "gh_command", return_value=["gh"]), \
                mock.patch.object(ship, "git_out", return_value="feat(x): y"), \
                mock.patch.object(ship, "git"), \
                mock.patch.object(ship, "run", side_effect=fake_run), \
                mock.patch.object(ship.ShipFlow, "_wait_for_checks") as wait:
            result = flow._pull_request()
        return result, calls, wait

    def test_ci_down_merges_without_waiting_and_leaves_a_comment(self):
        result, calls, wait = self.run_flow({"ci_down": "Actions outage"})
        wait.assert_not_called()
        self.assertEqual(result["status"], "shipped")
        self.assertEqual(result["ci_skipped"], "Actions outage")
        self.assertTrue(any(command[1:3] == ["pr", "comment"] for command in calls))

    def test_normal_ship_waits_for_checks(self):
        result, calls, wait = self.run_flow({})
        wait.assert_called_once()
        self.assertNotIn("ci_skipped", result)


if __name__ == "__main__":
    unittest.main()
