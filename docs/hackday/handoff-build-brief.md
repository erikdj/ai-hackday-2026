# ASTRA (Codex) — BUILD BRIEF: HANDOFF — The AI Conference Hack Day 2026 — laptop-only edition

> Revision 2 (11:10 PDT). Supersedes `hallway-build-brief.md`. Erik kept the tool composition and changed the business case to healthcare + data sovereignty. **Skeleton unchanged.** Phase issues JV-105..108 keep their numbers and cut lines.

You are Astra, running in Codex. You are the builder. Claude Code is your design partner on AgentBridge — it comes up with ideas and reviews your work; you write and run the code. Two humans, Erik Jones (lead) and Jaiven Spence, are next to you. 4 hours of wall clock. Everything gets built on two laptops with self-serve accounts. No sponsor booths, no waiting on a human to hand us anything. If a tool needs a rep to provision it, it is out.

Read this whole brief before touching a file.

## 0. What we're optimizing for (verified on the HackerSquad dashboard)

- Overall 1st / 2nd / 3rd — $5,000 / $3,000 / $2,000 — funded by Crusoe. Must use Crusoe to qualify.
- Best Use of Band — $1,000. Agents must coordinate through a Band room such that removing Band breaks it. Judges want ≥1 of: dependent handoffs, runtime recruitment, enforced visibility boundaries, a critic that can veto. They want to see the live room and execution events. An orchestrator calling agents in sequence, or status posting, does not count.
- Best Agent Overall — DuploCloud — $750. Must run live during judging.
- Most Sponsor Tools Meaningfully Integrated — DuploCloud — $750. Unused-but-connected doesn't count.
- Neo4j — $500 / $400 / $300 in Aura credits.
- (Plaud $1,500, Vultr LEGO — Plaud needs a device we don't have; skip it.)

Buyer and pain: clinics want AI scribes but cannot send PHI to a hyperscaler LLM API and cannot prove afterwards who saw what. HANDOFF: inference on Crusoe (US-hosted, sovereign), a boundary Band enforces, a lineage graph a compliance officer can query.

Crusoe and Band are the spine. Everything else attaches to the spine and gets cut before the spine does.

## 1. The idea — decided, not swappable

HANDOFF. A nurse-to-nurse shift handoff recording (.wav transcribed locally with faster-whisper, or a .txt fixture; synthetic patient, stated on screen) becomes a Band case room where agents on Crusoe extract a quoted clinical brief → recruit a researcher only if a drug is named → a Critic on a different model family blocks unsupported claims, unowned follow-ups, and any direct identifier trying to leave the room → only then do the graph-writer and the closer get let in, and Neo4j records exactly which agent saw which field.

The two re-targeting lines:

1. **Input:** nurse-to-nurse shift handoff, `.wav` transcribed on-device (say on screen: zero bytes of audio left this laptop) or `.txt`. Synthetic patient.
2. **Critic rule:** every claim carries a verbatim quote; every follow-up names an owner; **no direct identifier (patient name, DOB, MRN, phone, address) may appear in anything destined for the outbound room**; APPROVE names the exact brief revision. Programmatic identifier check (identifier list from the transcript + DOB/MRN/phone regex) plus model judgment.

The domain is decided. Nobody swaps the skeleton: Band room per case, Crusoe as every agent's brain, runtime recruitment, a Critic with a real veto, Neo4j as memory and lineage. If anyone proposes something that breaks the skeleton, say no and cite this line.

## 2. The crew and the room protocol (build exactly this)

Six Band agents, each its own Python process with its own Band agent_id + api_key (free tier allows 10). Never name an agent "Assistant", "AI", "Bot" or "Agent" — Band treats those as role tokens.

| Agent | Crusoe model | Job | Band tools |
|---|---|---|---|
| Desk | fast | Trip-wire. Watches inbox/ for a new .txt/.md/.wav (a tiny FastAPI upload page writes there). Transcribes .wav locally with faster-whisper and logs "0 bytes of audio left this machine". Assigns the patient's stable `pseudo_id` (salted hash of the spoken direct identifiers, computed and stored only on the laptop) and passes it with the transcript. Creates case-<slug> room, adds Scribe + Critic, posts the transcript, @Scribe extract. Desk sees identifiers by definition and is recorded in lineage as such. | band_create_chatroom, band_add_participant, band_send_message |
| Scribe | strong | Extracts HANDOFF brief (JSON): patient (pseudonymous id only), meds, allergies, pending results, findings, follow-ups; every item carries a verbatim quote. If a drug is named → band_create_chatroom(case-<slug>-research) → band_lookup_peers → band_add_participant(Researcher, research room) → posts **drug names only** there → waits for the fact or an explicit failure → relays the fact into the case room. Then @Critic review. On VETO: redacts identifiers itself; for an unowned follow-up it @mentions the human charge nurse in the room and records the owner they name, with the room message as provenance. Never invents an owner. Posts a new revision number each time. | band_create_chatroom, band_lookup_peers, band_add_participant, band_send_message, band_send_event |
| Researcher | strong | Recruited at runtime only when a drug is named, into the **research room**, never the case room. Sees drug names only. Brave Search for one sourced interaction/guideline fact. Posts ENRICHMENT with URL in the research room; Scribe relays it. Lineage: Researcher has no ACCESSED edge to any identifier field, and the query proves it. | band_send_message, band_send_event |
| Critic | different family from Scribe | The veto. Programmatic + judgment: every quote must be a normalized substring of the transcript; every follow-up needs an owner; every enrichment fact needs a URL; **no direct identifier in the outbound brief** (identifier list pulled from the transcript + DOB/MRN/phone regex). Posts VERDICT: APPROVE <revision> or VERDICT: VETO + numbered reasons. VETO → @Scribe fix (max 2 rounds, then escalate to the human in the room). An unowned follow-up is never auto-assigned: Scribe asks the human charge nurse in the room; the Critic accepts an owner only if a room message from a human names one, and records that message as provenance; otherwise the item stays `unresolved` and APPROVE lists it as such. APPROVE → posts the redacted brief **plus an access manifest** (one entry per actual message delivery per room: which agent received which field, for what purpose, when; in the case room that is Desk, Scribe, Critic) into the **approved room** (`case-<slug>-approved`, the boundary room where Grapher and Closer live). Grapher and Closer never enter the case room. | band_create_chatroom, band_add_participant, band_send_message, band_send_event |
| Grapher | fast | Lives in the approved room only; never sees the transcript. Writes the redacted brief to Neo4j plus lineage: (Agent)-[:ACCESSED {field, purpose, ts}]->(Field) from the Critic's access manifest (actual deliveries, never assumed), plus its own edges to redacted fields. Identity is the stable `pseudo_id` Desk assigns on the laptop (salted hash of the spoken direct identifiers, mapping never leaves the laptop and never enters the graph); Grapher MERGEs Patient on `pseudo_id` only. Nebius embeddings + vector index only suggest "possible prior encounter" candidates for a human to confirm. Posts merged vs. new. | band_send_message, band_send_event |
| Closer | strong | Lives in the approved room (the boundary room shared with Grapher) that only ever receives the redacted approved brief and the manifest, never the transcript. STRETCH after 14:00: registered under Erik's second Band account and added by contact request (the cross-account signal). Drafts the discharge follow-up from that brief (and Researcher's fact: dependent handoff). Posts the draft. Its room history must contain no transcript and no name. | band_send_message, band_send_event |

