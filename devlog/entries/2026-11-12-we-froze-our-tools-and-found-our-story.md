# We froze our tools and found our story

## From Pablo

Honestly, I think the project and the ideas we came up with are really good. I hope we can pull off everything we want to do. Fingers crossed!

## From Ivan

I'm really excited to be part of this jam! The idea we came up with together looks fun. We'll see which art style we choose for the project, and I'll find out what it's like to move the visuals forward in this environment.

## What changed

Since the last entry we set out to finish the harness, test it against real work, and then stop touching it.

Most of the testing happened in the game repository's CI. Our only self-hosted runner is a teammate's PC, because GitHub-hosted runners cannot build Unreal Engine. We added a 60 fps budget check that measures frame time at 720p, 1080p and 1440p, charts in the workflow summary, and a nightly package at 06:00 Argentina time on jam days two to four.

Several things went wrong. The runner only works while someone is signed in to that PC, so it now starts as a scheduled task at sign-in instead of a Windows service, since the performance test needs the desktop and GPU. The first version of the nightly package would have built the wrong commit: on scheduled runs, `GITHUB_SHA` points to `main`, not to the `dev` branch we package. And when an agent ran two ships in parallel on the same PC, the harness unit tests timed out after 600 seconds. Run alone, the suite passed in under three minutes. We now ship one change at a time per PC.

That last bug summed up a risk we had already lived through: debugging the tool instead of doing the work. So we made a rule (ADR 0007). From the jam start the harness is frozen. `h ship` refuses to change it unless someone names a blocker with no simple workaround:

```
h contribute --blocker "Ship fails on every content PR"
```

We also wrote a fallback so broken CI never stops the game. `h ship --ci-down "<reason>"` merges without waiting for checks and leaves the reason on the pull request; real failing checks are never bypassed. Trello moved back to manual updates, with the agent used only when we ask.

What we delegated: the CI scripts, the tests and the bookkeeping, including a ledger column for whether each asset may be used commercially and the "Tools you used" list for the submission. What we kept: the freeze rule, and how much automation was worth its cost.

Then the theme arrived: "Director's Cut". We brought our first idea, a time-bending heist, to an agent to ground it and score it against the judging criteria. Two rounds of feedback later it had become something else. A bar regular tells everyone he robbed the bank on the TV news. Each section of the heist is played as his story. When he gets caught, he says "No, wait, that's not how it happened" and picks a correction, such as "that camera was broken". We kept these decisions:

- Every failure re-cuts the story, so the theme lives in the core loop, not in the setting (Theme, Gameplay).
- Beers are the lives that keep his audience listening: four at the start and one more at each checkpoint. The story gets more epic under the pressure of the lie, never because he is drunk, which keeps us within the Teen rating.
- The epic level rises with failures and with checkpoints, so every player reaches slow motion, not only those who fail (Fun factor).
- Guards follow fixed routes within a run and switch between hand-made layouts after a lost run, so players can learn them (Level design, Gameplay).

The whole game reads one `StoryState` object: entry point, starting item, beers, epic level, corrections and guard layout. That makes each system small enough to hand to an agent.

The next entry will be about the game.
