# Documentation index

Start with the root [README.md](../README.md) (the pitch and directory) and
[CLAUDE.md](../CLAUDE.md) (team operating rules). Everything else is listed here.

## For judges and readers

| Document | What it is |
| --- | --- |
| [hackday/demo-script.md](hackday/demo-script.md) | The recorded demo: scene-setting, eight timed beats with fallbacks, technical dive, tool-by-tool proof, judge Q&A, rehearsal log |
- [hackday/stage-pitch.md](hackday/stage-pitch.md): the two-minute stage pitch for the top-10 round, sixty-second proof order, judge Q&A.
| [hackday/submission-readme.md](hackday/submission-readme.md) | The short project description pasted into the submission form |
| [hackday/integration-ledger.md](hackday/integration-ledger.md) | One row per sponsor tool: verified / mocked / attempted / not used, with the evidence line and time |
| [compliance/hipaa.md](compliance/hipaa.md) | HIPAA posture: what Safe Scribe does and does not do, what each vendor's terms say, the gaps, the production path |
| [hackday/sponsor-integrations.md](hackday/sponsor-integrations.md) | How each sponsor tool is wired, including the DuploCloud devkit on WSL2 |
| [hackday/safe-scribe-build-brief.md](hackday/safe-scribe-build-brief.md) | The build brief the agents worked from: architecture, protocol, phases, cut lines |
| [hackday/event-brief.md](hackday/event-brief.md) | Sponsors, prizes, judging criteria, timeline |

## For contributors and agents

| Document | What it is |
| --- | --- |
| [agent-instructions.md](agent-instructions.md) | How work happens here: orchestrator, coder, reviewer; Linear, PRs, local review, human merge |
| [../CLAUDE.md](../CLAUDE.md) | The hard rules and reference configuration (Grok as coder, Astra as reviewer) |
| [hackday/secrets.md](hackday/secrets.md) | Doppler is the source of truth for every key; how to run anything with `doppler run` |
| [decisions/0001-project-operating-rules.md](decisions/0001-project-operating-rules.md) | ADR-0001: operating rules |
| [decisions/0002-tech-stack.md](decisions/0002-tech-stack.md) | ADR-0002: Python, Band + LangGraph, Crusoe direct, FastAPI, Neo4j |
| [../hallway/README.md](../hallway/README.md) | Product module notes: the spine, verified status, runtime flags, deviations |
| [../hallway/fixtures/README.md](../hallway/fixtures/README.md) | The four synthetic scenarios, planted lines, expected verdicts |
| [../hallway/dashboard/README.md](../hallway/dashboard/README.md) | Judge dashboard endpoints and the MCP tool |
| [reference/duplocloud-devkit/](reference/duplocloud-devkit/) | Vendored DuploCloud devkit docs (Apache-2.0) |
| [../backlog.md](../backlog.md) / [../changelog.md](../changelog.md) | What is next / what shipped |
