# Safe Scribe by TrustEdge AI

**A clinical handoff scribe where the agents argue before they commit, nothing identifiable leaves
the room, and the system can prove who saw what.**

Built in one day at The AI Conference Hack Day 2026 (San Francisco, September 29, 2026) by Erik
Jones and Jaiven Spence, TrustEdge AI / Jacobian Engineering, with their agent teams. Every patient
in this repository is synthetic. This README is the pitch and the directory; the recorded demo and
its script are in [docs/hackday/demo-script.md](docs/hackday/demo-script.md).

## The problem, in plain language

Nurses and doctors hand patients off to each other all day, by talking. "Mr. Callahan, born in
fifty-two, is on a blood thinner and just started an antibiotic that interacts with it; someone
should call his daughter about discharge." That spoken handoff is where things get lost: follow-ups
with no owner do not happen, details get misremembered, and writing it down takes time nobody has.

Every hospital wants an AI scribe. Compliance says no, twice. First, the audio and the patient's
identity would be shipped to a big cloud AI company. Second, afterwards nobody can prove which
systems saw the name, the date of birth, the record number. "Trust us" is not an answer an auditor
accepts.

## What Safe Scribe does

1. The recording is transcribed **on the laptop** (faster-whisper). Zero bytes of audio leave the
   machine.
2. Only text enters a **Band** case room. The room holds four members: Desk, Scribe, Critic, and the
   human charge nurse. Membership is enforced by the room, not by convention.
3. **Scribe**, thinking on **Crusoe** Managed Inference, extracts a structured brief. Every item
   carries a verbatim quote from the transcript. The patient is referred to by a locally generated
   pseudonymous id.
4. **Critic**, on a different model family (also on Crusoe) so it does not share Scribe's blind
   spots, reviews. It vetoes a quote that is not in the transcript, a follow-up with no owner, and any
   patient identifier in the outbound brief. Deterministic code checks cannot be overridden by the
   model.
5. The unowned follow-up is not guessed. Critic asks the room; the nurse types `I'll own it`; that
   human message becomes the owner's provenance. Critic approves an exact brief revision by digest.
6. Only then is a second, **approved room** created, holding Critic, **Grapher** and the nurse, and
   never the transcript. Grapher writes the pseudonymous brief to **Neo4j** together with an access
   manifest: `(Agent)-[:ACCESSED]->(Field)` edges saying which agent touched which identifier field.
7. The compliance question is answered live from the graph: *which agents saw identifiers?*
   **Desk, Scribe, Critic.** Nothing downstream. A Crusoe model turns that lineage into the
   three-sentence statement a privacy officer reads, from agent names, field names and counts only.
   Both are exposed as MCP tools registered in the **DuploCloud** studio, so another agent can ask
   them under human approval.

Every step above ran live today on synthetic case `19ecdb31` (Band room ids, Aura rows and the
studio tool result are recorded on Linear JV-116, JV-106, JV-98).

## Why these tools

| Tool | Job in Safe Scribe | Why this tool | How we know it works |
| --- | --- | --- | --- |
| **Crusoe** Managed Inference | All agent inference, plus the compliance narrative | Two model families from one catalog; a provider a hospital can contract with directly; if it is unavailable the case pauses, it never routes elsewhere | 13-model tool-calling probe, two live runs that changed the pins, every live case today, narrative live from Aura in 3.6 s |
| **Band** | The rooms and the door policy: case room, approved room, roster checks, vetoes, the human's reply as a message | Room membership is a boundary we can enforce and show, not a promise; the human is a first-class participant | Live cases `a9806e53`, `84cfeb33`, `19ecdb31` |
| **Neo4j** Aura | Pseudonymous patient memory across encounters and the access-lineage graph | The audit question is a graph question: agents, fields, and the edges between them | Live Grapher write on Aura; `who_saw_identifiers` = Critic, Desk, Scribe |
| **DuploCloud** | The lineage answer and the compliance narrative exposed as MCP tools in the studio, called under human approval | Compliance tooling should be reachable by other agents, with a human approving each call | MCP server, provider, scope and ticket registered via the studio admin API; tool call returned the live answer |
| **Brave Search** | One sourced fact per drug named in the handoff (warfarin, ciprofloxacin, enoxaparin), for the Critic to verify by URL | The interaction in the handoff is split across sentences; public evidence gets attached to the brief without the research agent ever seeing the patient | Live facts in research room `6ebcdfae` on scenario 2 |
| **Similarweb** | Legitimacy fact for a referral organization spoken in a visit | Referrals name outside organizations; a referral to a moribund or fake provider is a safety and fraud vector | Live: `sunrisehomehealth.com` unranked, ~890 visits/month, flagged for a human |
| faster-whisper (open source, not a sponsor) | Transcription on the laptop | The audio never moves | Verified on `handoff_2.wav` |

