# Demo script: Safe Scribe by TrustEdge AI

Linear JV-102. This is the script for the **recorded** submission: a two-minute demo followed by a
three-minute technical dive, recorded 14:40–15:10 PDT, submitted by 15:25. Every line below
matches what was observed live by 13:05 PDT; where a beat is not yet live the fallback line is
given and must be used instead. Never say a sponsor did something it did not do on the recording.

Say once, early: **every patient is synthetic.** Names, dates of birth, record numbers and phone
numbers were invented for the fixture and spoken by a text-to-speech voice.

## One-sentence claim

A clinical handoff recording becomes a Band case room where agents on Crusoe extract a quoted
brief, a Critic on a second model family blocks unsupported claims, unowned follow-ups and any
patient identifier trying to leave the room, and Neo4j records which agent saw which field.

## Before pressing record (checklist)

- [ ] Processes on Jaiven's laptop restarted under `doppler run` on the code-freeze commit with
      pins v4 (Scribe `zai-org/GLM-5.3` low reasoning, Desk and Critic `Qwen/Qwen3.8-27B` thinking
      off). `ENABLE_APPROVED_ROOM=1` only if the 13:30 phase-2 receipt was observed live.
      `ENABLE_DRUG_RESEARCH` stays unset unless a live research run is on JV-107.
- [ ] Band: lobby renamed `Safe Scribe lobby`; no stale case rooms open on screen.
- [ ] Dashboard `python -m hallway.dashboard.app` running under `doppler run` on port 8090
      against Aura; `/mcp/health` answers.
- [ ] Terminal in `/home/erikdj/projects/ai-hackday-2026` on main; beat-5 command pasted and ready (repo `.venv`, built with `uv venv .venv && uv pip install -r requirements.txt`); `doppler run -- make demo FIXTURE=handoff_2` ready but not started.
- [ ] Windows: Band (room list visible), terminal, dashboard tab, DuploCloud studio tab.
- [ ] `hallway/fixtures/handoff_2.wav` and `.txt` at hand; the planted lines are in
      `hallway/fixtures/README.md`.
- [ ] Time a full dry run. Target: upload to APPROVE under 90 seconds. Record the number.

## Set the scene (45 seconds, before beat 1)

Say this in your own words; it is the whole case.

Nurses and doctors hand patients off to each other all day, by talking. "Mr. Callahan, born in
fifty-two, is on a blood thinner and just started an antibiotic that interacts with it; someone
should call his daughter about discharge." That spoken handoff is where things get lost: follow-ups
with no owner don't happen, details get misremembered, and writing it all down takes time nobody
has. Every hospital wants an AI scribe. Compliance says no, twice: the audio and the patient's
identity would be shipped to a big cloud AI company, and afterwards nobody can prove which systems
saw the name, the birthdate, the record number. "Trust us" is not an answer an auditor accepts.

Safe Scribe is the scribe a compliance officer can say yes to. The audio stays on the laptop. A small
team of agents works in a private room with a human nurse in it. One agent writes the summary and
quotes the transcript for every line. A second agent, on a different AI model so it doesn't share
the first one's blind spots, can block it: an unowned follow-up gets asked, not guessed; any patient
identifier in the outgoing summary gets stopped. Only after approval does a pseudonymous summary
leave the room, into a second room that never held the transcript, where it is filed as memory and
the system writes down which agent touched which piece of information. Every patient today is
synthetic. This is the second of four synthetic scenarios we wrote and voiced this morning, and it
is the one already sitting in the graph.

## Two-minute demo

