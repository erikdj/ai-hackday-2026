# Event brief: The AI Conference Hack Day 2026

Source: `ai-hackday-2026.pdf` and `ai-hackday-2026-prizes.pdf` (Builder Terminal exports),
plus https://github.com/duplocloud/devkit/tree/main/hackday.

- **When:** September 29, 2026. Six hours of build time.
- **Where:** San Francisco (The AI Conference).
- **Team:** Erik Jones, Jaiven Spence.
- **Support:** hackday@duplocloud.net, Hack Day Slack, sponsor desks on the floor.
- **Dashboard:** the Builder Terminal (`./tools+feedback.sh`, `./project.sh`, `./prizes.sh`,
  `./leaderboard.sh`). Giving developer feedback on sponsor tools earns leaderboard points.

## Sponsor stack (12 tools)

| Tier | Sponsor | What it is |
| --- | --- | --- |
| Foundation | **Crusoe** | Vertically integrated AI infrastructure; GPU cloud with an "energy-first" approach. Managed Inference is OpenAI-compatible. |
| Core | DuploCloud | AI-powered self-hosted DevOps automation platform. Ships the devkit we build agents on. |
| Core | Similarweb | Digital intelligence: web traffic, competitor analysis, market research data. |
| Core | OpenRouter | Unified API gateway to 500+ models from 80+ providers. Fronts Crusoe and Nebius. |
| Core | Vultr | Global cloud infrastructure: AMD/NVIDIA GPUs, VPS, bare metal, Kubernetes, storage. |
| Core | Band | Interaction infrastructure for real-time multi-agent coordination through shared rooms. |
| Core | Plaud | AI hardware + software that records conversations and turns them into structured notes. |
| Core | Neo4j | Graph database (AuraDB Free for the hackday). |
| Spark | Merge.dev | Unified API for hundreds of third-party integrations. |
| Spark | Nebius | AI-focused GPU cloud. Reached via OpenRouter preset. |
| Spark | Brave | Private AI platform and search API. |
| Spark | UserTesting | Human feedback in design and AI workflows via MCP servers and plugins. |

## Prizes (12 trophies)

| Prize | Award | Rule |
| --- | --- | --- |
| **Overall 1st, Crusoe** | **$5,000** + pitch on the main stage at the Startup Showdown | Projects MUST use Crusoe |
| **Overall 2nd, Crusoe** | **$3,000** | Projects MUST use Crusoe |
| **Overall 3rd, Crusoe** | **$2,000** | Projects MUST use Crusoe |
| Best Use of BAND | $1,000 | Agent coordination must go through a Band room such that removing Band breaks it. Show one of: dependent handoff, runtime recruitment, enforced cross-account boundary, critic with veto. Live room + execution events in the demo. Criteria: https://www.band.ai/hacker-guide |
| Best Agent Overall, DuploCloud | $750 gift card | Judged on what the agent actually does end to end, live. A pitch alone is insufficient. |
| Most Sponsor Tools Meaningfully Integrated, DuploCloud | $750 gift card | Every counted integration must actively contribute. Connected but unused does not count. |
| Best Use of Neo4j | $500 Aura credits | |
| Best Technical Implementation, Neo4j | $400 Aura credits | |
| Most Creative Use Case, Neo4j | $300 Aura credits | |
| Best Use of Plaud | $1,000 | |
| Second-Best Use of Plaud | $500 | |
| LEGO Set, Vultr | LEGO set | |

Qualification depends on challenge completion and judges' evaluation. See contest rules.

## What this means for us

1. **Crusoe is non-negotiable.** Inference must visibly run on Crusoe. Log the provider.
2. **Live and end to end beats ambitious and broken.** Rehearse from a cold start.
3. **Depth over breadth on sponsor tools.** Each one we wire must do a job in the demo flow.
4. **Band is the best secondary bet** if the idea has two or more agents that must coordinate.
5. **Submit feedback on every sponsor tool we touch** for leaderboard points.
