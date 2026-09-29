# AI Hackday 2026

Team entry for **The AI Conference Hack Day 2026** (September 29, 2026, San Francisco).
Erik Jones and Jaiven Spence.

Goal: build an agent that runs live, uses **Crusoe** for inference (required for the overall
prize pool), and wires in other sponsor tools that do real work. The product is **HANDOFF**: a
nurse-to-nurse shift handoff becomes a Band case room where agents on Crusoe extract a quoted
clinical brief, a Critic vetoes unsupported claims, unowned follow-ups, and any identifier leaving
the room, and Neo4j records which agent saw which field.

## Status

- Idea: **HANDOFF**, a PHI-safe clinical handoff scribe with an enforced data boundary and access lineage (pivoted from HALLWAY at 11:10 PDT). Build brief: [docs/hackday/handoff-build-brief.md](docs/hackday/handoff-build-brief.md). See Linear JV-95.
- Tech stack: [ADR-0002](docs/decisions/0002-tech-stack.md), accepted. Python, Band + LangGraph, Crusoe direct, FastAPI, Neo4j.
- Project tracking: Linear project **AI Hackday 2026** (`P-JV-47`), Jaiven team.

## Read first

| Doc | What |
| --- | --- |
| [CLAUDE.md](CLAUDE.md) | Team operating rules for humans and agents. Read before anything else. |
| [docs/hackday/event-brief.md](docs/hackday/event-brief.md) | Sponsors, prizes, judging, timeline. |
| [docs/hackday/sponsor-integrations.md](docs/hackday/sponsor-integrations.md) | How to wire Crusoe, Band, DuploCloud, Neo4j, and the rest. |
| [docs/decisions/](docs/decisions/) | Architecture decision records. |
| [docs/reference/duplocloud-devkit/](docs/reference/duplocloud-devkit/) | Vendored DuploCloud devkit hackday docs. |
| [docs/hackday/secrets.md](docs/hackday/secrets.md) | Doppler is the source of truth for every key. `doppler run -- <cmd>`. |
| [backlog.md](backlog.md) | What is next. |
| [changelog.md](changelog.md) | What shipped. |

## Quick start

```bash
doppler setup                                   # project ai-hackday-2026, config dev
doppler run -- ./scripts/check-crusoe.sh        # proves the Crusoe inference path works
```

Product setup instructions are added here once the stack is chosen.

## How work happens

1. Every task is a Linear issue in the AI Hackday 2026 project.
2. An orchestrator agent plans, a coder agent writes, a reviewer agent reviews locally before the PR.
   Each contributor picks their own tools (Erik: Claude Code, Grok, Astra).
3. Everything ships as a pull request. A human approves and merges. No gating.

Details in [CLAUDE.md](CLAUDE.md).
