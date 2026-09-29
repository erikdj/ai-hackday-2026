# Backlog

Mirror of the Linear project **AI Hackday 2026** (`P-JV-47`). Linear is the source of truth;
this file is the offline summary. Update it in every PR that changes the plan.

## Now

- [x] JV-95 Idea: HANDOFF (pivoted from HALLWAY 11:10 PDT; brief in docs/hackday/handoff-build-brief.md)
- [x] JV-96 Tech stack decision, ADR-0002 accepted (PR #3)
- [ ] JV-97 Crusoe account, API key, hello-world inference call (prize qualification gate)
- [ ] JV-100 Band-only fixture slice in progress; authenticated messages, veto/repair and revision-bound approval. Live verification pending credentials; contributes to JV-105.
- [x] JV-104 Neo4j starter recipe written into sponsor-integrations.md (implementation is JV-106)

## Next

- [ ] JV-99 Wire the agent's LLM to Crusoe end to end
- [ ] JV-102 Demo script written; rehearsal pending a green `make demo`

## HANDOFF build phases (Jaiven's agent, Astra in Codex)

- [ ] JV-105 Phase 1 spine: in progress in draft PR #8; case-room-only HANDOFF schema, identifier/owner checks and Crusoe fail-closed path. Both vetoes and live Band/Crusoe execution remain unverified (cut line 11:50).
- [ ] JV-106 Phase 2 memory + lineage: Grapher to Neo4j with ACCESSED edges, .wav to inbox, compose (cut line 12:45)
- [ ] JV-107 Phase 3 boundary room under Erik's second Band account + Researcher on drug names (13:30)
- [ ] JV-108 Phase 4 dashboard, Vultr deploy, harden, `make demo` (feature freeze 14:00, code freeze 14:40)

## Candidates (only if the idea needs them)

- [ ] JV-98 DuploCloud devkit (Tier 2, only after `make demo` is green)
- [ ] JV-101 Additional sponsor integrations that do real work (Neo4j, Vultr, Brave, Similarweb, Merge.dev, Plaud, UserTesting, Nebius)
- [ ] JV-103 Submit sponsor developer feedback (leaderboard points)

The live path is not yet verified. Agentbridge, coding agents and Linear are development
tools only; runtime handoffs must go through Band. A mocked check is never a live demo pass.

## Done

- [x] JV-94 Project skeleton: CLAUDE.md rules, docs, PR template, Linear project
