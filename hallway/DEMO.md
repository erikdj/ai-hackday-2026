# Safe Scribe by TrustEdge AI — phase-1 rehearsal

Use synthetic patient fixtures only. Real Crusoe function calling and Band case creation/read have
passed. With `cfb1268`, case `4be3e276-d248-4558-878d-6678b75f4ec8` produced a BRIEF at
12:01:40, a VETO at 12:01:45, and OWNER_REQUEST `0d2a7a40-2f8f-4951-b0a2-a0740823f462`
for `fu_call_daughter`. Erik's real reply is still required; no approval has been observed.
This case's observer also expired at 90 seconds while waiting for the human reply. Agents remain
connected and a late reply can complete the case, but this run failed the timing requirement.

GLM-only `reasoning_effort=low` restored generation within the existing 10-second request timeout;
model pins and timeouts were not changed. The previous 90-second demo failure remains part of the
run history. The full live demo is not green; the remaining steps below are rehearsal targets.

1. Configure credentials and catalog-verified Crusoe primary/fallback IDs, run the three role processes, and use `make demo` or the watch-only command in README.
2. Open the actual case in Band. Check the roster contains only Desk, Scribe, Critic and the human.
3. Observe the actual brief and verdict. Do not manufacture a bad quote or identifier leak to force a veto. Deterministic checks reject ownerless actions and recognized identifiers whenever present.
4. For an owner request, mention both Scribe and Critic and answer `/own <id> <name>` or `I'll own it`. The recorded human message is ownership provenance. Unassigned actions remain explicitly unresolved.
5. Approval names the exact revision and lists unresolved follow-ups. No graph/research/boundary room is implemented in this phase, so the full live demo still reports incomplete.

The offline test suite has 71 passing tests (66 product + 5 smoke). Run `make check` and optionally
`MOCK_BAND=1 MOCK_CRUSOE=1 make demo` to check offline behavior while the live case awaits a human ownership reply.
Call this an offline unit-test harness, never a live sponsor demo. It uses synthetic test examples,
not model-generated output from the selected fixture. No real graph writes or boundary are shown.

Text is sent to Band and Crusoe. Desk stays local; audio transcription is deferred.
The identifier guard is a regex/list demonstration, not certified de-identification.
