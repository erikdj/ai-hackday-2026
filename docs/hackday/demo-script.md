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
- [ ] Terminal with `doppler run -- make demo FIXTURE=handoff_2` ready but not started.
- [ ] Windows: Band (room list visible), terminal, dashboard tab, DuploCloud studio tab.
- [ ] `hallway/fixtures/handoff_2.wav` and `.txt` at hand; the planted lines are in
      `hallway/fixtures/README.md`.
- [ ] Time a full dry run. Target: upload to APPROVE under 90 seconds. Record the number.

## Two-minute demo

| # | Time | Erik says / does | On screen | Sponsor | Fallback if not live |
| --- | --- | --- | --- | --- | --- |
| 0 | 0:00 | "Clinics want AI scribes. Compliance says no twice: data leaves for a hyperscaler, and nobody can prove who saw what. Safe Scribe is the scribe a compliance officer can say yes to. The patient you'll hear is synthetic." | Title slide or README top | | |
| 1 | 0:15 | "The handoff was recorded on this laptop. It is transcribed here, by faster-whisper. Zero bytes of audio leave the machine." Runs `python -m hallway.ingest.transcribe hallway/fixtures/handoff_2.wav --inbox inbox --print`. | Log line `0 bytes of audio left this machine`, transcript text | faster-whisper (local, open source) | Play 10 s of the `.wav`, then `cat hallway/fixtures/handoff_2.txt`. Say "transcription runs locally; for time we use the pre-transcribed text." |
| 2 | 0:35 | "Text only goes to Desk. In Band I ask Desk to open a case." In the lobby: mention Desk, `/ingest fixture:handoff_2`. | Room `Safe Scribe case <id>` appears with Desk, Scribe, Critic and Erik. TRANSCRIPT posted. | Band | If the inbox watcher (PR #33) is wired by freeze, drop the file instead and let Desk open the case from the inbox. |
| 3 | 0:50 | "Scribe, on GLM-5.3 served by Crusoe, extracts the brief. Every item carries a verbatim quote from the transcript." | BRIEF rev 1 in the room: meds (warfarin, ciprofloxacin), allergies, pending results, follow-ups. Desk log shows provider and model id. | Crusoe, Band | None needed; observed live in cases `4be3e276` and `a9806e53`. |
| 4 | 1:05 | "Now the Critic, a different model family, also on Crusoe. The veto: a follow-up nobody owns, 'someone should call the daughter'. It does not guess an owner. It asks the room." Erik types `@Scribe @Critic I'll own it`. | VETO rev 1 (unowned follow-up `fu-daughter-call`), OWNER_REQUEST, Erik's reply, BRIEF rev 2 with owner `Erik Jones` and his message id as provenance | Crusoe (2nd family), Band human-in-room | None needed; observed live in `a9806e53`. |
| 5 | 1:25 | "The Critic also scans the outbound brief for any patient identifier: name, date of birth, record number, phone, address. Scribe worked from a pseudonymous id, so the gate passes and the brief is approved. When a name does slip into a brief, this is what happens." Runs `python -m unittest hallway.tests.test_spine -k identifier -v` in the terminal. | BRIEF rev 2 (owner recorded), VERDICT rev 2 APPROVE, APPROVAL rev 2 in the room; terminal shows the identifier-gate tests vetoing briefs that carry a name, a spoken DOB, an MRN. | Band gate, Crusoe | None needed. Live in case `a9806e53` at 13:0x: VETO 1 → owner reply → BRIEF 2 → APPROVE 2. The identifier veto never fires on `handoff_2` because Scribe never leaks; do not stage a leak to make it fire. |
| 6 | 1:40 | "Only now does anything leave the room, and only into a separate approved room that has never held the transcript. Grapher writes memory and lineage to Neo4j." Switches to dashboard: `who_saw_identifiers`. | Room `Safe Scribe approved <id>` with Critic, Grapher, Erik. Dashboard answers **Desk, Scribe, Critic**. | Band boundary, Neo4j Aura | If phase 2 was not observed live: before recording, the contributor session re-runs its verified `Neo4jStore` probe so Aura holds one encounter with lineage, then show the dashboard answer and say "the Grapher's delivery from the approved room is gated and not in this recording; the writer it calls and this query were verified against Aura separately today." |
| 7 | 1:52 | "The same lineage question is exposed as an MCP tool and registered in the DuploCloud studio, so a compliance agent can ask it." | DuploCloud studio: MCP server "Safe Scribe", scope `safe-scribe-lineage`; a `tools/call` answer | DuploCloud | If the studio tab misbehaves: `curl` the `/mcp` endpoint on 8090 and show the same answer. |
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
   Doppler as the single secrets store. Thirty PRs merged in the day. The integration ledger
   (`docs/hackday/integration-ledger.md`) says verified, mocked, attempted or deferred per tool,
   and the README table is generated from it.

## Sponsor status to state on tape (as of 13:05 PDT, update at freeze)

| Tool | Say | Do not say |
| --- | --- | --- |
| Crusoe | Every agent's inference; two model families; pins from a live probe | anything about fine-tuning or hosting |
| Band | Live case room, roster gate, vetoes, human owner in the room, approved room built and gated | that the approved room ran live unless the 13:30 receipt exists |
| Neo4j | Aura instance, real writes and the lineage query verified | that lineage came from a live room unless phase 2 ran |
| DuploCloud | MCP server, provider and scope registered in the studio; tool call answers | that DuploCloud runs the agents |
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
| 1 | | handoff_2 | | | |
| 2 | | handoff_2 | | | |
| 3 | | handoff_2 | | | |

## Delete tests to say out loud if asked

| Tool | Remove it and... |
| --- | --- |
| Crusoe | No agent has a brain, and the text would have to go to a hyperscaler API. |
| Band | No room, no roster, no gate, no veto, no boundary. There is no fallback orchestrator. |
| Neo4j | No memory across encounters and no proof of who saw what. |
| DuploCloud | The lineage answer is not reachable by other agents as a tool. |
| Brave | Researcher has nothing to post; Critic cannot verify enrichment. |
| Similarweb | A spoken referral organization cannot be checked for legitimacy. |
