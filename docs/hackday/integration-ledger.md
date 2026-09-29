# Integration ledger

Owner: Erik's orchestrator session. One row per sponsor tool. States: **verified** (real key,
real call, seen in a run), **mocked** (`MOCK_*=1`, code path exists), **attempted** (tried, cut,
reason noted), **deferred** (not started by decision). Judges check that every claimed tool does
real work; this table is what the README tool table is generated from.

Last updated: 2026-09-29 10:50 PDT.

| Tool | Tier | State | Evidence | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| Crusoe | 1 | deferred | no key yet; `scripts/check_crusoe_tools.py` ready (mock: 3 PASS) | Erik (JV-97) | $10k gate. Discord pins, then Crusoe console Intelligence Foundry, then the Crusoe table. `scripts/check-crusoe.sh` and `scripts/check_crusoe_tools.py` verify. |
| Band | 1 | deferred | SDK installed on Jaiven's laptop; no agents registered | Jaiven (JV-105) | Six remote agents at app.band.ai/agents; ids and keys into gitignored `agent_config.yaml`. |
| Neo4j | 1 | deferred | recipe in docs (JV-104) | Jaiven (JV-106) | Aura Free instance not created yet. Cut line 2, after the spine. |
| OpenRouter | 2 | deferred | | Jaiven (JV-108) | Dashboard ask-the-graph and last-resort fallback only. |
| Nebius | 2 | deferred | | Jaiven (JV-107) | Embeddings for entity resolution. |
| Brave | 2 | deferred | | Jaiven (JV-107) | Researcher search. |
| Merge.dev | 2 | deferred | | Jaiven (JV-108) | Closer writes Contact + Opportunity + Note. |
| Vultr | 2 | deferred | | Jaiven (JV-108) | Compose deploy; laptop fallback. |
| DuploCloud | 2 (after `make demo` green) | deferred | devkit docs vendored | Erik (JV-98) | Self-serve local Docker; register HALLWAY as a skill/MCP server. |
| Similarweb | only if a key is pinned in Discord | deferred | | | Enterprise key; 20-minute cap if one appears. |
| Plaud | cut | attempted | no device | | Pitch says "any transcript". |
| UserTesting | cut | deferred | | | Needs provisioning. |

## Change log

- 2026-09-29 10:58 PDT: Crusoe tool-calling checker landed (JV-97); still no key.

- 2026-09-29 10:50 PDT: ledger created; everything deferred pending keys.
