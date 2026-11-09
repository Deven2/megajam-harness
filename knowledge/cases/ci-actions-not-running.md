# GitHub Actions reported as enabled but never ran

- **Date:** 2026-11-09
- **Area:** ci
- **Vendor:** both

## Situation

Both new private repositories listed their workflows as active, and the API answered `enabled: true`. The first real pull request produced no workflow run and no checks.

## What went wrong

The Actions tab said "GitHub Actions is not currently enabled on this repository", which the API did not reflect.

Separately, `h ship` treated "no checks" as a reason to retry, then merged when the retries ran out. The pull request reached `dev` without CI.

## What worked

- Saving the permission explicitly: `gh api -X PUT repos/<owner>/<repo>/actions/permissions -F enabled=true -f allowed_actions=all`. The Actions tab listed the workflows right after.
- Making `h ship` stop with `checks-missing` and leave the pull request open when no check starts.

## Rule for next time

After creating a repository, open its Actions tab. Active workflows and `enabled: true` do not prove that anything runs. A gate that passes when its signal is missing is not a gate.
