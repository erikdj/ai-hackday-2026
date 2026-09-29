# AI Hackday 2026 — team operating rules

This file is the source of truth for every human and agent session working in this
repo. Read it fully before doing anything. Project-level rules here override personal defaults.

## The event

- **The AI Conference Hack Day 2026**, September 29, 2026, San Francisco. Six hours of build time.
- **Team:** Erik Jones (`erikdj`, GitHub `erikdj`) and Jaiven Spence. Both are human operators.
- **Repo:** https://github.com/erikdj/ai-hackday-2026 (default branch `main`).
- **Prize target:** the Crusoe-funded overall pool ($5,000 / $3,000 / $2,000). **Projects MUST use
  Crusoe to qualify.** Secondary: Best Use of BAND ($1,000), DuploCloud Best Agent Overall ($750),
  DuploCloud Most Sponsor Tools Meaningfully Integrated ($750), Neo4j credits, Plaud ($1,000/$500).
- Judging is **live**. The agent must run and do the promised thing when judges look. Slides alone lose.
- A sponsor tool only counts if it does real work in the project. Plugged in and idle does not count.
- Full brief: `docs/hackday/event-brief.md`. Sponsor wiring: `docs/hackday/sponsor-integrations.md`.

## Roles

| Who | Role |
| --- | --- |
| **Erik and Jaiven** | Decide the idea and the stack, sign off on PRs, merge. |
| **Orchestrator agent** | Plans, breaks work into Linear issues, delegates coding, runs reviews, opens PRs, keeps docs current. On Erik's machine this is Claude Code. |
| **Coder agent** | Writes the code: features, tests, fixes, refactors, scaffolding. On Erik's machine this is Grok (grok plugin). |
| **Reviewer agent** | Reviews every change locally before a PR is opened. On Erik's machine this is Astra (`gpt-6-astra` via Codex CLI). |

**Each contributor picks their own local agent team.** Not everyone has Astra or Grok. What is
fixed is the shape (orchestrate, code, review locally, PR, human merge), not the vendors. Say which
tools you used in the PR body. Erik's setup is documented below as the reference configuration;
adapt the commands to whatever you run.

## Hard rules

1. **Track everything in Linear.** Project **AI Hackday 2026** (`P-JV-47`) in the **Jaiven** team.
   Every unit of work is an issue there. Create the issue before starting the work; move it to
   In Progress when you start and Completed/Released when the PR merges. Use the issue's
   `gitBranchName` (e.g. `feature/jv-97-...`) as the branch name and put the issue id (`JV-NN`) in
   the PR title.
2. **Everything is a pull request.** No direct pushes to `main`. One issue per PR where practical.
3. **Humans approve PRs.** Erik or Jaiven signs off and merges. Anyone may approve their own PR or
   another's PR. **No gating:** no required reviewers, no required status checks, no branch
   protection that blocks a merge. CI is informational only. GitHub will not let an author click
   Approve on their own PR; for your own PR, the merge itself is the approval.
4. **Every change gets an independent AI review locally before the PR is opened.** On Erik's
   machine that is Astra via the Codex CLI or codex plugin. Other contributors use whatever
   reviewer agent they have. The review runs **in the session**, not as a GitHub bot or PR round
   trip. Paste the summary into the PR body. See "Reviewer agent: Astra (reference)" below.
5. **Coding is delegated to a coder agent, separate from the orchestrator.** On Erik's machine
   that is Grok via the grok plugin skills or MCP tools; the orchestrator (Claude) does not
   hand-write implementation code. Other contributors use their own coder agent. See "Coder
   agent: Grok (reference)" below.
6. **Crusoe is mandatory.** The product must use Crusoe in a way judges can see (model served by
   Crusoe via Managed Inference or an OpenRouter preset pinned to `crusoe`). Never ship a demo path
   that silently falls back to another provider.
7. **No secrets in git.** Keys live in `.env` (gitignored). Every new credential gets a blank line
   in `.env.example` with a one-line comment.
8. **Tech stack is undecided until ADR-0002 is accepted** (`docs/decisions/0002-tech-stack.md`).
   Until then, do not add language-specific tooling to the repo root.

## Workflow for any task

1. Confirm or create the Linear issue. Read its description.
2. `git checkout main && git pull`, then `git checkout -b <linear gitBranchName>`.
3. Delegate the implementation to your coder agent. Review its diff yourself for scope and safety.
4. Run tests (once a stack exists). Fix via the coder agent.
5. Run your reviewer agent. Address CRITICAL and HIGH findings. Re-run until clean.
6. Update `changelog.md`, `backlog.md`, and README/docs if structure changed.
7. Commit with conventional commits (`feat:`, `fix:`, `docs:`, `chore:`, `test:`, `refactor:`).
8. Push with `-u` and open the PR with `gh pr create` using `.github/PULL_REQUEST_TEMPLATE.md`.
   Paste the reviewer agent's summary into the PR body and name the tools you used.
