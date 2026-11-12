# The rules changed our plan before we wrote any code

## From Nicolas

Laying the groundwork for the jam! Our team has two technical profiles (Pablo and me) and one artistic profile (Ivan). Given the contest's timeline, we decided to focus our project's use of AI on making it easy for any of the three of us to contribute using only natural language, so that each of us can even work outside our comfort zone. The idea behind the harness is that it works as an abstraction portal: the ideas we come up with can be turned into our game in a predefined way, following, for example, a work or style standard, a particular structure, or the jam's own rules.

## From Pablo

Honestly, I think the project and the ideas we came up with are really good. I hope we can pull off everything we want to do. Fingers crossed!

## What changed

We are three students from Argentina entering the 2026 Epic AI MegaJam with Unreal Engine 5.8, C++ and Blender. One of us is an artist who does not program. Two of us use Claude and one uses ChatGPT.

We started with a plan centered on AI: a shared multi-agent harness that anyone could install and use in plain language. Then we read all 16 pages of the official rules with an agent, and six things changed.

AI use earns no points on its own, so the harness has to pay for itself in speed. Game content cannot exist before the jam, so our Unreal template became a truly blank project. Epic can request our version control history, so nothing in the harness is allowed to rewrite it. A person has to submit the entry, not an agent. AI-generated assets are judged while sourced assets are not scored, so we now log every asset's origin. And the game cannot require extra software, which ruled out calling an LLM at runtime.

The research also broke one of our design ideas. We wanted each subagent to have its own permissions. Claude Code supports that, but Codex subagents inherit their parent's sandbox and tools. A design built on that feature would have protected only some of us.

So permissions moved out of the agents. Every write to a shared branch goes through one command, `h ship`. A hook shared by both tools blocks the direct alternatives, and git hooks apply the same rules a second time. On the GitHub Free plan our private repository has no server-side branch protection, so this local layer is all we have.

What we delegated: reading the rules, comparing vendor documentation and drafting the tooling. What we kept for ourselves: every decision about what to give up.

The first thing the harness did for us was tell us what not to build.
