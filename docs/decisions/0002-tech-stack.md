# ADR-0002: Tech stack

Status: Accepted 2026-09-29 (Erik merged PR #3; Jaiven's design-partner review on the PR: accept). Derived from Jaiven's HALLWAY
build brief (PR #4, `docs/hackday/hallway-build-brief.md`), amended at the 11:10 PDT pivot to
HANDOFF (`docs/hackday/handoff-build-brief.md`) and the review on Linear JV-95.

## Context

**The idea: HANDOFF (pivot, 11:10 PDT).** A nurse-to-nurse shift handoff recording (transcribed
on-device) becomes a Band case room where agents on Crusoe extract a quoted clinical brief, a
Critic blocks unsupported claims, unowned follow-ups, and any direct identifier trying to leave
the room, and Neo4j records which agent saw which field. Buyer: clinics that cannot send PHI to a
hyperscaler LLM API and cannot prove afterwards who saw what. Merge.dev is cut; the Closer
boundary room under a second Band account is core. The stack below is unchanged.

**The original idea: HALLWAY.** A conversation (typed notes, pasted transcript, or a 60-second recording
transcribed locally) becomes a Band case room where a crew of agents, all thinking on Crusoe,
argues before it commits: extract facts with verbatim quotes, recruit a researcher only if a
company is named, a Critic on a different model family vetoes anything unsupported, and only then
are the graph writer and the closer let into the room. Neo4j is cross-case memory.

The brief fixes the skeleton (Band room per case, Crusoe as every agent's brain, runtime
recruitment, Critic with a real veto, Neo4j memory) and leaves the domain swappable in the first
15 minutes. Build budget is four hours of wall clock on two laptops with self-serve accounts.

## Decision

| Concern | Choice | Why |
| --- | --- | --- |
| Language / runtime | Python 3.11+ | Band SDK, LangGraph, faster-whisper, neo4j driver are all Python-first |
| Agent framework | `band-sdk[langgraph]` with `LangGraphAdapter(llm=ChatOpenAI(base_url=CRUSOE, ...))` | Documented Band quickstart with the base URL swapped; no custom adapter |
| LLM route to Crusoe | Crusoe Managed Inference direct, `https://api.inference.crusoecloud.com/v1`, ids from `GET /v1/models` | Judge-visible Crusoe use; one `llm(role)` factory in `common/llm.py`; fallback chain Crusoe A, Crusoe B, then OpenRouter logged in red and never on the demo path |
| Coordination | Band rooms, roster, gate, veto; `Emit.THOUGHTS` and `Emit.TOOL_CALLS` on every agent | Best Use of BAND delete test |
| Memory + lineage | Neo4j AuraDB Free, `graph/schema.cypher` (Patient, Encounter, Finding, Med, Commitment, Staff plus `(Agent)-[:ACCESSED {field, purpose, ts}]->(Field)`, MERGE everything), vector index for prior-encounter suggestions (Nebius embeddings; identity is Desk's locally assigned pseudo_id, similarity never merges); follow the sponsor's hackathon starter (`tools.py` pattern, `neo4j-viz`). `neo4j-agent-memory` is a later option, not on the demo path | Neo4j prizes, cross-case linking; see JV-104 |
| Web / API | FastAPI (upload page, dashboard, ask-the-graph via OpenRouter) | Small, async, one process |
| Transcription | faster-whisper, local | No device dependency |
| Hosting for demo | Vultr VM, Docker Compose; laptop is the fallback | Demo does not ride venue wifi |
| Tests | pytest; `make demo` runs `fixtures/case_2.txt` end to end as the acceptance test; mocks per integration behind `MOCK=1` | Hackday-realistic coverage: every integration has a mock and one real-path check |
| Product code location | `hallway/` in this repo, one file per agent and per integration | Brief section 5 |
| Dependencies | band-sdk, langgraph, langchain-openai, openai, neo4j, neo4j-viz, fastapi, httpx, faster-whisper, pytest | Anything else needs a reason in the commit message |

Sponsor tool tiers (from the brief, amended by review and the pivot): Tier 1 Crusoe, Band, Neo4j.
Tier 2 OpenRouter (ask-the-graph over the pseudonymized graph only), Nebius, Brave, Vultr.
Merge.dev cut at the pivot. Amendment: DuploCloud is self-serve (local Docker
devkit, work email only) and stays a Tier 2 candidate, taken up only after `make demo` is green
on Vultr: register HALLWAY as a skill or MCP server so a ticket can open a case. Plaud is cut unless a device appears; the pitch says "any
transcript", not "Plaud transcript".

## Consequences

- Repo gains Python tooling at `hallway/` (pyproject or requirements, Makefile, docker-compose).
  Root stays as is.
- `agent_config.yaml` (six Band agent ids and keys) is gitignored. Every key is listed in
  `.env.example`.
- Team rules still apply to the builder agent: branch per Linear issue, local independent review,
  PR, human merge. No direct pushes to `main`.
- The Critic must be on a different model family from the Scribe; the demo must show at least the
  Critic and three workers served by Crusoe.