| # | Time | Erik says / does | On screen | Sponsor | Fallback if not live |
| --- | --- | --- | --- | --- | --- |
| 0 | 0:00 | "Clinics want AI scribes. Compliance says no twice: data leaves for a hyperscaler, and nobody can prove who saw what. Safe Scribe is the scribe a compliance officer can say yes to. The patient you'll hear is synthetic." | Title slide or README top | | |
| 1 | 0:15 | Plays the first 20 seconds of `hallway/fixtures/handoff_2.wav`: the nurse says the patient's name and date of birth and the warfarin line. Stops it. "That name and birthdate you just heard will not appear in anything that leaves the room. The recording is transcribed on this laptop by faster-whisper; zero bytes of audio leave the machine." Runs `python -m hallway.ingest.transcribe hallway/fixtures/handoff_2.wav --inbox inbox --print`. | Audio playing, then the log line `0 bytes of audio left this machine` and the transcript text | faster-whisper (local, open source) | If transcription is slow on stage: play the clip, then `cat hallway/fixtures/handoff_2.txt` and say "for time we use the text transcribed earlier on this laptop." |
| 2 | 0:35 | "Text only goes to Desk. In Band I ask Desk to open a case." In the lobby: mention Desk, `/ingest fixture:handoff_2`. | Room `Safe Scribe case <id>` appears with Desk, Scribe, Critic and Erik. TRANSCRIPT posted. | Band | The inbox watcher is merged (PR #33, 13:03 PDT): drop the file instead and let Desk open the case from the inbox. |
| 3 | 0:50 | "Scribe, on GLM-5.3 served by Crusoe, extracts the brief. Every item carries a verbatim quote from the transcript." | BRIEF rev 1 in the room: meds (warfarin, ciprofloxacin), allergies, pending results, follow-ups. Desk log shows provider and model id. | Crusoe, Band | None needed; observed live in cases `4be3e276` and `a9806e53`. |
| 4 | 1:05 | "Now the Critic, a different model family, also on Crusoe. The veto: a follow-up nobody owns, 'someone should call the daughter'. It does not guess an owner. It asks the room." Erik types `@Scribe @Critic I'll own it`. | VETO rev 1 (unowned follow-up `fu-daughter-call`), OWNER_REQUEST, Erik's reply, BRIEF rev 2 with owner `Erik Jones` and his message id as provenance | Crusoe (2nd family), Band human-in-room | None needed; observed live in `a9806e53`. |
| 5 | 1:25 | "The Critic also scans the outbound brief for any patient identifier: name, date of birth, record number, phone, address. Scribe worked from a pseudonymous id, so the gate passes and the brief is approved. When a name does slip into a brief, this is what happens." Runs `.venv/bin/python -m unittest hallway.tests.test_spine -k identifier -v` from the repo root (the repo `.venv` has the Band SDK; bare `python` on this laptop does not; 5 tests, 1.3 s at 14:28). | BRIEF rev 2 (owner recorded), VERDICT rev 2 APPROVE, APPROVAL rev 2 in the room; terminal shows the identifier-gate tests vetoing briefs that carry a name, a spoken DOB, an MRN. | Band gate, Crusoe | None needed. Live in case `a9806e53` at 13:0x: VETO 1 → owner reply → BRIEF 2 → APPROVE 2. The identifier veto never fires on `handoff_2` because Scribe never leaks; do not stage a leak to make it fire. |
| 6 | 1:40 | "Only now does anything leave the room, and only into a separate approved room that has never held the transcript. Grapher writes memory and lineage to Neo4j." Switches to dashboard: `who_saw_identifiers`. | Room `Safe Scribe approved <id>` with Critic, Grapher, Erik. Dashboard answers **Desk, Scribe, Critic**. | Band boundary, Neo4j Aura | If phase 2 was not observed live: before recording, the contributor session re-runs its verified `Neo4jStore` probe so Aura holds one encounter with lineage, then show the dashboard answer and say "the Grapher's delivery from the approved room is gated and not in this recording; the writer it calls and this query were verified against Aura separately today." |
| 7 | 1:52 | "The same lineage question is exposed as an MCP tool and registered in the DuploCloud studio, so a compliance agent can ask it." (Live, or cut to the 20-second clip recorded at 14:0x if the devkit is stopped.) | DuploCloud studio: MCP server "Safe Scribe", scope `safe-scribe-lineage`; a `tools/call` answer | DuploCloud | If the studio tab misbehaves: `curl` the `/mcp` endpoint on 8090 and show the same answer. |
| 8 | 2:00 | "Audio never left the laptop. Text touched only Crusoe. Nothing identifiable crossed the boundary. Band enforced it, Neo4j proves it." | README tool table | All | |

## Three-minute technical dive

Speak to the architecture diagram in `docs/hackday/submission-readme.md`, then hop to code.

1. **Two rooms, one boundary (0:40).** Case room: Desk, Scribe, Critic, the charge nurse.
   Approved room: Critic, Grapher, the nurse. Roster is checked on every write; an unexpected
   participant raises. Show `publish_approved_boundary` in `hallway/common/room.py`: created only
   on a digest-matched APPROVE, must differ from the case room, `identifier_violations` on the
   outbound envelope blocks delivery.
2. **Provenance is message ids, not model memory (0:30).** Every room message is a readable
   summary plus a `SAFESCRIBE/1` JSON envelope with revision and digest. Decoders accept exactly one
   envelope per message and only from the authenticated sender for that kind. The owner of a
   follow-up is the human's Band message id. Show `decode_messages`.
3. **Two model families on Crusoe, pinned from live evidence (0:30).** Thirteen models probed for
   tool calling (`scripts/check_crusoe_tools.py`). The offline probe picked Deepseek-V4-Flash for
   Scribe; live it emitted 2,077 tokens and no brief. GLM-5.3 at low reasoning produced the brief in
   about four seconds. Critic is Qwen3.8-27B with thinking off, a different family by rule. If
   Crusoe is unavailable the case pauses; it never routes to another provider.
4. **Lineage in Neo4j (0:30).** Pseudonymous patient (`pseudo_id` from a local salt), encounter,
   clinical nodes, and `(Agent)-[:ACCESSED]->(Field)` edges from the access manifest. The canned
   question "which agents saw identifiers" is a five-line Cypher match. Merge across encounters is
   by pseudo id only, never by similarity.
5. **Research, gated (0:20).** Researcher is recruited into a separate drug-only room; the request
   carries drug names from a bounded vocabulary and an opaque routing id. Brave returns one sourced
   fact per drug (live: ciprofloxacin → drugs.com in 1.7 s); Similarweb gives an organization
   legitimacy fact for a spoken referral domain (live: sunrisehomehealth.com, unranked). Say
   plainly whether the room recruitment ran live today or is shown from tests.
6. **How it was built (0:30).** Two humans, three agent sessions. Every task a Linear issue, every
   change a PR with an independent local AI review (Astra via Codex CLI) before merge, a third
   Claude session as overseer holding the clock and challenging claims not backed by a live run.
   Doppler as the single secrets store. Forty-nine PRs merged in the day. The integration ledger
   (`docs/hackday/integration-ledger.md`) says verified, mocked, attempted or deferred per tool,
   and the README table is generated from it.

## If a judge asks

**"Why is this needed? A doctor recorded a conversation."** Nurses and doctors hand patients off
by talking, all day. Follow-ups without an owner don't happen, details get misremembered, and
writing it down takes time nobody has. Every hospital wants an AI scribe. Compliance blocks it for
two reasons: the audio and the patient's identity would be shipped to a big cloud AI company, and
afterwards nobody can prove which systems saw the name, the birthdate, the record number. "Trust
us" is not an answer an auditor accepts. Safe Scribe is the scribe a compliance officer can say yes
to: the audio stays on the laptop, a small team of agents works in a private room with a human
nurse in it, a second agent on a different model can block the first, a human owns every
follow-up, only a pseudonymous summary leaves the room, and the system writes down who saw what.

**"Band and Crusoe still see patient data. Why is that OK?"** Say it straight: today it is only
OK because every patient is synthetic. Three named agents in one room see the transcript, and they
run on Crusoe inside a Band room. What we checked on 2026-09-29: Crusoe's self-serve Managed
Inference terms say inputs and outputs are not stored to disk and are not used for training without
opt-in, and Crusoe Cloud holds ISO 27001 and ISO 42001; the same terms also **prohibit** processing
"health information subject to United States HIPAA regulations" and offer no business associate
agreement, so real PHI would need a negotiated dedicated deployment that we have not confirmed
exists. Band's public terms and privacy policy (July 2026) say nothing about HIPAA, a BAA,
encryption, or where data is hosted. So the architecture argument is what we can claim: *chosen*
(the hospital picks where the room and the models run; the compose file runs the agents on any host
it controls), *minimized* (audio never moves, exactly three agents see identifiers, nothing
downstream sees the transcript, room membership is the boundary Band enforces), *provable* (the
graph records which agent touched which field). The vendor-contract part is procurement, and we
say so.

**"Do Crusoe or Band enclave the data or sign BAAs?"** Not that we could find. No confidential
computing or enclave claim on either vendor's public pages; no BAA offered by either. Do not imply
otherwise.

**"Why Brave and Similarweb? What do they add here?"** Listen to the handoff: "he's on warfarin",
then three sentences later "the hospitalist started ciprofloxacin", then "somebody needs to be
watching that INR." A real, dangerous interaction split across sentences at shift change. Scribe
hands the Researcher only the drug names, never the patient or the transcript; the Researcher
fetches one sourced fact per drug from Brave and the Critic accepts enrichment only with a
verifiable URL. It ran live on this scenario today: case `19ecdb31`, research room `6ebcdfae`,
three live facts (ciprofloxacin, enoxaparin, warfarin). The point is an agent that helps without
ever entering the room that holds identity. Similarweb answers a different question: the handoff
ends with a home-health referral, and referrals name outside organizations. When a transcript names
one with a website (the doctor-patient fixture: "Sunrise Home Health, sunrise home health dot
com"), the Researcher asks whether it is a real, established site; today's live answer was
"unranked, about 890 visits a month", which flags it for a human before the referral goes into the
plan. The query carries a domain, not a patient. Scenario 2 names no domain, so Similarweb is a
technical-dive line pointing at the doctor-patient scenario.

**"What about Vultr and Nebius?"** Attempted, not integrated, and not counted. Nebius issued
object-storage keys rather than an inference key, so the embeddings idea was never built. Vultr has
a deploy-ready compose file and no host: a last-hour cloud deploy was riskier than the laptop.

**"Is this HIPAA compliant / de-identified?"** No claim. It is a boundary control with an
identifier gate and an access ledger. Certification is a program, not a hackday.

**"Where is the research agent?"** Built and tested (drug-name-only room, Brave fact with URL,
Similarweb legitimacy fact for a spoken referral organization), gated off for this recording
because a failed recruitment had no retry path until the last hour. Live Brave and Similarweb
facts are in the ledger; the doctor-patient fixture `visit_1.wav` is the scenario it serves.

## Tool-by-tool proof (technical dive, 2 minutes)

Walk this table top to bottom. For each tool: what it does here, where it is on the tape, and the
proof that it is real work and not a logo.

| Tool | Job in Safe Scribe | Where you see it | Proof it is real |
| --- | --- | --- | --- |
| **Crusoe** | Every agent's thinking. Scribe on GLM-5.3, Desk and Critic on Qwen3.8-27B, two model families by rule. | Desk log line with provider and model id on every call; the brief and the veto appearing in the room. | `doppler run -- bash scripts/check-crusoe.sh` lists the live catalog from `api.inference.crusoecloud.com` and completes a chat; pins came from a 13-model tool-calling probe plus two live runs (Flash produced no brief, GLM-5.3 did). If Crusoe is down the case pauses; there is no other provider in the code. |
| **Band** | The rooms and the door policy. Case room holds Desk, Scribe, Critic and the nurse; the approved room holds Critic, Grapher and the nurse and never the transcript. Vetoes, the owner request and the human reply are Band messages. | Room list: `Safe Scribe case <id>`, `Safe Scribe approved <id>`. The veto, your `I'll own it`, the approve, all in the room. | Roster is checked on every write; an unexpected participant raises. Case `a9806e53` shows the full loop; case `84cfeb33` shows the approved room being created only after a digest-matched approve. Open the approved room's history on tape: no transcript, no name. |
| **Neo4j** | Memory and the audit trail. Pseudonymous patient, encounter, clinical nodes, and `(Agent)-[:ACCESSED]->(Field)` edges from the access manifest. | Dashboard `/lineage/who-saw-identifiers` answering **Critic, Desk, Scribe**; Aura browser showing `p_83cd10…`, the `handoff_2` patient. | The nodes on Aura were written by the Grapher from the approved room, not seeded. Second encounter for the same pseudo id MERGEs (`merged: True`); merge is by pseudo id only, never similarity. |
| **DuploCloud** | The audit question exposed as an MCP tool so a compliance agent can ask it. | Studio ticket `extensiondev-1`: the agent selects `mcp__Safe_Scribe__who_saw_identifiers`, you approve, it answers Critic, Desk, Scribe. | Server, provider, scope and ticket registered through the studio admin API; the devkit agent completed the MCP handshake against the live dashboard. The tool result is the same query as the dashboard, from Aura. |
| **Brave** | One sourced fact per drug named in the handoff, for the Critic to verify by URL. | Technical dive only: `doppler run -- python -m hallway.research.brave ciprofloxacin`. | Live result today: drugs.com interaction page in 1.7 s. The research room that recruits the Researcher is built and tested, gated off for this recording (say so). |
| **Similarweb** | Legitimacy fact for a referral organization spoken in a visit. | Technical dive only, on the doctor-patient fixture `visit_1`: "Sunrise Home Health" → unranked, ~890 visits/month. | Live result today under `doppler run`; spoken-domain extraction is name-anchored and fails closed. |
| faster-whisper | Transcription on the laptop. Not a sponsor. | Beat 1: the audio clip, then the log line `0 bytes of audio left this machine`. | Verified on `handoff_2.wav`: the planted name, DOB and unowned line survive. |
| Nebius, Vultr | Attempted, not integrated. | Not on tape. | Say it if asked; do not list them as integrations. |

## Sponsor status to state on tape (as of the 14:40 PDT code freeze)

| Tool | Say | Do not say |
| --- | --- | --- |
| Crusoe | Every agent's inference; two model families; pins from a live probe | anything about fine-tuning or hosting |
| Band | Live case room, veto, human owner in the room, APPROVE, and the approved room with Grapher only (cases a9806e53 and 84cfeb33) | that the identifier veto fired live (it did not need to) |
| Neo4j | Aura instance, real writes and the lineage query verified from the store; Grapher wrote its receipt from a live approved room | that the Aura write came from a live room unless the code-freeze run's receipt says GRAPH_WRITTEN (not MOCK) |
| DuploCloud | MCP server, provider, scope and ticket registered in the studio; the devkit agent completed the handshake and picked the lineage tool; the call runs after Erik approves it in the studio | that DuploCloud runs the agents |
| Brave | Live sourced fact per drug | that the Researcher joined a live case unless it did |
| Similarweb | Live organization fact for a spoken referral domain | that it verifies a provider's credentials |
| faster-whisper | Local transcription on the laptop | that it is a sponsor |
| Nebius, Vultr | Attempted, not integrated (key type mismatch; no time for a safe deploy) | anything else |
| OpenRouter, Merge.dev | Not used | anything |
| xAI | Text-to-speech used to build the synthetic fixtures; development tooling only | that it is part of the product |

Words never to use: HANDOFF or HALLWAY as the product name; "de-identified" or "HIPAA
compliant" (say "identifier gate", "boundary control"); "real patient".

## Rehearsal log

| # | Time | Fixture | Upload → APPROVE | What broke | Fix |
| --- | --- | --- | --- | --- | --- |
| 1 | 14:42 | handoff_2 | 51 s (case `d92244bd`, approved room `fe086da2`, Aura write) | No human beat: Scribe requested an owner for one follow-up, then 10 s later published rev 3 with two follow-ups marked unresolved and the Critic approved (its prompt allows that when the request is on record). Veto count 2. | None; this is the approved-with-unresolved shape. |
| 2 | 14:44 | handoff_2 | timed out at 90 s (case `6a2556ea`) | Two unowned follow-ups, four OWNER_REQUEST posts. Erik's "I'll own it" (both mentions) bound to the latest request only; the other stayed unowned and the Scribe read the case, called no tool and waited. | Runbook: answer each "Who owns this?" with `/own <id> Erik Jones` mentioning both agents; no code change. |
| 3 | 14:53 | handoff_2 | not approved (case `2a6bee3a`) | Owner reply landed within seconds; the Scribe's rev 2 was rejected twice by the deterministic guard "Repair must preserve the original source-backed follow-up quote" because the model rewrote a follow-up quote while adding the owner. Band shows "Internal error while processing message" from Scribe. | Post-mortem on JV-116; take used the fallback (run 1 shape plus the morning rooms `a9806e53` / `19ecdb31`). |
| 4 (take) | 15:06 | handoff_2 | ~71 s (case `c4584729`, approved room `c99b8972`, Aura write; dashboard 3 histories, 35 lineage edges, who-saw Critic/Desk/Scribe) | Nothing on the path: VETO, one OWNER_REQUEST, Erik's `I'll own it` bound, Scribe rev 3 accepted by the guard, APPROVE rev 3 with 0 unresolved, Grapher write completed after one transient Aura connection retry. `make demo` printed DEMO NOT GREEN because its single 90 s deadline spans case creation and approval. | Backlog: split the demo watcher deadline; the receipts in Band and Aura stand. |

## Delete tests to say out loud if asked

| Tool | Remove it and... |
| --- | --- |
| Crusoe | No agent has a brain, and the text would have to go to a hyperscaler API. |
| Band | No room, no roster, no gate, no veto, no boundary. There is no fallback orchestrator. |
| Neo4j | No memory across encounters and no proof of who saw what. |
| DuploCloud | The lineage answer is not reachable by other agents as a tool. |
| Brave | Researcher has nothing to post; Critic cannot verify enrichment. |
| Similarweb | A spoken referral organization cannot be checked for legitimacy. |
