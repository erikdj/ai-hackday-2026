# Safe Scribe by TrustEdge AI

**A clinical handoff scribe where the agents argue before they commit, and nothing identifiable
leaves the room.**

Built in one day at The AI Conference Hack Day 2026 by Erik Jones and Jaiven Spence
(TrustEdge AI / Jacobian Engineering) with their agent teams. Repo:
https://github.com/erikdj/ai-hackday-2026

## The problem

Clinics want AI scribes. Compliance officers say no, twice: patient data would leave for a
hyperscaler LLM API, and afterwards nobody can prove which system saw which field. Safe Scribe
is the version of an AI scribe that a compliance officer can say yes to.

## What it does, in two minutes

1. A nurse-to-nurse shift handoff recording is dropped on a local upload page. It is transcribed
   **on the laptop** with faster-whisper. Zero bytes of audio leave the machine.
2. A **Band** case room opens. **Scribe**, thinking on **Crusoe** Managed Inference, extracts a
   structured brief: patient, meds, allergies, pending results, findings, follow-ups. Every item
   carries a verbatim quote from the transcript.
3. A **Critic** on a different model family (also on Crusoe) reviews. It vetoes anything
   unsupported: a quote that is not in the transcript, a follow-up with no owner, and, the beat
   that matters, **any patient identifier in the outbound brief** (name, date of birth, record
   number, phone, address).
4. The unowned follow-up is not guessed. The charge nurse in the room types `I'll own it`, and
   that human message becomes the provenance for the owner. The identifier leak is redacted.
   The Critic approves an exact brief revision.
5. Only then are the downstream agents let in, and only into a separate **approved room** that has
   never contained the transcript. **Grapher** writes the brief to **Neo4j** as a pseudonymous
   patient record plus an access-lineage graph. **Closer** drafts the discharge follow-up from the
   redacted brief alone.
6. The dashboard answers the compliance question live: *which agents saw identifiers?* The
   answer is Desk, Scribe, Critic. Nothing downstream.

Delete Band and there is no room, no roster, no gate, no veto. Delete Crusoe and no agent has a
brain. Delete Neo4j and there is no memory across encounters and no proof of who saw what.

## Architecture

```
laptop                              Band (coordination)                 Crusoe (inference)
┌──────────────────────┐   text    ┌──────────────────────────┐        ┌──────────────────┐
│ upload page          │ ────────► │ case room                │ ◄────► │ GLM-5.3  (Scribe)│
│ faster-whisper (local)│          │   Desk → Scribe → Critic │        │ Qwen3.8  (Desk)  │
│ pseudo_id salt (local)│          │   human: "I'll own it"   │        │ DeepSeek (Critic)│
└──────────────────────┘           │   VETO / APPROVE rev N   │        └──────────────────┘
                                   └────────────┬─────────────┘
                                   redacted brief + access manifest only
                                   ┌────────────▼─────────────┐        ┌──────────────────┐
                                   │ approved room            │ ─────► │ Neo4j Aura       │
                                   │   Grapher → Closer       │        │ patient (pseudo) │
                                   └──────────────────────────┘        │ ACCESSED lineage │
                                                                       └──────────────────┘
```

## Sponsor tools and what breaks without them

| Tool | Job in Safe Scribe | Delete test | Status |
| --- | --- | --- | --- |
| **Crusoe** | Every agent's inference. Three models pinned from a live tool-calling probe of the whole catalog. | No agent has a brain | verified live |
| **Band** | Case room, runtime roster, veto gate, approved-room boundary, live execution events | No room, no gate, no veto | [ ] live room verified |
| **Neo4j** | Pseudonymous patient memory across encounters; `(Agent)-[:ACCESSED]->(Field)` lineage | No memory, no proof of who saw what | [ ] Aura writes verified |
| Brave Search | Researcher, recruited only when a drug is named, one sourced fact with URL | Critic cannot verify enrichment | [ ] optional |
| Nebius | Embeddings that *suggest* a prior encounter for a human to confirm | Duplicate patients | [ ] optional |
| OpenRouter | Dashboard "ask the graph" over the pseudonymous graph only | No natural-language graph Q&A | [ ] optional |
| Vultr | Hosts Scribe, Critic, Grapher, Closer, dashboard. Desk and audio stay on the laptop. | Demo rides on venue wifi | [ ] optional |

xAI text-to-speech was used to synthesize the demo recordings from written scripts (synthetic
patients). It is development tooling, not part of the product, and is not claimed as an
integration.

## What we are careful to say

- Every patient in the demo is synthetic. Names, dates of birth, record numbers, and phone
  numbers are invented.
- The identifier gate is a programmatic check plus model judgment on the outbound brief. It is
  a boundary control, not a de-identification certification.
- Inference for anything that holds the transcript fails closed. If Crusoe is unavailable the
  case pauses; it never silently routes to another provider.

## Run it

```bash
doppler setup                                  # project ai-hackday-2026, config dev
doppler run -- python3 scripts/check_crusoe_tools.py --max 20
doppler run -- make demo                       # handoff_2: both vetoes, then approve (Makefile lands with PR #8)
```

Fixtures: `hallway/fixtures/handoff_{1,2,3}.{txt,wav}`. `handoff_2` is the demo, with a
planted name and date of birth, a warfarin plus ciprofloxacin interaction, and one follow-up
nobody owns.

## How it was built

Two humans, several agents, one rule set (`CLAUDE.md`). Every task is a Linear issue, every
change is a pull request, every PR gets an independent local AI review before it opens, humans
merge. Erik's side: Claude Code orchestrating, Grok writing code, Astra (Codex) reviewing.
Jaiven's side: Astra building, Claude Code reviewing, Grok second-reading. A third Claude
session acted as overseer: merged reviewed PRs, held the clock, and challenged claims that were
not yet backed by a live run.