9. Tell the human operator the PR is ready. They approve and merge. Move the Linear issue.

## Coder agent: Grok (reference)

Erik's coder agent. Grok runs through the grok plugin (`grok@grok-marketplace`), which is installed and authenticated
in subscription mode on this machine.

- Check readiness: `grok_build_status` MCP tool (or `/grok:setup`).
- Route first when fit is unclear: `grok_build_route` / `/grok:route`, follow `nextAction`.
- Plan for risky or wide edits: `grok_build_plan` / `/grok:plan`, wait for human approval.
- Execute: `grok_build_delegate` / `/grok:delegate` with an absolute `cwd`. Use `worktree: true`
  for large or risky changes and review in the worktree before merging.
- Presets: `/grok:tests`, `/grok:migrate`, `/grok:boilerplate`. Follow-ups: `/grok:resume`.
- Never make code edits through `grok_cli` / `/grok:cli` (no provenance). Use it only for
  non-editing subcommands.
- Grok never commits. Claude reviews the diff, then Astra reviews, then Claude commits.
- Keep in the orchestrator (no delegation): architecture and API-shape decisions, secrets
  handling, final review and quality gate.

Contributors without Grok: any coder agent works (Codex, Claude Code subagents, Cursor, etc.).
Keep the same split: the agent that plans and reviews is not the one that writes the code.

## Reviewer agent: Astra (reference)

Erik's reviewer agent. Astra is OpenAI's `gpt-6-astra`, the default model in `~/.codex/config.toml` for Codex CLI
(`codex-cli` 0.154+). The codex plugin (`codex@openai-codex`) wraps it for this session.

- Standard review of the branch: `/codex:review --wait --base main` (or `--scope working-tree`
  before committing).
- Design challenge: `/codex:adversarial-review --wait --base main <focus>`.
- Investigation or a second implementation opinion: `/codex:rescue <task>`.
- CLI fallback (same thing, no plugin): `codex review --base main -c model='"gpt-6-astra"'`.
  Note: `codex review` rejects a custom prompt when `--base` is given; use
  `/codex:adversarial-review` (or `codex exec` with a prompt) for focused instructions.
  A full pass on this repo takes roughly five minutes at xhigh reasoning; run it in the background.
  If it fails with a bwrap loopback error, the working fallback (drops the sandbox, so only on a
  trusted machine) is `codex review --base main -c model='"gpt-6-astra"'
  -c model_reasoning_effort='"medium"' -c sandbox_mode='"danger-full-access"' </dev/null`.
- Review output is returned verbatim. Fix findings via the coder agent, then re-run. A PR is not
  ready until the last review pass has no CRITICAL or HIGH findings, or the human operator
  explicitly waives them.

Contributors without Astra: use any independent reviewer (Claude Code `/code-review`, Codex with
another model, Gemini, a second Claude session). The requirement is a fresh set of eyes that did
not write the code, run locally, before the PR opens.

## Repo layout

```
CLAUDE.md                      this file
README.md                      project overview and quick start
backlog.md / changelog.md      what is next / what shipped (update in every PR)
.env.example                   every credential the project needs, blank
.github/                       PR template, informational CI
docs/hackday/                  event brief, sponsor integrations, demo script
docs/decisions/                ADRs (0001 rules, 0002 tech stack)
docs/reference/duplocloud-devkit/  vendored devkit hackday docs (Apache-2.0)
scripts/                       stack-agnostic helper scripts (Crusoe smoke test)
```

Product code goes under `hallway/` once ADR-0002 is accepted (Python, Band + LangGraph, Crusoe
direct, FastAPI, Neo4j). The HALLWAY build brief is `docs/hackday/hallway-build-brief.md` (PR #4). If a DuploCloud
extension is added later, it lives under `extensions/<name>/` per the devkit docs.

## Docs and hygiene

- Every PR updates `changelog.md` (Unreleased section) and, if it changes future work, `backlog.md`.
- Update `README.md` when structure or run instructions change.
- Keep files small and focused. Prefer many small modules. No hardcoded config.
- Tests are written first once a stack exists. Aim for 80% coverage on product code; the hackday
  demo path must have at least one end-to-end test.
- Improve skills and this file when you learn something the next session needs.