Band signals this hits and how the demo proves each:

- **Dependent handoff** — Closer's draft changes with Researcher's findings. Prove: run one case with a drug named, one without; the drafts differ.
- **Roster decided at runtime** — a research room with Researcher appears only when a drug is named; the approved room with Grapher and Closer is created only after APPROVE. Prove: the room list visibly grows mid-case, and the case room's roster never includes Grapher or Closer.
- **Verdict that can be blocked** — Critic vetoes twice: (1) "someone should call the daughter about discharge" has no owner: Scribe asks the human in the room, Erik (as charge nurse) replies "I'll own it", Scribe records the owner with that message as provenance; (2) the hero veto: patient name + DOB in the outbound brief; Scribe redacts. APPROVE names the revision. Nothing reaches the boundary room before that. Humans and agents in one room is the point.
- **Boundary Band enforces** — CORE (phase 3, by 13:45): the approved room is the boundary; room membership is what Band enforces. Closer and Grapher live there; it only ever receives the redacted approved brief and the manifest, never the raw transcript. Prove: open that room's history on screen; no transcript, no name. STRETCH after 14:00 with everything green: Closer under Erik's second Band account via contact request (cross-account boundary).

Delete test: rip out Band and there's no room, no roster, no gate, no veto. Do not build any fallback orchestrator that calls agents in sequence. Emit Emit.THOUGHTS and Emit.TOOL_CALLS on every agent so the room shows tool calls live.

