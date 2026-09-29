# Changelog

All notable changes to this project. Format follows Keep a Changelog; versions are hackday
milestones rather than releases.

## [Unreleased]

### Added
- ADR-0002 proposed: HALLWAY stack (Python, Band + LangGraph, Crusoe direct, FastAPI, Neo4j, Vultr).
- `.env.example`: Nebius, Brave, Merge.dev keys and per-integration MOCK flags; `agent_config.yaml` gitignored.

### Changed
- CLAUDE.md: GitHub blocks self-approval, so merging your own PR is the approval; product code lands in `hallway/`.

## [0.1.0] - 2026-09-29 (PR #1)

### Added
- Project skeleton: `CLAUDE.md` operating rules, README, backlog, changelog, PR template,
  informational CI, `.env.example`, Crusoe smoke-test script.
- `docs/hackday/event-brief.md` with sponsors, prizes, and judging criteria.
- `docs/hackday/sponsor-integrations.md` with Crusoe, Band, DuploCloud, Neo4j, Vultr, OpenRouter notes.
- ADR-0001 (project operating rules) and ADR-0002 (tech stack, proposed/pending).
- Vendored DuploCloud devkit hackday docs under `docs/reference/duplocloud-devkit/` (Apache-2.0).
- Linear project AI Hackday 2026 (`P-JV-47`) with issues JV-94 to JV-103.
