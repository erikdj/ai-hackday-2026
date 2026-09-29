# Integration ledger

Owner: Erik's orchestrator session. One row per sponsor tool. States: **verified** (real key,
real call, seen in a run), **mocked** (`MOCK_*=1`, code path exists), **attempted** (tried, cut,
reason noted), **deferred** (not started by decision). Judges check that every claimed tool does
real work; this table is what the README tool table is generated from.

Last updated: 2026-09-29 11:50 PDT.

| Tool | Tier | State | Evidence | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| Crusoe | 1 | **verified** | 11:44 PDT: key in Doppler; `check-crusoe.sh` OK; `check_crusoe_tools.py --max 20` 13/13 PASS tool calling; trio pinned in Doppler by the overseer after a reasoning-overhead probe (STRONG deepseek-ai/Deepseek-V4-Flash). Table on JV-97. | Erik (JV-97, done) | Live agent run still pending Band ids. Desk log prints provider + model id for judges. |
| Band | 1 | mocked | PR #8 spine passes 36+5 offline tests against a fake Band; one `BAND_API_KEY` in Doppler, six per-role agent ids still missing | Jaiven (JV-105), Erik (JV-107) | Six remote agents at app.band.ai/agents plus (stretch only) Erik's second account for the Closer boundary room (core since the pivot). |
| Neo4j | 1 | mocked | `hallway/graph/store.py` (PR #11) in-memory with lineage query; driver backend in review; no Aura instance yet | Erik (JV-110), Jaiven (JV-106) | Aura Free instance not created yet. Cut line 2. Clinical nodes plus ACCESSED lineage edges; canned query "which agents saw identifiers?" (expected: Desk, Scribe, Critic). |
| OpenRouter | 2 | deferred | | Jaiven (JV-108) | Dashboard ask-the-graph over the pseudonymized graph only. Never a fallback for transcript-bearing agents (they fail closed). |
| Nebius | 2 | deferred | | Jaiven (JV-107) | Embeddings suggest possible prior encounters on pseudonymous fields; never merge. Identity is Desk's local pseudo_id. |
| Brave | 2 | deferred | | Jaiven (JV-107) | Researcher: one drug interaction/guideline fact with URL; query is the drug name only. |
| Merge.dev | cut | attempted | | | Cut at the 11:10 pivot: no healthcare fit. |
| Vultr | 2 | deferred | | Jaiven (JV-108) | Hosts Scribe, Critic, Grapher, Closer, dashboard. Desk + transcription + upload page stay on the laptop so no audio leaves it. |
| DuploCloud | 2 (after `make demo` green) | deferred | devkit docs vendored | Erik (JV-98) | Self-serve local Docker; register Safe Scribe as a skill/MCP server. |
| Similarweb | 2 | attempted | `hallway/research/similarweb.py` + 7 tests (PR JV-113); live call not yet run against a key | Erik (JV-113) | Researcher organization-legitimacy fact for the named referral org in `visit_1` ("sunrise home health dot com"): rank, monthly visits, Similarweb page URL. Flip to verified once `SIMILARWEB_API_KEY` is in Doppler and one live call returns. Cut 13:45. |
| Plaud | cut | attempted | no device | | Pitch says "any transcript". |
| UserTesting | cut | deferred | | | Needs provisioning. |

## Change log

- 2026-09-29 11:50 PDT: Crusoe verified (13/13 tool calling). Band and Neo4j mocked with real code paths.

- 2026-09-29 11:15 PDT: pivot to Safe Scribe. Merge.dev cut; Band boundary room now core; Neo4j gains lineage edges.

- 2026-09-29 10:58 PDT: Crusoe tool-calling checker landed (JV-97); still no key.

- 2026-09-29 10:50 PDT: ledger created; everything deferred pending keys.