## 3. Crusoe is the brain of every agent

- Endpoint https://api.inference.crusoecloud.com/v1 — OpenAI-compatible. Env CRUSOE_API_KEY.
- Getting the key without talking to anyone: (1) check the event Discord pins/announcements for a Crusoe hackathon key or promo — that's where foundation sponsors put them; (2) in parallel, sign up at the Crusoe Cloud console → Intelligence Foundry → Models → Get API Key. Whichever lands first wins. If neither lands by T+0:30, tell the humans that a 2-minute stop at the Crusoe table is the only booth visit this plan needs — it's worth $10,000.
- Run `python3 scripts/check_crusoe_tools.py --max 20` (on main) the moment a key exists; it lists the catalog, probes tool calling, and recommends fast/strong/critic with the critic from a different vendor. Copy ids verbatim from its table. Never guess an ID.
- First 10 minutes: smoke-test tool calling on two candidates with a 3-line script. Band's platform tools are function calls; a model that can't tool-call reliably kills the whole thing. Pick one strong model (Scribe/Researcher/Closer), one fast (Desk/Grapher), one different family for Critic.
- Wire through Band's LangGraphAdapter(llm=ChatOpenAI(base_url=CRUSOE, api_key=..., model=...)) — the documented Band quickstart with the base URL swapped. Don't invent an adapter.
- One llm(role) factory in common/llm.py. Fallback chain for agents that hold the raw transcript or identifiers (Desk, Scribe, Critic): Crusoe model A → Crusoe model B → **fail closed** (post "inference unavailable, case paused" to the room; never an external provider). OpenRouter is reachable only from the dashboard's ask-the-graph over the pseudonymized graph, and from Grapher or Closer in the approved room if both Crusoe models are down (their input is already redacted); log that in red. At demo time the Critic and at least three workers must be on Crusoe.

## 4. Tool map — self-serve only

Tier 1 = must ship. Tier 2 = ship by T+3:00. Anything not working 20 minutes after you start it gets cut and listed in README under "Attempted."

| # | Tool | Tier | Role | Delete test | How we get it (no humans) |
|---|---|---|---|---|---|
| 1 | Crusoe | 1 | Inference for all six agents | No brains | §3 |
| 2 | Band | 1 | Rooms, roster, gate, veto, live events | No coordination | Free signup at app.band.ai → Agents → Remote Agent ×6 → copy UUID + key (shown once) into agent_config.yaml. pip install "band-sdk[langgraph]". One WebSocket per agent_id. |
| 3 | Neo4j | 1 | Clinical memory + access lineage | No memory across encounters and no proof of who saw what | Aura Free, self-serve. Schema: (:Patient {pseudo_id}), (:Encounter {id, at})-[:OF]->(:Patient), (:Encounter)-[:FOUND]->(:Finding {quote}), (:Encounter)-[:ON_MED]->(:Med), (:Commitment)-[:OWNED_BY]->(:Staff), and lineage (:Agent)-[:ACCESSED {field, purpose, ts}]->(:Field). Vector index on Patient.embedding (pseudonymous). One schema.cypher, MERGE everything. Canned queries: which agents saw identifiers? (expected: Desk, Scribe, Critic only); open follow-ups by owner; this patient's prior encounters. |
| 4 | OpenRouter | 2 | Dashboard "ask the graph" over the **pseudonymized graph only** + last-resort fallback | No natural-language graph Q&A | Self-serve, https://openrouter.ai/api/v1, OPENROUTER_API_KEY, $5 credit. Keep it off the agents' primary path so Crusoe stays central. Never sends identifiers. |
| 5 | Nebius | 2 | Embeddings that **suggest** possible prior encounters of the same patient (pseudonymous fields only), shown to the human as candidates | No "you may have seen this patient before" hints | Nebius AI Studio, self-serve signup with starter credit, OpenAI-compatible. List embedding models via /v1/models, copy the ID. Similarity never merges: the graph MERGEs only on `pseudo_id`; cosine ≥ 0.92 posts "possible prior encounter" candidates for a human to confirm. |
| 6 | Brave | 2 | Researcher's drug interaction/guideline fact with URL | Critic can't verify enrichment | Brave Search API free plan, self-serve (may ask for a card, $0). Header X-Subscription-Token. Top 5 {title,url,snippet}. Query is the drug name only. Mock first. |
| — | Merge.dev | cut | — | — | No healthcare fit. Listed in README as "not attempted — cut at pivot." |
| 8 | Vultr | 2 | Hosts Scribe, Critic, Grapher, Closer and the dashboard | Demo depends on a laptop | Self-serve (card). Check Discord for a Vultr credit code. One VM, Docker Compose. **Desk, the upload page, and faster-whisper stay on the presenting laptop**; only text crosses to the Band room. That is what makes "zero bytes of audio left this laptop" true. Ship the compose file at 12:45 even if deploy is later. |
| — | Similarweb | only if a key is pinned in Discord | Company traffic + similar sites → SIMILAR_TO edges | — | Enterprise key; no self-serve path. If a hackathon key is posted, 20-minute cap. Otherwise "Attempted." |
| — | Plaud, DuploCloud, UserTesting | cut | — | — | Need a device or a provisioned tenant. Listed in README as "not attempted — required sponsor provisioning." |

