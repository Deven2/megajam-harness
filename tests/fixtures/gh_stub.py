"""Stands in for the GitHub CLI in end-to-end tests. Merges happen in a server-side clone."""

import json
import os
import subprocess
import sys
from pathlib import Path

state_path = Path(os.environ["GH_STUB_STATE"])
server = os.environ["GH_STUB_SERVER"]
args = sys.argv[1:]
state = json.loads(state_path.read_text()) if state_path.exists() else {}


def server_git(*command):
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1"}
    subprocess.run(["git", *command], cwd=server, check=True, capture_output=True, env=env)


if args[:2] == ["pr", "create"]:
    base = args[args.index("--base") + 1]
    head = args[args.index("--head") + 1]
    number = len(state) + 1
    state[head] = {"number": number, "url": f"https://example.test/pr/{number}", "state": "OPEN", "base": base}
    state_path.write_text(json.dumps(state))
    print(state[head]["url"])
elif args[:2] == ["pr", "view"]:
    if args[2] not in state:
        sys.exit(1)
    print(json.dumps(state[args[2]]))
elif args[:2] == ["pr", "checks"]:
    if os.environ.get("GH_STUB_NO_CHECKS"):
        sys.exit("no checks reported on this branch")
    print("All checks were successful")
elif args[:2] == ["pr", "merge"]:
    number = int(args[2])
    head, entry = next((key, value) for key, value in state.items() if value["number"] == number)
    server_git("fetch", "origin")
    server_git("checkout", "-q", entry["base"])
    server_git("merge", "--ff-only", f"origin/{entry['base']}")
    server_git("merge", "--no-ff", "-m", f"Merge pull request #{number}", f"origin/{head}")
    server_git("push", "origin", entry["base"])
    entry["state"] = "MERGED"
    state_path.write_text(json.dumps(state))
else:
    sys.exit(f"gh stub: unsupported command {args}")
