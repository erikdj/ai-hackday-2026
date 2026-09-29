# Safe Scribe by TrustEdge AI — live rehearsal runbook

Use synthetic patients only and say so on screen. The verified historical case is
`19ecdb31-2006-4284-acd3-0a6c22d1a6e0`: VETO `18c8fe26-664a-4ab2-bc44-520aca503b1d`, Erik's original ownership reply
`92ce7975-3ad3-41c1-af0a-0e8e7c31116d` at 13:21 PDT (recovered at 13:39), BRIEF revision 2,
APPROVE verdict `82c1f9ca-6000-411d-9445-b6141b4496bb`, approved room `4704ff81-f261-4cba-84ba-6c79e75aa06f`, and real graph receipt `e02d4a4b-e543-43b1-866e-70358731a12e`.
The source was an atomic local text upload of `handoff_2`, not audio or Plaud. The graph reported `merged: false`; do not narrate a dedupe.
Historical network/delivery delays meant this run **exceeded 90 seconds**.

Research room `6ebcdfae-eb57-4365-b030-10fe3ccaa9f3` produced three real Brave facts with URLs through runtime recruitment.
The current recording preset sets `ENABLE_DRUG_RESEARCH=0` and
`ENABLE_APPROVED_ROOM=1`. Show the earlier live research evidence separately; do not
suggest the recording run recruited Researcher when the flag is off. PRs #42 and #43
are merged. Coordinate any process handover between cases, never mid-case.

1. Configure real Crusoe/Band credentials and real Neo4j mode (`MOCK_NEO4J=0`). Keep Desk
   on the laptop; start the required role processes once per agent ID. Check the preset flags.
2. Submit synthetic text through the verified local upload path. Start a timer at intake.
   Audio/Whisper is separate Claude-owned verification; use it only with its own evidence.
3. Open the live case in Band. Show Desk, Scribe, Critic and the human roster, the extracted
   brief and the actual veto. Do not fabricate an unsupported quote to stage an extra veto.
4. For the owner request, the human mentions both Scribe and Critic and replies
   `I'll own that`, `I'll own it`, or `/own <id> <name>`. The actual message is ownership
   provenance. If processing stalls, inspect that existing message and delivery state;
   do not claim the human has not answered merely because an agent is delayed.
5. Show revision-bound approval, then the separate approved room and Grapher receipt.
   Verify a real write, not a mock receipt. The lineage roles `critic`, `desk`, `scribe`
   describe runtime field processing, **not human reading or Band delivery proof**.
6. Stop the timer at the matching real graph receipt. Record the result below, including
   failures. Show a shared encounter/deduplication only if the actual new result proves it.

| Rehearsal | Intake time | Graph receipt time | Elapsed | Case / receipt | Outcome |
| --- | --- | --- | --- | --- | --- |
| 1 | Not recorded | Not recorded | Not recorded | Not recorded | Pending |
| 2 | Not recorded | Not recorded | Not recorded | Not recorded | Pending |
| 3 | Not recorded | Not recorded | Not recorded | Not recorded | Pending |

These are empty result slots, not three successful rehearsals. The historical completed
case is evidence of the functional path, not a passing timed rehearsal or deployment proof.

Run `make check` for current offline validation. `MOCK_BAND=1 MOCK_CRUSOE=1 make demo`
is explicitly an offline unit-test harness, never live sponsor evidence. Live failure
must not switch to it. Crusoe inference uses 30 seconds with one retry; Band REST/search
retain 10 seconds with two retries, and the live observer deadline remains 90 seconds.

Text is sent to Band and Crusoe; Desk and raw audio remain local. The identifier guard
is a regex/list demonstration, not certified de-identification. Event submission,
video upload and sponsor feedback still require their own completion evidence.
