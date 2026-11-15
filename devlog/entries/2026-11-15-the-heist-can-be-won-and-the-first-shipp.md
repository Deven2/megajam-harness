# The heist can be won, and the first Shipping build

## From Ivan

It started calm, but as the hours went by it got harder: sometimes errors, sometimes broken textures or models. What I take from this stretch is how much I learned about tools I had never used before. I worked on the art style through AI tools, and they took care of most of the technical layer, the exporters, import settings and engine menus I would otherwise have had to learn first, so I could spend my time on the look itself and on the details. When something broke, the fix was usually to look closely and talk it through with the team.

## What changed

Today was freeze day, the content freeze before the deadline. We set out to close the loop of the game: a heist you can actually win, beers that behave like lives, and a first Shipping build.

The ending is in. In the vault you take the loot bag and carry it to the getaway van's rear doors, and F there ends the run and opens a victory scene in the bar. The listeners react ("Wow... so you really are the guy from the news", "Maybe we should call the police..."), the hero jokes that the statute of limitations ran out last Tuesday, and the camera turns back to the TV for a second news video, made with AI. Then he says "Well... I'd better get going", the bartender answers "Just another one of those lying fools", and it ends. Beers are now lives tied to the story: the hero buys a round to start telling, each retelling costs a beer, and after a capture the bar shows the beers left, with the lost one blinking three times. There is no cap on corrections, and losing the last beer ends the run (Theme, Gameplay).

Each section now opens with its objective, and nearby guards chat with hints as subtitles: lost keys, a duct cleaning crew messing with the vents, the lift keycard, the van. Their voices come from the guard who speaks and fade with distance (Gameplay, Level design).

The longest list came from playtests. A teammate dictated it in Spanish to the agent, which turned it into small shipped changes. The main ones:

- Aim-only interaction. Before, a keycard next to a door opened the door.
- Detection twice as slow, now 1.2 s.
- Keys and keycards glow soft blue, and keycards show twice as big.
- Cameras light their view with a red spot light that walls block and that switches off when the camera is broken. The old translucent cone went through walls.
- A lift to section 3, a one-way vault door, a lower crouch made in code, an arm swing on the smoke throw, and a third-person camera that no longer peeks through walls.

We made these to make the stealth readable and fair (Fun factor, Gameplay, Visuals). Map edits from three people merged without conflicts.

Ivan added licensed music and sounds from We Love Indies (a tune per section, a different bar song after every capture, a tape rewind on "No, wait"). He also added voiced dialogue for the bartender and the hero, generated offline with ElevenLabs, and a real street with a hotel and a vintage shop, plus a plaza twice the size around the bank (Audio, Level design). Licensed audio is sourced, so it goes in the ledger and is not scored. The generated voices are ours to be judged. In Blender, the team's procedural scripts produced a lift sign reading "OUT OF SERVICE, ONLY WORKS FROM VAULT TO SERVER ROOM" and a stackable switchback stair (Visuals).

Two things went wrong with the first Shipping build, which came out at 260 MB zipped. A shader cook hung waiting for a distributed compile service, so we cooked without it. Then the build failed where the editor did not: two source files defined the same helper name, and Shipping compiles them together as a unity build. We renamed the objective helpers (commit "rename objective helpers that clash in unity builds"). The editor build had accepted it, so only a Shipping build showed the clash.

The agents did the C++, editor and Blender steps from plain-language requests, and the Spanish playtest list is the clearest case: one dictation became many small changes.

The scorecard has no rows yet, so there are no scores to report in this entry.
