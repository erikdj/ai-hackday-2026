# Safe Scribe by TrustEdge AI

Safe Scribe turns a synthetic nurse-to-nurse handoff into a Band case room where
agents on Crusoe review evidence before approval. A separate approved room gates the
Grapher write; optional drug-only research adds sourced context.

**Every patient in this repository is synthetic.** Names, dates of birth, record numbers and phone
numbers in `hallway/fixtures/` are invented (see `hallway/fixtures/README.md`). Say so on screen.

## Verified live evidence

Case `19ecdb31-2006-4284-acd3-0a6c22d1a6e0` completed the live Band/Crusoe
veto, human ownership, approval and real graph-write path. The source was an atomic local text upload of `handoff_2`, not audio or Plaud:

| Evidence | Observed result |
| --- | --- |
| VETO `18c8fe26-664a-4ab2-bc44-520aca503b1d` | Critic rejected the unowned follow-up. |
| Human reply `92ce7975-3ad3-41c1-af0a-0e8e7c31116d` | Erik said “I'll own that” at 13:21 PDT, mentioning both Scribe and Critic. The original reply was recovered at 13:39; no replacement ownership was fabricated. |
| BRIEF revision 2 / APPROVE verdict `82c1f9ca-6000-411d-9445-b6141b4496bb` | Revised ownership led to Critic approval. |
| APPROVAL `006950b2-6397-4475-94b1-c40f712ca00f` | Authenticated approval record for the revised brief. |
| Approved room `4704ff81-f261-4cba-84ba-6c79e75aa06f` | Separate downstream room received the approved payload. |
| Real graph receipt `e02d4a4b-e543-43b1-866e-70358731a12e` | Real Neo4j write; `merged: false` for this encounter. No deduplication success is claimed. |
| Research room `6ebcdfae-eb57-4365-b030-10fe3ccaa9f3` | Runtime recruitment produced three real Brave facts with source URLs (enrichment `3ebd9770-41ff-4b5b-8799-518dd579fe1c`) before research was disabled for the recording preset. |

The lineage query returned `critic`, `desk`, and `scribe` runtime field-processing
roles. This is processing provenance, **not proof a human read identifiers**. The
Band manifest retains the source-message evidence. PRs #42 and #43 are merged.
Historical network/delivery delays mean this run **did not meet 90 seconds**.
A successful write does not establish the timing target, Vultr deployment, or event
submission. The three timed rehearsals in [DEMO.md](DEMO.md) remain unrecorded.

Text-upload intake was verified on this path. Audio/Whisper verification is separate
Claude-owned evidence; this case must not be presented as proof of an audio run.
Run `make check` for the current offline test count; offline tests are not live evidence.

## Coordination and boundaries

Band carries authenticated transcript, brief, owner request, verdict and approval
messages. Delete Band and the agents have no coordination channel. Every agent's
model runs on Crusoe; inference fails closed after the configured Crusoe fallback.
Critic checks quoted evidence, ownership and recognized identifiers. An unowned
follow-up is assigned only from an authenticated human reply or retained as unresolved.
The identifier guard is a regex/list demonstration, not certified de-identification.

```text
Local text upload -> Desk -> Band case: Desk, Scribe, Critic, human
                                | VETO -> human reply -> revised brief -> APPROVE
                                | optional drug-only room: Scribe, Researcher
                                v
                            approved room: Critic, Grapher, human -> Neo4j
```

The research room receives supported drug names and a routing ID, not the transcript.
Grapher receives the approved redacted payload in a separate room, never case membership.
Closer is deferred.

| Tool | Implemented role | Evidence / limit |
| --- | --- | --- |
| Crusoe | Agent inference (`common/llm.py`) | Live extraction and review observed. |
| Band | Rooms, roster, gate and events (`common/room.py`, `common/runtime.py`) | Live veto, ownership repair and approved boundary observed. |
| Brave | Drug facts (`research/brave.py`, `common/research_room.py`) | Three sourced facts in research room `6ebcdfae-eb57-4365-b030-10fe3ccaa9f3`; disabled only in recording preset. |
| Neo4j | Graph persistence and processing provenance (`graph/neo4j_store.py`) | Real receipt `e02d4a4b-e543-43b1-866e-70358731a12e`; this run did not merge a previous encounter. |
| Vultr | Compose deployment configuration | Deployment not established by the evidence above. |
| DuploCloud | Studio agent calls the dashboard MCP lineage tool (`dashboard/mcp.py`) | Separately verified on Erik's WSL2 trial devkit: after human approval, `who_saw_identifiers` returned Critic, Desk and Scribe from live Aura. See the [integration ledger](../docs/hackday/integration-ledger.md); this is MCP use, not deployment of the Safe Scribe stack. |
| Other sponsors | See Attempted / cut and the integration ledger | No additional sponsor-use claim from this run. |

