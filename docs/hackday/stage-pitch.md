# Stage pitch: Safe Scribe by TrustEdge AI (top-10 round)

Shark-tank format. Two minutes of pitch, sixty seconds of proof, then questions. Written 17:05 PDT
on 2026-09-29 for Erik Jones. Say "synthetic patient" once, early. Never say HIPAA compliant,
de-identified, enclave or BAA. The recorded take is case `c4584729` (15:06 PDT, approved room
`c99b8972`, Neo4j Aura write, about 71 seconds from ingest to approval).

## The pitch (2:00)

**Hook (0:00).** "Every hospital wants an AI scribe. Every compliance officer says no. Twice.
We built the scribe a compliance officer can say yes to."

**Problem (0:15).** "Nurses hand patients off by talking. 'Mr. Callahan, born in fifty-two, on a
blood thinner, just started an antibiotic that interacts with it, someone should call his daughter
about discharge.' That sentence is where hospitals lose patients: follow-ups with no owner don't
happen. An AI scribe would fix it. Compliance says no because the audio and the patient's identity
go to a big cloud AI company, and afterwards nobody can prove which system saw the name, the
birthdate, the record number. 'Trust us' is not an answer an auditor accepts."

**Product (0:40).** "Safe Scribe changes three things.
One: the audio never leaves the laptop. Transcription is local.
Two: the agents argue before they commit. A Scribe on Crusoe writes the summary and quotes the
transcript for every line. A Critic on a different model family, so it doesn't share the Scribe's
blind spots, can veto: an unsupported quote, a follow-up nobody owns, and any patient identifier
trying to leave the room. The unowned follow-up is not guessed. The nurse in the room types 'I'll
own it', and that human message becomes the record.
Three: it proves who saw what. Only the approved, pseudonymous summary crosses into a second room
that never held the transcript, and Neo4j records which agent touched which identifier field. Ask
'which systems saw patient identifiers?' and the answer comes back from the graph: Desk, Scribe,
Critic. Nothing downstream. A Crusoe model turns that into the three sentences a privacy officer
reads."

**Proof (1:20).** "This ran live today. Seventy-one seconds from handoff recording to approved
brief, with the veto, the human owner and the graph write in the recording. Six sponsor tools do
real work: Crusoe for every model call, Band for the rooms and the human gate, Neo4j for memory and
lineage, DuploCloud exposing the compliance answer as a tool other agents can call under human
approval, Brave for sourced drug facts, Similarweb for checking a spoken referral organization."

**Business (1:40).** "Ambient clinical documentation is one of the fastest-growing categories in
health AI, and the buyer's blocker is compliance, not accuracy. We sell to the CMIO and the
compliance officer together: a scribe deployed in the hospital's own cloud or on a dedicated Crusoe
endpoint under contract, priced per clinician seat, with the access graph as the audit artifact
they hand to the auditor. The lineage graph is the moat: every competitor's answer to 'who saw the
data' is a policy document. Ours is a query."

**Ask (1:55).** "Next: the eighteen Safe Harbor identifier categories in the gate, a dedicated Crusoe
inference endpoint under a signed agreement, and a first clinic pilot on real voices. We built this
in six hours with two humans and their agent teams, fifty-two pull requests, every one reviewed."

## The proof, if they ask for a demo (0:60)

Preferred order. Stop at any step if time is called; each step stands alone.

1. **Band, room `Safe Scribe case c4584729`.** Scroll top to bottom: transcript in, Scribe brief with
   quotes, Critic VETO with the reason, OWNER_REQUEST, your "I'll own it", brief rev 3, APPROVE rev 3.
   Say: "Every message here is authenticated by Band. The human reply is the provenance."
2. **Band, room `Safe Scribe approved c99b8972`.** "Different room, different roster. Critic, Grapher
   and me. The transcript was never here." Show Grapher's graph-write receipt.
3. **Dashboard on :8090.** "Who saw identifiers: Critic, Desk, Scribe." Then the compliance
   narrative section: "Written by a Crusoe model from agent names, field names and counts. The exact
   payload it received is printed beside it, so you can check that no patient data went in."
4. **If they want it live and the contributor confirms the stack is warm:** drop `handoff_2` on the
   inbox, watch the case room open, answer the owner request. If Scribe posts two OWNER_REQUESTs,
   answer each one with `@Scribe @Critic /own <id> Erik Jones`. Budget ninety seconds; if it is not
   approved by then, cut to step 1 and say "this is the same system at 15:06 today."

## Questions they will ask

- **"Is this HIPAA compliant?"** "No claim. Every patient today is synthetic. What we claim is the
  architecture: the hospital chooses where the models and rooms run, exactly three agents see
  identifiers, and the graph proves it. For real patients, every component that touches the
  transcript needs a business associate agreement or a hospital-controlled substitute. That is a
  contract, not a redesign; the inference endpoint is one configuration value."
- **"Crusoe and Band see patient data. Why is that acceptable?"** "Today because the patients are
  synthetic. Crusoe's self-serve terms exclude regulated health data and it does not store or train on
  inputs; production means a dedicated Crusoe deployment under contract or hospital GPUs. Band would be
  under an enterprise agreement or replaced by a hospital-controlled room service with the same
  roster semantics. We wrote all of this down in the repo rather than hide it."
- **"Why multiple agents instead of one good model?"** "Because the failure mode we care about is
  a confident summary that is wrong or leaks. A second model family with veto power and
  deterministic checks catches what one model cannot see about itself. The human gate catches what
  neither can."
- **"Why not Nuance or Abridge?"** "They are hyperscaler-hosted scribes; the compliance answer is
  their policy. Ours is a provable boundary the hospital controls, and it is provider-agnostic."
- **"What breaks without each sponsor?"** "No Band: no room, no gate, no veto. No Crusoe: no agent
  has a brain, and we fail closed rather than route elsewhere. No Neo4j: no memory across encounters
  and no proof of who saw what."
- **"What did not work today?"** "Two failure modes we found in rehearsal and documented: a bare
  'I'll own it' binds only to the latest owner request, and our own guard rejected a repair where the
  model rewrote a quote. Both are in the backlog with fixes. The take itself was clean."
- **"Business model / who pays?"** "Per clinician seat, sold to the CMIO with the compliance officer
  as the champion, deployed in the customer's cloud or a dedicated Crusoe endpoint. The audit graph is
  the artifact that shortens their security review from months to a query."

## Say / do not say

Say: identifier gate, boundary control, access lineage, pseudonymous, synthetic patients, "the
audio never leaves the laptop", "three named agents see the transcript and we can prove it".
Do not say: HIPAA compliant, de-identified, enclave, BAA in place, "no one sees patient data",
market-size numbers you cannot source on stage.
