---
name: kickoff
description: Run the team's kickoff, from the theme reveal to a chosen game idea, a one-page brief and a work plan. Use when the theme is announced, when someone says the jam is starting or asks what game to make, or wants to pick between game ideas. Any language.
---

# Kickoff

The theme is revealed on Nov 11 at 16:00 Argentina time. The jam starts on Nov 12 at 02:00. Until then nobody creates game content: ideas and documents only. Guide the team through these steps and keep the timeboxes.

## Before the stream

- Each person runs `{{h}} doctor --live` and fixes any failure.
- The runner is online. Unreal and Blender MCP answer one read-only call.

## 1. Theme (during the stream)

Write down the theme, its exact wording and any rule or schedule change. Rule changes go to the person, never into the harness: it freezes at the jam start.

## 2. Ideas (30 minutes)

Each person brings up to three ideas, one line each, in any language: the player's goal, the main action and how it uses the theme. No discussion yet.

## 3. Choice (30 minutes)

Score each idea from 1 to 5 against the seven judging criteria: Ambition and innovation, Theme, Fun factor, Gameplay, Visuals, Level design, Audio. Fun factor counts double, as in the judges' tie-break. Remove any idea that needs a technology we have not tested. Pick the top idea. If it is a tie, the team decides.

## 4. Brief (one hour)

Write `docs/design/game-brief.md` in the game repository, in English, one page:

- Pitch in one sentence, and how it uses the theme.
- Core loop: what the player does every 30 seconds.
- Three player verbs, such as jump, grab, throw.
- Minimum playable game for the end of day two, and stretch goals in priority order.
- Art direction (Ivan), audio direction (Ivan) and the first level's flow (whole team, gameplay lead Nicolas).
- Risks and what we will not do.
- Work per day: day 1 core loop in a greybox; day 2 playable, first package and the first video test; day 3 content and polish; day 4 freeze 8 hours before the deadline, video and submission.

## 5. Owners

- Nicolas: gameplay lead and the runner. Pablo: programming. Ivan: art and audio. Level design: everyone, with one owner per level file at a time.
- Create the main level with external actors (World Settings > Use External Actors, on by default in World Partition levels), so each actor saves as its own file and two people can edit the level without overwriting each other. Lock the `.umap` for changes to the level itself.

## 6. Paperwork (before 02:00)

1. Give the person a list of cards to create by hand on the board, with `Need`, `Goal` and `Steps`.
2. Set `game_name` in `docs/compliance/submission.toml` and in the harness's `harness.toml`, which freezes at 02:00.
3. Complete the game design section of `docs/compliance/pre-jam-declaration.md` and set `declaration_complete = true`.
4. Create `docs/design/scorecard.md` with one row per day and one column per criterion. Each night the team scores the game from 1 to 5. The devlog uses it.
5. Ship the documents. Content starts at 02:00.