Attempted, not integrated, not counted: **Nebius** (credentials issued were object storage, not
inference) and **Vultr** (compose file ready, no host; a last-hour deploy was riskier than the
laptop). **OpenRouter** and **Merge.dev** were not used. **xAI** text-to-speech built the synthetic
fixtures and is development tooling only.

## Where the patient data goes today, and what changes for a real deployment

Three agents in one room (Desk, Scribe, Critic) see the transcript, and they run on Crusoe inside a
Band room. Grapher receives the pseudonymous brief: no identifiers, but clinical content tied to a
pseudonym, which is still PHI under HIPAA until formally de-identified. Researcher, the dashboard
narrative and the DuploCloud tools receive only drug names or lineage metadata. Today this is acceptable for
one reason: **every patient is synthetic.** Crusoe's self-serve terms exclude HIPAA-regulated data,
Band's terms are silent on it, and no business associate agreement is in place with anyone. Nothing
runs in an enclave.

What we claim is the architecture: **chosen** (the hospital picks where the room and the models
run; the endpoint is one configuration value), **minimized** (audio never moves; exactly three agents
see identifiers; room membership is the boundary), **provable** (the graph records which agent
touched which field, and a Crusoe model turns that into the sentence a privacy officer reads). For
a real deployment, every component that receives the transcript or the pseudonymous brief (Scribe,
Critic, Desk, Grapher, the Band rooms, the Neo4j store) needs a business associate agreement or a
hospital-controlled substitute; only the agents that receive drug names or lineage metadata can stay
on public serverless services unchanged. Vendor terms with sources, the gaps, and the
production checklist: [docs/compliance/hipaa.md](docs/compliance/hipaa.md). Words we do not use:
"HIPAA compliant", "de-identified", "enclave".

## Crusoe: what it does today and where it grows

Crusoe is the only inference provider in the code; if it is unavailable, the case pauses.

| Today, live | On Crusoe | Receives |
| --- | --- | --- |
| Scribe extracts the quoted brief | `zai-org/GLM-5.3`, low reasoning | transcript (PHI) |
| Desk opens the case, Critic reviews and vetoes | `Qwen/Qwen3.8-27B`, thinking off, a second model family by rule | transcript (PHI) |
| Grapher writes the pseudonymous graph through tool calls | Qwen | pseudonymous brief (no identifiers; still PHI until formally de-identified) |
| Researcher turns drug names into sourced facts | Qwen | drug names only |
| **Compliance narrative**: a three-sentence privacy-officer statement written from lineage metadata only, shown on the dashboard and served as a DuploCloud tool, with the exact payload sent | Qwen | agent names, field names, counts |

The split matters: the agents that receive the transcript or the pseudonymous brief are one
contract away from a dedicated Crusoe deployment or hospital GPUs; the agents that receive only drug
names or lineage metadata run on Crusoe serverless under today's terms, and that is where a scaled
system spends a growing share of its inference. Next on Crusoe, in order: Closer drafting
the discharge follow-up from the redacted brief in the approved room; "ask the graph" natural
language over the pseudonymous graph for the dashboard; per-shift compliance digests across
encounters; a Crusoe-served embedding model, when the catalog has one, for suggesting prior
encounters a human confirms; and the PHI-side pair on a contracted dedicated endpoint.

## What is here

