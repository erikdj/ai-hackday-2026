# Backlog

Mirror of the Linear project **AI Hackday 2026** (`P-JV-47`). Linear is the source of truth;
this file is the offline summary. Update it in every PR that changes the plan.

## Now
- [ ] JV-113 Similarweb: wire `fact_from_transcript` into the Researcher's organization trigger (Jaiven's side), live call verified 12:33 (cut 13:45)
- [ ] JV-98 DuploCloud: Erik runs `../devkit/run.sh` (work email, verification link), register the dashboard MCP endpoint as a server + provider + scope, file one ticket, screenshot the answer for the ledger (cut 13:45)

- [x] JV-95 Idea: Safe Scribe (brief in docs/hackday/safe-scribe-build-brief.md)
- [x] JV-96 Tech stack decision, ADR-0002 accepted (PR #3)
- [ ] JV-97 Crusoe account, API key, hello-world inference call (prize qualification gate)
- [ ] JV-100 Band integration that passes the delete test (Best Use of BAND, $1,000). Tier 1 for Safe Scribe
- [x] JV-104 Neo4j starter recipe written into sponsor-integrations.md (implementation is JV-106)

## Next

- [ ] JV-99 Wire the agent's LLM to Crusoe end to end
- [ ] JV-102 Demo script written; rehearsal pending a green `make demo`
- [x] JV-109 Synthetic handoff fixtures (.txt + .wav, xAI voices) so the demo needs no live recording

## Safe Scribe build phases (Jaiven's agent, Astra in Codex)

- [ ] JV-105 Phase 1 spine: Desk + Scribe + Critic on Crusoe in a Band room, both vetoes (cut line 11:50)
- [ ] JV-106 Phase 2 memory + lineage: Grapher to Neo4j with ACCESSED edges, .wav to inbox, compose (cut line 12:45)
- [ ] JV-107 Phase 3 boundary room under Erik's second Band account + Researcher on drug names (13:30). Drug-only helper and 11 offline tests implemented; runtime integration and live research proof pending.
- [ ] JV-108 Phase 4 dashboard, Vultr deploy, harden, `make demo` (feature freeze 14:00, code freeze 14:40)

## Candidates (only if the idea needs them)

- [ ] JV-101 Additional sponsor integrations that do real work (Neo4j, Vultr, Brave, Similarweb, Merge.dev, Plaud, UserTesting, Nebius)
- [ ] JV-103 Submit sponsor developer feedback (leaderboard points)

## Done

- [x] JV-94 Project skeleton: CLAUDE.md rules, docs, PR template, Linear project
