# Safe Scribe by TrustEdge AI — phase-1 rehearsal

Use synthetic patient fixtures only. Real Crusoe function calling passed, and Band message parsing,
case creation and case reading were verified in `550fdd7`. Scribe's GLM/Kimi inference attempts
timed out through retries: no BRIEF, veto or approval was observed. The live run failed its
90-second budget. These steps are a rehearsal target, not a completed demo.

1. Configure credentials and catalog-verified Crusoe primary/fallback IDs, run the three role processes, and use `make demo` or the watch-only command in README.
2. Open the actual case in Band. Check the roster contains only Desk, Scribe, Critic and the human.
3. Observe the actual brief and verdict. Do not manufacture a bad quote or identifier leak to force a veto. Deterministic checks reject ownerless actions and recognized identifiers whenever present.
4. For an owner request, mention both Scribe and Critic and answer `/own <id> <name>` or `I'll own it`. The recorded human message is ownership provenance. Unassigned actions remain explicitly unresolved.
5. Approval names the exact revision and lists unresolved follow-ups. No graph/research/boundary room is implemented in this phase, so the full live demo still reports incomplete.

The offline test suite has 52 passing tests. Run `make check` and optionally
`MOCK_BAND=1 MOCK_CRUSOE=1 make demo` to check offline behavior while the live inference issue is unresolved.
Call this an offline unit-test harness, never a live sponsor demo. It uses synthetic test examples,
not model-generated output from the selected fixture. No real graph writes or boundary are shown.

Text is sent to Band and Crusoe. Desk stays local; audio transcription is deferred.
The identifier guard is a regex/list demonstration, not certified de-identification.