```
README.md                          this pitch and directory
CLAUDE.md                          team operating rules (humans and agents)
docs/README.md                     table of contents for every document
docs/agent-instructions.md         how agents work in this repo (orchestrator, coder, reviewer)
docs/compliance/hipaa.md           HIPAA posture: what we did, vendor terms, gaps, production path
docs/hackday/                      demo script, submission README, integration ledger, sponsor wiring, event brief, build brief, secrets
docs/decisions/                    ADR-0001 operating rules, ADR-0002 tech stack
docs/reference/duplocloud-devkit/  vendored devkit docs (Apache-2.0)
hallway/                           the product (directory name predates the product name)
  agents/                          desk, scribe, critic, grapher, researcher (closer: stub)
  common/                          Band room protocol, brief schema and identifier gate, Crusoe client, runtime, research room
  graph/                           in-memory and Neo4j stores, schema.cypher
  dashboard/                       judge dashboard, lineage queries, Crusoe compliance narrative, MCP endpoint for DuploCloud
  ingest/                          local upload page, faster-whisper transcription, Desk inbox watcher
  research/                        Brave and Similarweb facts
  fixtures/                        four synthetic scenarios: script, transcript, WAV
  tests/                           spine, boundary, lineage, research, inbox tests
scripts/                           Crusoe smoke test and tool-calling probe, fixture synthesis (xAI TTS)
docker-compose.yml                 role-scoped agent deployment (phase-2 profile), unused today
backlog.md / changelog.md          what is next / what shipped
```

Test suite at the code freeze: 135 unittest (2 live tests skipped) plus 44 pytest, all green.

## Run it

```bash
doppler setup                                    # project ai-hackday-2026, config dev
doppler run -- bash scripts/check-crusoe.sh      # live Crusoe catalog and a completion
make install && make check                       # offline suite
doppler run -- .venv/bin/python -m hallway.dashboard.app   # judge dashboard + MCP endpoint on :8090
```

The agents run as Band Remote Agents, one process per role, under `doppler run` (see
`hallway/README.md`). Fixtures: `hallway/fixtures/handoff_{1,2,3}` and `visit_1`; the demo is
`handoff_2`.

## What comes next

- **Production topology.** DuploCloud's platform provisions and manages the Safe Scribe deployment
  with its HIPAA control set applied to that infrastructure, inside the hospital's cloud account or on Crusoe Cloud compute; the
  agents call a dedicated Crusoe inference endpoint under a signed agreement, or open models on
  hospital-controlled GPUs; Band under an enterprise agreement or replaced by a hospital-controlled
  room service; Neo4j Aura under a signed BAA or self-managed. To Erik's question, "would we move
  DuploCloud onto Crusoe if we did not have a local devkit": yes. The devkit is local-only by
  license; the production shape is DuploCloud managing the agents and dashboard on Crusoe compute,
  with the studio agent reaching the MCP endpoint over a private network rather than
  `host.docker.internal`.
- **Identifier gate to Safe Harbor.** Today's gate detects five categories (name, date of birth,
  record number, phone, address). HIPAA's Safe Harbor lists eighteen. Extend the detector and the
  lineage field vocabulary, and add a human review step for anything the model redacts.
- **Closer.** The discharge-follow-up drafter in the approved room is a stub; it should draft from
  the redacted brief alone, with the same roster checks as Grapher.
- **Research recruitment on by default** once the retry path merged today has a live run behind
  it; add Similarweb's organization check to the recruitment trigger.
- **Real voices, real rooms.** Human-acted recordings of the scripts; a second Band account for the
  approved room to show cross-tenant boundaries.
- **Memory across encounters on stage.** Run `handoff_1` before `handoff_2` so the second encounter
  MERGEs onto the same pseudonymous patient.

## How it was built

Two humans and three agent sessions in six hours. Every task a Linear issue, every change a pull
request, every PR reviewed locally by an independent AI reviewer (Astra via Codex CLI) before
merge, and a third Claude session acting as overseer: holding the clock, merging reviewed PRs, and
challenging any claim not backed by a live run. Doppler is the single secrets store. Forty-nine
PRs merged in the day. The integration ledger says verified, mocked, attempted or not used per tool,
with the evidence line for each. See [docs/agent-instructions.md](docs/agent-instructions.md).