Seven real integrations, each doing a job. That's a strong "most tools" entry without a single booth visit. The humans fill the sponsor feedback forms on the dashboard for points while you build — remind them at T+2:00 and T+3:30.

## 5. Build order

**T+0:00 → 0:20 — Scaffold + accounts in parallel.**

```
hallway/
  common/llm.py            # Crusoe factory + fallback chain
  common/band_cfg.py
  agents/desk.py scribe.py researcher.py critic.py grapher.py closer.py
  ingest/transcribe.py     # faster-whisper, local
  research/brave.py
  graph/schema.cypher graph/neo4j.py graph/embed.py
  dashboard/app.py         # FastAPI: upload page, room link, graph viz, ask-the-graph
  fixtures/handoff_1.txt handoff_2.txt handoff_2.wav   # handoff_2 plants full name + DOB early and "someone should call the daughter about discharge" with no owner
  inbox/  docker-compose.yml  .env.example  README.md  DEMO.md  Makefile
```

Write fixtures/ first. Humans create accounts in this order: Crusoe (done), Band (6 agents; Erik's second account only for the stretch), Neo4j Aura, then OpenRouter, Nebius, Brave, Vultr. Secrets live in Doppler `ai-hackday-2026/dev`; model pins are overseer-owned config there. You build against mocks (MOCK=1 per integration) until each key lands.

**11:50 PDT — The spine. Cut line #1 (JV-105).** Desk + Scribe + Critic on Crusoe, in a Band room, on `fixtures/handoff_2.txt`. Both vetoes (unowned follow-up, identifier in outbound) → fix → APPROVE <revision> loop works. Events visible in the Band web app. Draft PR open under `hallway/` (or `handoff/`). If this isn't green at 11:50, stop everything else and fix it.

**12:45 PDT — Memory + lineage. Cut line #2 (JV-106).** Grapher writes clinical nodes and ACCESSED edges to Aura; "which agents saw identifiers?" answers Desk, Scribe, Critic. Local .wav → faster-whisper → inbox works. Ship docker-compose.yml.

**13:45 PDT — Approved room + recruitment (JV-107).** Closer and Grapher in the approved room that only receives the redacted brief; its history shows no transcript and no name. Second Band account is stretch after 14:00. Researcher via Brave, recruited only when a drug is named. Closer draft uses the fact. Nebius same-patient dedupe if time allows.

**14:00 PDT feature freeze — Dashboard, deploy (JV-108).** Dashboard: upload page, Band room link, lineage query, graph viz (neovis.js is fine), OpenRouter ask-the-graph over the pseudonymized graph. Deploy compose to Vultr.

**14:00 → 14:40 PDT — Harden, code freeze at 14:40.** Run the full path three times. Retries on every network call. Write DEMO.md. Stretch only if rehearsals are clean: live mic on stage.

**14:40 → 15:10 PDT — Record demo + technical dive. 15:25 submitted.** HackerSquad: save project (name, README, stack checkboxes, git remote) → record demo video → submit. Submit is locked until save + video are done. Not the last 5 minutes.

## 6. Working with Claude Code on AgentBridge

- Claude Code owns: idea/domain choice (first 15 min), README narrative, demo script, code review on request. You own: every file, every test, every deploy.
- Post to the bridge every 15 minutes, ≤5 lines: green / red / need-from-human. Same summary goes to the humans.
- Ask Claude Code for a decision only when two options are both viable and the choice is about the product, not the code. Give it a 5-minute window; if no answer, take the option closest to this brief and move on. Never block on the bridge.
- If Claude Code's review says "rewrite X," do it only if X is red or blocks the next cut line. Style notes wait until T+3:15.
- Anything Claude Code proposes that breaks the skeleton in §1: decline, quote the line, keep building.

## 7. Operating rules

- Vertical slice first. Two agents talking on Crusoe in a Band room beats six half-built agents.
- Mock every external API on first contact. Real key lands → flip the flag → verify → move on.
- One file per agent, one file per integration. Dependencies: band-sdk, langgraph, langchain-openai, openai, neo4j, fastapi, httpx, faster-whisper. Nothing else without a reason in the commit message. No base classes, no plugin systems, no config loaders.
- Every network call: 10s timeout, 2 retries, log the failure with the tool name.
- Commit every 15 minutes with a message that says what works now. Push to the remote the humans put in HackerSquad.
- make demo runs fixtures/handoff_2.txt end to end and prints the room URL, the lineage query result (Desk, Scribe, Critic), and the boundary room URL. Red make demo = no new features.
- Announce cuts immediately and add them to README "Attempted." Honest scope beats broken scope.
- Don't fake the demo. No hard-coded verdicts, no pre-baked graph. The vetoes come from the real recording: Erik says the synthetic patient's full name and DOB early, and "someone should call the daughter about discharge" with no owner, on purpose. Never manufacture a bad quote to stage a veto.
- Ask the humans one thing at a time, with the exact URL and button.
- Every claim in the README maps to a file that's actually called. The "most tools" judge will check.
- Keep the spine on Crusoe. If the logs show OpenRouter carrying the demo, fix Crusoe — don't hide it. Transcript-bearing agents fail closed rather than fall back.
- Audio never leaves the laptop: Desk + faster-whisper + the upload page run locally in every topology; the compose file on Vultr does not contain Desk.
- Fifteen minutes per bug, then change approach or cut.

## 8. Demo (2 minutes, live)

1. Erik drops the .wav recorded this morning on the upload page. Desk transcribes on-device. Say: "zero bytes of audio left this laptop." Log shows the Crusoe model id.
2. Screen is the Band room, not the dashboard. case-… appears. Scribe posts the HANDOFF brief with quotes. Execution events stream.
3. A research room opens — Researcher is recruited because a drug was named, sees only the drug names, posts one fact with a URL; Scribe relays it into the case room.
4. Critic: VETO 1 — "follow-up #2 has no owner." Scribe asks the room; Erik types "I'll own it"; Scribe records the owner with that message as provenance. Critic: VETO 2 (hero) — "patient name + DOB in outbound." Scribe redacts. Critic: APPROVE revision 3. The approved room appears with Grapher and Closer; the redacted brief and the access manifest cross into it. The case room's roster never changes.
5. Grapher, from the approved room, writes Neo4j including ACCESSED edges from the manifest. Dashboard: "which agents saw identifiers?" → Desk, Scribe, Critic. Grapher, Researcher, Closer absent.
6. Closer, in the same approved room, drafts the discharge follow-up from the redacted brief only. Open that room's history: no transcript, no name. (Stretch: Closer is under a second account.)
7. Close: "Audio never left the laptop. Text only touched Crusoe. Nothing identifiable crossed the boundary; Band enforced it, Neo4j proves it. Seven sponsor tools, each with a delete test in the README, all self-serve, built by two people and two agents in four hours."

## 9. Definition of done

- make demo green from a clean clone with real keys.
- Deployed on Vultr; Band room opens from the dashboard.
- Both Critic vetoes → fix → APPROVE <revision> observed on a real recording.
- Neo4j answers "which agents saw identifiers?" with Desk, Scribe, Critic only (Grapher, Researcher, Closer absent); ≥2 encounters linked to one patient by `pseudo_id`, never by similarity.
- Transcript-bearing agents fail closed when Crusoe is down; no external provider ever receives identifiers.
- Approved (boundary) room history contains no transcript and no name; Grapher and Closer were never in the case room.
- README: ASCII architecture diagram, tool table with delete tests, "Attempted" section, run instructions.
- HackerSquad: saved, video uploaded, submitted, feedback forms done.

Start now. First action: post "Astra online — re-targeting to HANDOFF" to the bridge, open the Draft PR, write fixtures/handoff_2.txt.
