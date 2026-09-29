# Demo script: HANDOFF

Linear JV-102. Judging is live. Two minutes on screen, then questions. Source: the HANDOFF
brief (`docs/hackday/handoff-build-brief.md`, sections 2 and 8) and the pivot decision in the
Linear project update of 11:10 PDT.

## One-sentence claim

A nurse-to-nurse shift handoff recording becomes a Band case room where agents on Crusoe extract
a quoted clinical brief, a Critic blocks unsupported claims, unowned follow-ups, and any
identifier trying to leave the room, and Neo4j records exactly which agent saw which field.

Say once, early: the patient is synthetic.

## Two-minute flow

| # | Erik says / does | Judges see | Sponsor tool visible | Proof it is real |
| --- | --- | --- | --- | --- |
| 1 | Drops the `.wav` on the upload page, which runs on this laptop. "Zero bytes of audio left this laptop." | Desk transcribes on-device and posts only text into the Band room; log line with the Crusoe model id. | Crusoe, faster-whisper (local) | Log shows local transcription; the Vultr compose file has no Desk |
| 2 | "Scribe extracts the handoff brief. Every item carries a verbatim quote." | `case-<slug>` room opens. Scribe posts the HANDOFF brief. Execution events stream. | Band, Crusoe | Quotes are substrings of the transcript on screen |
| 3 | "A drug was named, so Scribe opens a research room and recruits a researcher. It sees only the drug names." | Room list grows: `case-…-research` appears with Researcher. It posts one interaction or guideline fact with a URL; Scribe relays it. | Band runtime recruitment, Brave | URL opens; research room history shows drug names only |
| 4 | "Now the Critic, on a different model family. Two vetoes." Erik, as charge nurse, types "I'll own it" in the room when asked. | VETO 1: follow-up #2 has no owner. Scribe asks the room; Erik answers; Scribe records the owner with that message as provenance. VETO 2, the hero: patient name and DOB in the outbound brief. Scribe redacts. APPROVE revision 3. Grapher joins; the redacted brief crosses to the boundary room. | Band veto and gate, human in the room, Crusoe (two model ids) | The identifiers and the unowned follow-up are deliberate lines in the recording; the owner comes from a human, never invented |
| 5 | "Grapher writes memory and lineage." | Neo4j nodes plus ACCESSED edges. Dashboard query "which agents saw identifiers?" answers Desk, Scribe, Critic. Researcher and Closer are absent. | Neo4j | Live query result on screen |
| 6 | "Closer lives in a separate room under a separate account. It only ever gets the redacted brief." | Closer drafts the discharge follow-up from the redacted brief only. Open that room's history: no transcript, no name. | Band enforced boundary | Room history on screen |
| 7 | Close: "Audio never left the laptop. Text only touched Crusoe. Nothing identifiable crossed the boundary. Band enforced it, Neo4j proves it. Seven sponsor tools, each with a delete test in the README, all self-serve, built by two people and two agents in four hours." | README tool table with delete tests. | All | `make demo` output |

Timing target from upload to APPROVE: under 90 seconds. Report transcription time separately if
asked.

## Delete tests to say out loud if asked

| Tool | Remove it and... |
| --- | --- |
| Crusoe | No agent has a brain, and the text would have to go to a hyperscaler API. |
| Band | No room, no roster, no gate, no veto, no boundary. There is no fallback orchestrator. |
| Neo4j | No memory across encounters and no proof of who saw what. |
| Brave | Researcher has nothing to post; Critic cannot verify enrichment. |
| Nebius | Same patient across encounters is not recognised (tier 2). |
| OpenRouter | No ask-the-graph on the dashboard, no last-resort fallback (tier 2). |
| Vultr | Demo rides on venue wifi and a laptop (tier 2). |

Merge.dev was cut at the pivot (no healthcare fit). Plaud: no device.

## Cold-start checklist (run twice before judging)

- [ ] `.env` filled; `./scripts/check-crusoe.sh` and `python3 scripts/check_crusoe_tools.py --max 20` pass; the three model ids match `common/llm.py`
- [ ] Six Band agents connected on the case-room account; Closer connected on Erik's second account; stale case rooms archived
- [ ] Neo4j Aura instance awake (free tier pauses); a prior encounter for the synthetic patient loaded so the lineage and history queries return rows
- [ ] Brave key live; `MOCK_*` all 0 for tier 1
- [ ] Vultr VM up, `docker compose ps` all Up; dashboard URL bookmarked (laptop fallback ready)
- [ ] Phone recording ready with the deliberate full name + DOB early and the unowned "someone should call the daughter about discharge"; `fixtures/handoff_2.txt` is the same content
- [ ] `make demo` green in the last 15 minutes
- [ ] Recorded run (screen capture) saved locally in case wifi or a sponsor API fails

## Fallbacks

| Failure | Do |
| --- | --- |
| Wifi drops | Play the recorded run; narrate the same beats. |
| Crusoe rate limit | Retry once (model B). Transcript-bearing agents then fail closed and the room says "case paused"; say so honestly and show the earlier Crusoe run. Never route the transcript to another provider. |
| Band web app slow | Keep the terminal event stream visible; it shows the same events. |
| Transcription slow | Drop `fixtures/handoff_2.txt` instead of the `.wav`. |
| Neo4j asleep | Wake it in the console before the demo; if it fails, show the lineage screenshot from the rehearsal. |
| Boundary room fails to receive | Show the Critic's APPROVE and the redacted brief in the case room; state the boundary as designed, not as shown. |

## Rehearsal log

| Time | Upload to APPROVE | Result | Fix |
| --- | --- | --- | --- |
