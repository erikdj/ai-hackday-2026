# Integration ledger

Owner: Erik's orchestrator session. One row per sponsor tool. States: **verified** (real key,
real call, seen in a run), **mocked** (`MOCK_*=1`, code path exists), **attempted** (tried, cut,
reason noted), **deferred** (not started by decision). Judges check that every claimed tool does
real work; this table is what the README tool table is generated from.

Last updated: 2026-09-29 11:50 PDT.

| Tool | Tier | State | Evidence | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| Crusoe | 1 | **verified** | 11:44 PDT: key in Doppler; `check-crusoe.sh` OK; `check_crusoe_tools.py --max 20` 13/13 PASS tool calling; trio pinned in Doppler by the overseer; pins v4 from live evidence (JV-116): STRONG zai-org/GLM-5.3 at low reasoning (real BRIEF in ~4 s, correct veto in case 4be3e276), fallback Deepseek-V4-Flash with a 4096 cap; FAST and CRITIC Qwen/Qwen3.8-27B thinking off. Table on JV-97. | Erik (JV-97, done) | Live agent run still pending Band ids. Desk log prints provider + model id for judges. |
| Band | 1 | mocked | PR #8 spine passes 36+5 offline tests against a fake Band; one `BAND_API_KEY` in Doppler, six per-role agent ids still missing | Jaiven (JV-105), Erik (JV-107) | Six remote agents at app.band.ai/agents plus (stretch only) Erik's second account for the Closer boundary room (core since the pivot). |
| Neo4j | 1 | mocked | `hallway/graph/store.py` (PR #11) in-memory with lineage query; driver backend in review; no Aura instance yet | Erik (JV-110), Jaiven (JV-106) | Aura Free instance not created yet. Cut line 2. Clinical nodes plus ACCESSED lineage edges; canned query "which agents saw identifiers?" (expected: Desk, Scribe, Critic). |
| OpenRouter | 2 | deferred | | Jaiven (JV-108) | Dashboard ask-the-graph over the pseudonymized graph only. Never a fallback for transcript-bearing agents (they fail closed). |
| Nebius | 2 | deferred | | Jaiven (JV-107) | Embeddings suggest possible prior encounters on pseudonymous fields; never merge. Identity is Desk's local pseudo_id. |
| Brave | 2 | deferred | | Jaiven (JV-107) | Researcher: one drug interaction/guideline fact with URL; query is the drug name only. |
| Merge.dev | cut | attempted | | | Cut at the 11:10 pivot: no healthcare fit. |
| Vultr | 2 | deferred | | Jaiven (JV-108) | Hosts Scribe, Critic, Grapher, Closer, dashboard. Desk + transcription + upload page stay on the laptop so no audio leaves it. |
| Similarweb | 2 | **verified** | 12:33 PDT live under `doppler run` from Erik's machine: mayoclinic.org → rank 1,304, ~52.3M visits/month (2026-08); sunrisehomehealth.com (the `visit_1` referral org) → unranked, ~890 visits/month. `hallway/research/similarweb.py` + 15 tests (JV-113). | Erik (JV-113) | Researcher organization-legitimacy fact: spoken domain from the transcript (name-anchored, never an unrelated domain), rank + visits + Similarweb page URL; low-traffic and not-found are reported honestly. Wiring into the Researcher's organization trigger is Jaiven's side (JV-107). |
| DuploCloud | 2 | attempted | devkit cloned to `../devkit`, Docker up; `hallway/dashboard/mcp.py` MCP endpoint + 8 tests (PR JV-98); devkit stack not yet started (needs Erik's work email + verification link) | Erik (JV-98) | Register `http://host.docker.internal:8090/mcp` (transport http) under AI Admin → MCP Servers, Provider + Scope, then a ticket asks "which agents saw identifiers?" and gets Desk, Scribe, Critic from Neo4j. Cut 13:45. |
| Plaud | cut | attempted | no device | | Pitch says "any transcript". |
| UserTesting | cut | deferred | | | Needs provisioning. |

## Change log

- 2026-09-29 11:50 PDT: Crusoe verified (13/13 tool calling). Band and Neo4j mocked with real code paths.

- 2026-09-29 11:15 PDT: pivot to Safe Scribe. Merge.dev cut; Band boundary room now core; Neo4j gains lineage edges.

- 2026-09-29 10:58 PDT: Crusoe tool-calling checker landed (JV-97); still no key.

- 2026-09-29 10:50 PDT: ledger created; everything deferred pending keys.
