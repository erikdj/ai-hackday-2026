# Integration ledger

Owner: Erik's orchestrator session. One row per sponsor tool. States: **verified** (real key,
real call, seen in a run), **mocked** (`MOCK_*=1`, code path exists), **attempted** (tried, cut,
reason noted), **deferred** (not started by decision). Judges check that every claimed tool does
real work; this table is what the README tool table is generated from.

Last updated: 2026-09-29 11:15 PDT (post-pivot to HANDOFF).

| Tool | Tier | State | Evidence | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| Crusoe | 1 | deferred | no key yet; `scripts/check_crusoe_tools.py` ready (mock: 3 PASS) | Erik (JV-97) | $10k gate. Discord pins, then Crusoe console Intelligence Foundry, then the Crusoe table. `scripts/check-crusoe.sh` and `scripts/check_crusoe_tools.py` verify. |
| Band | 1 | deferred | SDK installed on Jaiven's laptop; no agents registered | Jaiven (JV-105), Erik (JV-107) | Six remote agents at app.band.ai/agents plus Erik's second account for the Closer boundary room (core since the pivot). |
| Neo4j | 1 | deferred | recipe in docs (JV-104) | Jaiven (JV-106) | Aura Free instance not created yet. Cut line 2. Clinical nodes plus ACCESSED lineage edges; canned query "which agents saw identifiers?" (expected: Desk, Scribe, Critic). |
| OpenRouter | 2 | deferred | | Jaiven (JV-108) | Dashboard ask-the-graph over the pseudonymized graph only. Never a fallback for transcript-bearing agents (they fail closed). |
| Nebius | 2 | deferred | | Jaiven (JV-107) | Embeddings suggest possible prior encounters on pseudonymous fields; never merge. Identity is Desk's local pseudo_id. |
| Brave | 2 | deferred | | Jaiven (JV-107) | Researcher: one drug interaction/guideline fact with URL; query is the drug name only. |
| Merge.dev | cut | attempted | | | Cut at the 11:10 pivot: no healthcare fit. |
| Vultr | 2 | deferred | | Jaiven (JV-108) | Hosts Scribe, Critic, Grapher, Closer, dashboard. Desk + transcription + upload page stay on the laptop so no audio leaves it. |
| DuploCloud | 2 (after `make demo` green) | deferred | devkit docs vendored | Erik (JV-98) | Self-serve local Docker; register HALLWAY as a skill/MCP server. |
| Similarweb | only if a key is pinned in Discord | deferred | | | Enterprise key; 20-minute cap if one appears. |
| Plaud | cut | attempted | no device | | Pitch says "any transcript". |
| UserTesting | cut | deferred | | | Needs provisioning. |

## Change log

- 2026-09-29 11:15 PDT: pivot to HANDOFF. Merge.dev cut; Band boundary room now core; Neo4j gains lineage edges.

- 2026-09-29 10:58 PDT: Crusoe tool-calling checker landed (JV-97); still no key.

- 2026-09-29 10:50 PDT: ledger created; everything deferred pending keys.