## Run

Run these commands from the repository root.

The coordinated inference-only amendment sets both Crusoe clients to a 30-second timeout with one retry; Band REST/search remain at 10 seconds with two retries, and the live demo deadline remains 90 seconds.

Optionally set `CRUSOE_DISABLE_THINKING_MODELS` to comma-separated exact model IDs verified to
support `enable_thinking=false`; its blank default leaves model behavior unchanged.

```sh
make install
make check                      # offline protocol tests, no network
doppler setup                   # ai-hackday-2026 / dev; see docs/hackday/secrets.md
doppler run --no-fallback -- make demo         # real Crusoe + Band credentials required; red otherwise
```

Desk runs on the presenting laptop in every topology, never on the Vultr VM, so audio stays local. Text is explicitly sent to Band and Crusoe. Start Desk with
`doppler run --no-fallback -- .venv/bin/python -m hallway.agents.desk`; start Scribe and Critic in separate terminals with
`doppler run --no-fallback -- .venv/bin/python -m hallway.agents.scribe` and `doppler run --no-fallback -- .venv/bin/python -m hallway.agents.critic`. The
Compose file deliberately omits Desk. Its default services are Scribe and Critic; the `phase2` profile adds Researcher and Grapher. Closer remains in the separate `deferred` profile.

For a deliberately offline unit-test harness, run:

```sh
MOCK_BAND=1 MOCK_CRUSOE=1 make demo
```

It prints `OFFLINE HARNESS`, runs synthetic protocol tests against a Band double and mocked
model responses, and explicitly reports no live sponsor evidence. It does not process the selected
fixture as a live end-to-end run. Mixed mock/live flags are rejected; a failed live run never
switches to this harness. Set both flags to `0` for live operation.

Doppler supplies `CRUSOE_API_KEY`, exact model IDs and `BAND_<ROLE>_AGENT_ID` /
`BAND_<ROLE>_API_KEY`. Each process needs its own API key and the three case-role IDs. Legacy
`agent_config.yaml` remains an optional local fallback when environment credentials are absent.
A partially configured environment credential pair fails closed. The cloud Compose configuration
passes each service only its own Band key; no secret-file mount is required. To avoid Docker
Compose reading a legacy `.env` during interpolation, start cloud services with
`doppler run --no-fallback -- docker compose --env-file /dev/null up -d`. Docker deployment
has not been verified in this checkout. `--no-fallback` disables Doppler secret-cache files.

For five-agent operation, keep Desk on the laptop and run the four cloud roles with
`doppler run --no-fallback -- docker compose --env-file /dev/null --profile phase2 up -d --build`.
Configure `ENABLE_APPROVED_ROOM=1` and `ENABLE_DRUG_RESEARCH=1` in Doppler, all five
Band agent IDs and each running role's own key, plus `BRAVE_API_KEY` and
`NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD` (`NEO4J_DATABASE` is optional).
Use `MOCK_BRAVE=0` and `MOCK_NEO4J=0` for live evidence. Compose passes Brave credentials
only to Researcher and Neo4j credentials only to Grapher; it passes no human API key,
Desk watcher configuration or local pseudonym salt. Starting the profile does not turn
on the feature flags automatically. Do not start a second copy of an already connected
agent ID; coordinate the handover with the operator between cases. These are deployment
instructions, not evidence of a Docker build or a live deployment.

Create a Band lobby containing Desk and the human operator; copy its ID to `BAND_LOBBY_ROOM_ID`.
`make demo` requires `BAND_HUMAN_API_KEY` to send the authenticated intake request. Alternatively,
run `doppler run --no-fallback -- .venv/bin/python -m hallway.demo --watch-only` and follow the printed command in Band,
mentioning Desk. Reply to owner requests mentioning both Scribe and Critic so both can verify the
human message. The observer requires matching approval, boundary and real graph evidence within
its 90-second deadline; the historical completed case exceeded that deadline.


## Fixtures

