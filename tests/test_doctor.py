"""The doctor report must stay clear for teammates who are not developers."""

import contextlib
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from harness.doctor import Check, print_checks  # noqa: E402


def report(check):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        print_checks([check])
    return output.getvalue()


class PrintChecksTests(unittest.TestCase):
    def test_passing_check_hides_its_fix(self):
        self.assertNotIn("fix:", report(Check("gh-auth", "ok", "signed in", "gh auth login")))

    def test_failing_check_shows_its_fix(self):
        self.assertIn("fix: gh auth login", report(Check("gh-auth", "fail", "not signed in", "gh auth login")))


if __name__ == "__main__":
    unittest.main()
