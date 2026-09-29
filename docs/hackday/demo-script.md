# Demo script: HALLWAY

Linear JV-102. Judging is live. Two minutes on screen, then questions. Source: build brief
section 8 (`docs/hackday/hallway-build-brief.md`).

## One-sentence claim

Every hallway conversation becomes a Band case room where six agents, all thinking on Crusoe,
argue before they commit: quoted facts, runtime research, a Critic that can veto, then graph and
CRM writes only after approval.

## Two-minute flow

| # | Erik says / does | Judges see | Sponsor tool visible | Proof it is real |
| --- | --- | --- | --- | --- |
| 1 | "I recorded this 60 seconds ago on my phone." Drops the file on the upload page. | Upload page, then the screen switches to the Band room. | Band, Crusoe (Desk log line shows provider + model) | File name and timestamp on screen |
| 2 | "Scribe extracts the brief. Every claim carries a verbatim quote." | `case-<slug>` room appears. Scribe posts BRIEF JSON. Execution events stream (tool calls, thoughts). | Band events, Crusoe | Quotes are substrings of the transcript on screen |
| 3 | "A company was named, so Scribe recruits a researcher. It was not in the room a second ago." | Participant list grows: Researcher joins. Posts ENRICHMENT with URLs. | Band runtime recruitment, Brave Search | URLs open |
| 4 | "Now the Critic. It runs on a different model family." | Critic: `VERDICT: VETO. 1. Commitment #2 has no owner.` Scribe fixes. Critic: `VERDICT: APPROVE`. Roster grows again: Grapher and Closer join. | Band veto and gate, Crusoe (two model ids) | The unowned commitment is Erik's deliberate line in the recording ("someone should send them the deck") |
| 5 | "Grapher writes memory. It recognised the company from a case we ran earlier." | Grapher: "merged Company X with case 2 (cosine 0.96)". Graph view links both cases. | Neo4j, Nebius embeddings | Live query in the dashboard: "who else met company X" |
| 6 | "Closer drafts the follow-up using the research, and the CRM record lands." | Draft references the news Researcher found. CRM record opens in a tab. | Merge.dev, dependent handoff | Record id printed in the room |
| 7 | Close: "Every agent thinks on Crusoe. The room is Band: delete it and there is no roster, no gate, no veto. Eight sponsor tools, each with a delete test in the README, all self-serve, built by two people and two agents in four hours." | README tool table with delete tests. | All | `make demo` output |

Timing target from upload to APPROVE: under 90 seconds. Report recording and transcription time
separately if asked.

## Delete tests to say out loud if asked

| Tool | Remove it and... |
| --- | --- |
| Crusoe | No agent has a brain. |
| Band | No room, no roster, no gate, no veto. There is no fallback orchestrator. |
| Neo4j | No memory across cases; the merge in step 5 cannot happen. |
| Brave | Researcher has nothing to post; Critic cannot verify enrichment. |
| Nebius | Duplicate people and companies; no cosine merge. |
| Merge.dev | Nothing lands in a CRM. |
| OpenRouter | No ask-the-graph on the dashboard, no last-resort fallback. |
| Vultr | Demo rides on venue wifi and a laptop. |

## Cold-start checklist (run twice before judging)

- [ ] `.env` filled; `./scripts/check-crusoe.sh` and `python scripts/check_crusoe_tools.py` pass; note the three model ids
- [ ] Six Band agents connected; room list empty of stale cases (or archive them)
- [ ] Neo4j Aura instance awake (free tier pauses); prior case 2 loaded so the merge fires
- [ ] Brave, Nebius, Merge keys live; `MOCK_*` all 0
- [ ] Vultr VM up, `docker compose ps` all Up; dashboard URL bookmarked
- [ ] Phone recording ready with the deliberate unowned commitment; a `.txt` copy of it in `fixtures/` as fallback
- [ ] `make demo` green in the last 15 minutes
- [ ] Recorded run (screen capture) saved locally in case wifi or a sponsor API fails

## Fallbacks

| Failure | Do |
| --- | --- |
| Wifi drops | Play the recorded run; narrate the same beats. |
| Crusoe rate limit | Retry once; if the log shows OpenRouter in red, say so honestly and show the earlier Crusoe run. Do not hide it. |
| Band web app slow | Keep the terminal event stream visible; it shows the same events. |
| Transcription slow | Drop the `.txt` fixture instead of the `.wav`. |
| Neo4j asleep | Wake it in the console before the demo; if it fails, show the graph screenshot from the rehearsal. |

## Rehearsal log

| Time | Upload to APPROVE | Result | Fix |
| --- | --- | --- | --- |
