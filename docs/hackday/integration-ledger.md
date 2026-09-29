# Integration ledger

Owner: Erik's orchestrator session. One row per sponsor tool. States: **verified** (real key,
real call, seen in a run), **mocked** (`MOCK_*=1`, code path exists), **attempted** (tried, cut,
reason noted), **deferred** (not started by decision). Judges check that every claimed tool does
real work; this table is what the README tool table is generated from.

Last updated: 2026-09-29 14:00 PDT (feature-freeze sweep, overseer; every state below was observed today, evidence links on the Linear issue named).

| Tool | Tier | State | Evidence | Owner | Notes |
| --- | --- | --- | --- | --- | --- |
| Crusoe | 1 | **verified** | 11:44 PDT: key in Doppler; `check-crusoe.sh` OK; `check_crusoe_tools.py --max 20` 13/13 PASS tool calling; trio pinned in Doppler by the overseer; pins v4 from live evidence (JV-116): STRONG zai-org/GLM-5.3 at low reasoning (real BRIEF in ~4 s, correct veto in case 4be3e276), fallback Deepseek-V4-Flash with a 4096 cap; FAST and CRITIC Qwen/Qwen3.8-27B thinking off. Table on JV-97. | Erik (JV-97, done) | Live agent run still pending Band ids. Desk log prints provider + model id for judges. |
| Band | 1 | **verified** | Five Remote Agents (Desk, Scribe, Critic, Grapher, Researcher) registered with their own keys. Live case `a9806e53` (13:0x): TRANSCRIPT → BRIEF 1 → Critic VETO (unowned follow-up) → OWNER_REQUEST → human `I'll own it` → BRIEF 2 (owner = the human's message) → **APPROVE 2**. Live case `84cfeb33`: APPROVE → BOUNDARY_CREATED → BOUNDARY_SENT → approved room `0dc2f499` with Grapher only, envelope `lineage_verification: verified_field_access`. Rooms named `Safe Scribe case <id>` / `Safe Scribe approved <id>`; messages markdown first, envelope last (PR #40). | Jaiven (JV-116), Erik (JV-118) | Closer not registered (stretch). The identifier veto never fired live because Scribe never leaked; the gate is shown from tests. |
| Neo4j | 1 | **verified** | Aura instance `2d438d7b` (database named by instance id). 12:14 from Erik's machine with the real `Neo4jStore`: schema applied, two encounters MERGEd (`merged: True` on the second), `who_saw_identifiers` → Critic, Desk, Scribe. 13:48: the real `Neo4jStore` from Erik's machine shows `who_saw_identifiers` = Critic, Desk, Scribe and two pseudonymous patients (`p_1ea8b2…`, `p_83cd10…` = handoff_2) written by Jaiven's live Grapher from an approved room. Not seeded. `hallway/graph/store.py` + `neo4j_store.py`, dashboard `/lineage/who-saw-identifiers`, MCP tool. | Erik (JV-110), Jaiven (JV-106) | Lineage manifest names identifier fields per agent (PR #35); dashboard title-cases (PR #39). |
| OpenRouter | 2 | not used | | | Dropped: nothing on the demo path needs it; transcript-bearing agents fail closed on Crusoe by rule. |
| Nebius | 2 | attempted | Credentials issued were an object-storage access/secret pair, not an inference key; embeddings path not built. | Jaiven (JV-107) | Would have suggested prior encounters on pseudonymous fields; identity stays Desk's local pseudo_id either way. |
| Brave | 2 | **verified** | `hallway/research/brave.py` live through `doppler run`: ciprofloxacin → https://www.drugs.com/drug-interactions/ciprofloxacin.html in 1.7 s (PR #27). Labelled mock when no key. | Jaiven (JV-107) | Researcher recruitment and posting still to land (Astra). |
| Merge.dev | cut | attempted | | | Cut at the 11:10 pivot: no healthcare fit. |
| Vultr | 2 | attempted | Key in Doppler; `docker-compose.yml` with role-scoped credentials (PR #37) is deploy-ready; no host brought up: a last-hour deploy was judged riskier than the laptop for a live demo. | Jaiven (JV-108) | Desk, transcription and the upload page stay on the laptop by design. |
| Similarweb | 2 | **verified** | 12:33 PDT live under `doppler run` from Erik's machine: mayoclinic.org → rank 1,304, ~52.3M visits/month (2026-08); sunrisehomehealth.com (the `visit_1` referral org) → unranked, ~890 visits/month. `hallway/research/similarweb.py` + 15 tests (JV-113). | Erik (JV-113) | Researcher organization-legitimacy fact: spoken domain from the transcript (name-anchored, never an unrelated domain), rank + visits + Similarweb page URL; low-traffic and not-found are reported honestly. Wiring into the Researcher's organization trigger is Jaiven's side (JV-107). |
| DuploCloud | 2 | **verified** | Devkit stack up on Erik's WSL2 (trial license). Through the studio admin API: MCP server `Safe Scribe` (`6abc182dff750d428ab8eae9`, Http, `http://host.docker.internal:8090/mcp`), provider `6abc182dff750d428ab8eaee`, scope `safe-scribe-lineage` `6abc182dff750d428ab8eaf4` attached to workspace `extension-dev`; ticket `extensiondev-1` lists tool prefix `mcp__Safe_Scribe__`. Dashboard log: devkit agent container completed `initialize` 200 / `initialized` 202 / `tools/list` 200 and selected `mcp__Safe_Scribe__who_saw_identifiers`. 13:5x: Erik sent the question from the studio UI on ticket `extensiondev-1`, approved the tool call, and the devkit agent returned `{"agents":["Critic","Desk","Scribe"]}` from the dashboard bound to live Aura (human approval in the studio). | Erik (JV-98) | Demo beat 7 = Erik approves the tool call in the studio. WSL notes in `sponsor-integrations.md`. |
| Plaud | cut | attempted | no device | | Synthetic audio via xAI TTS instead; any recording that becomes text works. |
| UserTesting | cut | not used | | | |
| faster-whisper | local | **verified** | 12:55 on Jaiven's laptop: `handoff_2.wav` → transcript with the `base` model, planted name/DOB/unowned line survive (drug names mangled at `base`, `small` recommended). Upload page + Desk inbox watcher (PRs #26, #33, #35). | Jaiven (JV-106) | Not a sponsor; the "audio never leaves the laptop" beat. |
| xAI | dev tooling | used | Text-to-speech built the four synthetic fixtures (`scripts/make_fixtures.py`, JV-109/114). | Erik | Not claimed as a product integration. |

## Change log

- 2026-09-29 14:00 PDT: freeze sweep. Band verified through APPROVE and the approved-room boundary (cases a9806e53, 84cfeb33); Neo4j Aura verified with the real store, room-driven write pending the code-freeze run; DuploCloud verified (wired) via studio admin API + MCP handshake; Nebius and Vultr attempted; OpenRouter not used; drug research built and gated off for the recording.

- 2026-09-29 11:50 PDT: Crusoe verified (13/13 tool calling). Band and Neo4j mocked with real code paths.

- 2026-09-29 11:15 PDT: pivot to Safe Scribe. Merge.dev cut; Band boundary room now core; Neo4j gains lineage edges.

- 2026-09-29 10:58 PDT: Crusoe tool-calling checker landed (JV-97); still no key.

- 2026-09-29 10:50 PDT: ledger created; everything deferred pending keys.
- 2026-09-29 12:48 PDT: Band verified live (five agents registered, BRIEF/VETO/OWNER_REQUEST observed, no APPROVE yet); Brave verified live via PR #27; faster-whisper local transcription in PR #26.
