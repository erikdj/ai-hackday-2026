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

Status: candidate (JV-101).

AuraDB Free at https://console.neo4j.io. Download the credentials file immediately (password is
shown once). Devkit route: register the `mcp-neo4j-cypher` MCP server with a Raw config, provider
type Other, credential keys `uri`, `username`, `password`, `database` (lowercase), scope with both
credential and MCP server, attach to the workspace, enable on the ticket. Standalone route: the
official Python/JS drivers or the same MCP server.

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
