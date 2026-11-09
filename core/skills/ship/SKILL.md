---
name: ship
description: Save and share finished work with the team. Use whenever someone says they finished something or wants to upload, commit, push, save to the repo or share changes, in any language, even if they never mention git.
---

# Ship

The person may not know git. Do not ask them to run commands or explain branches unless they ask.

1. Delegate to the `git-shipper` subagent. Tell it what the person finished, in their words, and any Trello card they named.
2. Read the JSON it returns and act on `status`:
   - `shipped`: confirm in one sentence, then use the trello-sync skill to record the result.
   - `pr-open` or `pushed`: say what is still pending.
   - `binary-conflict`: name the files and ask which version to keep. If they keep theirs, rerun with `--keep-mine`.
   - `locked-by-other`: say who holds the lock and suggest talking to them.
   - `text-conflict`: delegate the markers to `ue-cpp-dev`, then ship again.
   - `close-editor`: ask them to close Unreal Editor, then ship again.
   - `checks-failed`: delegate the failure to `ue-test-runner` and report what it finds.
   - `checks-missing`: CI never started. Say the work is safe in an open pull request and that the team owner must check the repository's Actions tab.
   - `policy-rejected`: fix what the output says. Asset names are the usual cause.
3. If this was a milestone or something went surprisingly well or badly, pass one line to `--note` so it reaches the devlog.

Never run `git push`, `git commit` or `gh pr merge` yourself.
