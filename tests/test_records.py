"""Asset ledger and submission helpers that read the game repository's compliance files."""

import sys
import tempfile
import unittest
from pathlib import Path

HARNESS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HARNESS / "tools"))

from harness.records import (  # noqa: E402
    LEDGER_RELATIVE,
    append_ledger,
    not_commercial,
    read_ledger,
    read_tools,
    tools_missing_from_list,
)

AI_USAGE = """# AI usage

## Tools

| Tool | Used for |
| --- | --- |
| Claude Code | Programming |
| Hyper3D Rodin | Props from reference images |

## Other

| Tool | Used for |
| --- | --- |
| Not a tool | Ignored |
"""


class RecordsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def test_tools_come_from_the_tools_table_only(self):
        path = self.root / "docs" / "compliance" / "ai-usage.md"
        path.parent.mkdir(parents=True)
        path.write_text(AI_USAGE, encoding="utf-8")
        self.assertEqual(read_tools(self.root), ["Claude Code", "Hyper3D Rodin"])

    def test_ai_asset_sources_must_appear_in_the_tools_list(self):
        rows = [
            {"kind": "ai-generated", "origin": "rodin"},
            {"kind": "ai-generated", "origin": "Tripo"},
            {"kind": "sourced", "origin": "Fab"},
        ]
        self.assertEqual(tools_missing_from_list(rows, ["Claude Code", "Hyper3D Rodin"]), ["Tripo"])

    def test_old_ledger_gains_the_commercial_column(self):
        path = self.root / LEDGER_RELATIVE
        path.parent.mkdir(parents=True)
        path.write_text(
            "added_utc,kind,origin,reference,license,path,notes\n"
            "2026-11-12T10:00:00+00:00,sourced,Fab,,Fab Standard,/Game/ThirdParty/Crate,\n",
            encoding="utf-8",
        )
        append_ledger(self.root, {
            "added_utc": "2026-11-12T11:00:00+00:00", "kind": "sourced", "origin": "WeLoveIndies",
            "reference": "", "license": "WeLoveIndies free", "commercial_use": "no",
            "path": "/Game/ThirdParty/Audio/Theme", "notes": "",
        })
        rows = read_ledger(self.root)
        self.assertEqual([row["commercial_use"] for row in rows], ["unknown", "no"])
        self.assertEqual(not_commercial(rows), ["/Game/ThirdParty/Crate", "/Game/ThirdParty/Audio/Theme"])


if __name__ == "__main__":
    unittest.main()
