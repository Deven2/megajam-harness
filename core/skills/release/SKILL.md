---
name: release
description: Package a playable build, create a release branch or merge a release into main. Use when someone asks for a build, a test package, a release or a version number.
---

# Release

1. Run `{{h}} release start <x.y.z>`. The `package` workflow builds it on the self-hosted runner.
2. Watch it with `gh run list --workflow package --limit 1`. Packaging takes a while, so do not poll in a tight loop.
3. Ask a person to launch the build from the runner's output folder and play it for a minute.
4. Run `{{h}} release finish <x.y.z>`. It merges into `{{production}}` and back into `{{integration}}`, then tags the version.

Make a first test build on jam day two. Packaging surprises are the classic way to miss a jam deadline.
