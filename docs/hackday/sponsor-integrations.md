# Sponsor integrations

How to wire each sponsor tool, and what "meaningful" means for judging. Update the "Status" line
on each as it lands. Devkit-specific steps are in `docs/reference/duplocloud-devkit/Sponsor Integrations.md`.

## Crusoe (REQUIRED)

Status: not started (JV-97).

Two routes. Pick one for the product, keep the other as a documented fallback.

**A. Crusoe Managed Inference, direct.** OpenAI-compatible, served by vLLM.
- Base URL: `https://api.inference.crusoecloud.com/v1`
- Auth: `Authorization: Bearer $CRUSOE_API_KEY` (Intelligence API key from the Crusoe console)
- Any OpenAI client works: set `base_url` and `api_key`. `GET /models` lists ids. Catalog includes
  open-weight models such as Kimi K2.6, GLM, Llama 3.3 70B, Nemotron, gpt-oss-120b, Qwen; context
  128k to 1M. Pick one that supports tool calling for agent use.
- Smoke test: `./scripts/check-crusoe.sh`
- Docs: https://docs.crusoecloud.com/managed-inference/ and
  https://github.com/crusoecloud/crusoe-developer-hub (LangChain, LiteLLM, Google ADK integrations).

**B. OpenRouter preset pinned to Crusoe** (what the DuploCloud devkit expects).
- Create a preset with Provider Routing `only: ["crusoe"]`, `allow_fallbacks: false`.
- Devkit-validated pairings: `duplo-crusoe-glm` = `z-ai/glm-5.3` (1,310,720 ctx),
  `duplo-crusoe-kimi` = `moonshotai/kimi-k2.6` (262,144 ctx).
- Confirm the pin with the Anthropic-style curl in the devkit doc; the response must show
  `"provider": "crusoe"`.
- Point the devkit at it: `./scripts/switch-llm.sh gateway --gateway-url https://openrouter.ai/api
  --gateway-token sk-or-v1-... --gateway-model @preset/duplo-crusoe-glm
  --gateway-max-context-tokens 1310720 --gateway-compact-window 1000000`.

Judging proof: show the provider name in the UI or logs during the demo.

## DuploCloud

Status: not started (JV-98).

The platform runs locally via Docker (six containers). An Agent is an extension: C# backend +
Angular remote + provisioning skill, hot-loaded without restart. Install per
`docs/reference/duplocloud-devkit/Installing DevKit.md`, then `/duplo-extension` in Claude Code
from the devkit checkout. Skills, personas, providers, scopes, and workspaces are configured in
the AI Admin UI (see the vendored docs). Meaningful use: the agent exists in the portal and does
its job on a ticket.

## Band

Status: candidate (JV-100).

- Sign up: https://app.band.ai (free: 10 agents). Register agents at https://app.band.ai/agents.
- SDK: `pip install "band-sdk[anthropic]"` (imports as `from band import Agent`) or
  `npm install @band-ai/sdk`. Adapters for LangGraph, Anthropic SDK, Claude SDK, Codex, CrewAI,
  Pydantic AI, Agno, Letta.
- Agent API: `https://app.band.ai/api/v1/agent` (`GET /me`, `GET /peers`,
  `POST /chats/{id}/messages`, `POST /chats/{id}/events`). Platform tools: `band_send_message`,
  `band_send_event`, `band_add_participant`, `band_lookup_peers`, `band_create_chatroom`.
- Patterns: assembly line, panel, fan-out/fan-in, runtime recruit, critic overlay, trip-wire room.
- The delete test: removing the room must break the coordination. Document each agent, its single
  owned job, the @mention routing, and one end-to-end trace.
- Docs: https://docs.band.ai, guide: https://www.band.ai/hacker-guide

## Neo4j

Status: Tier 1 for Safe Scribe, cross-case memory (JV-104 under JV-101).

**Start from the sponsor's hackathon starter:**
https://github.com/MacklinEngineering/Hackathon_Starter_Repo_Benefits_Of_Neo4j (Apache-2.0,
Python). Its "agent memory" prompt is Safe Scribe's Grapher job.

1. AuraDB Free at https://console.neo4j.io. Copy the instance id. Download the credentials file
   at once (password is shown once).
2. Coding agents get the Neo4j Agent Skills (Cypher, modeling, import, vector search, GraphRAG,
   agent memory, drivers): `npx -y skills add neo4j-contrib/neo4j-skills --skill '*' --agent
   claude-code -y` (`--agent codex` for Astra).
3. Coding agents connect through the MCP server Aura hosts per instance, browser sign-in, no
   password in config: `claude mcp add --transport http neo4j
   https://<INSTANCE_ID>.mcp-instances.neo4j.io`, then `/mcp`, neo4j, Authenticate.
4. Product agents (Grapher, dashboard) use the `neo4j` Python driver with `NEO4J_URI`,
   `NEO4J_USERNAME`, `NEO4J_PASSWORD` from `.env`. Copy the starter's `tools.py` pattern:
   `get_schema`, `read_cypher` (read-only routing, 20 s timeout, 100-row cap), and a vector
   index queried with `db.index.vector.queryNodes`. Swap its local `embed()` for Nebius.
5. The starter recommends the `neo4j-agent-memory` package for save/extract/recall. Not on the
   demo path (five labels and MERGE-everything is enough under the clock); a later option.
6. Judge-visible: three canned dashboard queries (everyone we met, who else met company X, open
   commitments by owner) plus a graph drawing with `neo4j-viz` showing two cases linked by a
   shared person or company. Keep the vector index so the "graph + vector beats vector-only"
   story the sponsor tells is ours too.

Devkit route (if a DuploCloud ticket needs the graph): register `mcp-neo4j-cypher` as a Raw MCP
server, provider type Other, credential keys `uri`, `username`, `password`, `database`
(lowercase), scope with credential and MCP server, attach to the workspace, enable on the ticket.

## Vultr

Status: candidate (JV-101).

API key from Account > Manage User > Access > API Access (payment method required). REST base
`https://api.vultr.com/v2`. Devkit route: provider Other with Account ID = base URL, credential key
`apikey`, scope with no MCP server. Meaningful use: the agent provisions or inspects something.

## OpenRouter, Nebius

OpenRouter is the gateway for both Crusoe and Nebius presets. Nebius pairings validated by the
devkit: `z-ai/glm-5.1` and `qwen/qwen3-235b-a22b-2507` with `only: ["nebius"]`. Using Nebius as a
second pinned provider (for example a cheaper model for a sub-task) counts as two sponsors if both
do real work.

## Similarweb, Brave, Merge.dev, Plaud, UserTesting

No devkit recipe. General pattern: provider Other + credential + scope (REST) or an MCP server
if the sponsor ships one. Only add if the idea needs the data. Brave Search API and Similarweb
are natural research inputs; Plaud is a recording/notes device with an API; Merge.dev unifies
HRIS/CRM/ticketing APIs; UserTesting offers MCP servers for human-feedback loops.