From `hallway/fixtures/README.md` (Erik's PR #9): `handoff_1` prior encounter, all follow-ups owned;
`handoff_2` the demo (name + DOB, warfarin + ciprofloxacin, unowned daughter call); `handoff_3`
boundary stress (spoken MRN and phone, one unsupported claim, unowned nutrition consult).
Agents read `fixtures/<name>.txt` by name; `handoff_2` is the default.

## Attempted / cut

- Merge.dev: cut at the pivot, no healthcare fit.
- Plaud: cut; no device was available. Case `19ec` used text intake.
- UserTesting: not used.
- Emit.THOUGHTS: not supported by the Band LangGraph adapter (`SUPPORTED_EMIT` is tool calls and
  usage); explicit `thought` events are posted through `band_send_event` at each protocol step instead.


### Opt-in approved room and Grapher (JV-106)

Set `ENABLE_APPROVED_ROOM=1` on Critic and configure the Grapher peer ID; run the
Grapher process separately. Default remains the case-only phase 1 behavior. After
approval, Critic creates a separate `Safe Scribe approved <id>` room containing
Critic, Grapher and the initiating human. Only the redacted approved brief crosses;
Grapher never joins the case room. Closer recruitment is not part of this slice.

Grapher calls the existing graph store with the case room ID as the stable encounter
ID. `MOCK_NEO4J=1` remains explicitly mock and posts `MOCK_GRAPH_WRITTEN`. Without
mock mode, missing `NEO4J_URI` fails closed instead of silently using memory. A mock
receipt never suppresses a later real write. Case `19ec` verified an actual Neo4j write;
offline tests separately mock the graph API and Band transport.

The manifest records observed, authenticated Desk intake, Scribe extraction and
Critic review messages. It is **processing provenance, not delivery/read proof**.
No identifier-field access edges are invented; the real `who_saw_identifiers()`
result may be empty and is labeled as a global query across all encounters. The
existing graph store retains agent/field/purpose/timestamp but not source message
IDs; those remain in the Band manifest. Runtime-generated ISO processing timestamps
are appended after identifier checks to avoid confusing transport dates with DOBs.

Band checkpoints resume room delivery on retry and graph writes use stable MERGE
keys. A crash immediately after room creation can leave an empty orphan room before
its checkpoint exists. A graph call timeout emits no success receipt; its worker
thread may still complete, so a later retry can safely rewrite the same encounter.

The live demo observer now waits for an authenticated boundary checkpoint, matching Critic approval, and a real `GRAPH_WRITTEN` receipt with the actual lineage query result. Mock graph receipts never pass. Success is labeled **phase 2 verified**, not completion of Researcher, Closer, or event submission requirements.
## Drug-only research helper (JV-107)

`hallway/common/research_room.py` recruits Researcher into a separate Band room only for
supported, transcript-backed medication names. The request carries those names and an opaque
routing UUID, never the transcript or patient identity. Scribe validates and relays source URLs
back into the case; Critic waits for that relay or an explicit failure. The small medication
vocabulary skips unsupported names explicitly. Recruitment resumes from a Band checkpoint.

Brave results count as live evidence only when their own metadata says `mock: false` and
`source: brave`; missing keys and mock results produce no evidence. Focused offline tests
cover the boundary and retries. Live research room `6ebcdfae-eb57-4365-b030-10fe3ccaa9f3` produced three sourced facts
in the `19ec` case; mock outputs do not count toward that evidence.

New Scribe publication and Critic review tools record the identifier field categories they processed against the authenticated Desk source message. The boundary verifies these runtime records and emits only field labels and evidence IDs. This is tool/runtime processing evidence, **not human reading or Band delivery measurement**. Legacy or mismatched metadata remains unverified and blocks full phase-2 observer success. Detection is conservative and does not certify complete identification. The graph query is global; current-case proof comes from the matching approved manifest.

Set `ENABLE_DRUG_RESEARCH=1` on Scribe, Critic and Researcher to activate the separate drug-only room. Runtime tool wiring now starts recruitment after Scribe publishes, dispatches research-room messages to the relay, and prevents Critic approval until an authenticated result or explicit unavailability arrives. Mock search facts are never propagated as evidence. Live research was observed in room `6ebcdfae-eb57-4365-b030-10fe3ccaa9f3`. For the current recording preset, set
`ENABLE_DRUG_RESEARCH=0`; this disables recruitment for that run without removing the integration.
Keep `ENABLE_APPROVED_ROOM=1` for the approved-room and graph path.

Desk local inbox intake is opt-in with `ENABLE_LOCAL_INBOX=1`, `SAFESCRIBE_INBOX`
(default `inbox`), and `BAND_CHARGE_HUMAN_ID` set to an actual User in the lobby.
The watcher shares Desk's started Band client; no second WebSocket or local agent
orchestrator is created. Its upload producer must atomically rename completed
`.txt` files; `.part` files are ignored. Other roles never run this watcher.
Research recruitment interrupted after BRIEF publication can be resumed by the
case-bound `band_start_research` tool without creating another brief revision.
