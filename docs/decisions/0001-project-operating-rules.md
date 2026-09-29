# ADR-0001: Project operating rules

Status: Accepted, 2026-09-29. Owners: Erik Jones, Jaiven Spence.

## Context

Two humans and several AI agents (Claude Code, Grok, Codex/Astra) work in one repo under a six-hour
hackday clock. Rules must be explicit so any fresh session behaves the same way.

## Decision

1. Work is tracked in Linear, project **AI Hackday 2026** (`P-JV-47`), Jaiven team. One issue per
   unit of work; branch names come from the issue.
2. Everything is a pull request into `main`. Human operators (Erik, Jaiven) approve and merge.
   Anyone may approve their own or another's PR. No gating: no required checks or reviewers.
3. Every change is reviewed by Astra (`gpt-6-astra` via the local Codex CLI / codex plugin) before
   the PR is opened. Reviews run locally in the session, not through GitHub bot round trips.
4. All code is written by Grok via the grok plugin skills / MCP tools. Claude Code orchestrates,
   plans, reviews, and manages Linear, docs, and PRs.
5. Crusoe is used for inference in a judge-visible way. This is the qualification requirement
   for the overall prize pool.
6. Secrets stay in `.env`; `.env.example` documents every credential.
7. The tech stack is chosen in ADR-0002 after the idea is fixed. Until then the repo stays
   stack-agnostic.

## Consequences

- Slightly more ceremony per change (issue, branch, Astra pass, PR) in exchange for auditability
  and the ability to hand any task to any session cold.
- No CI gate means a human merging is the only safety net after Astra. Humans read the Astra
  summary in the PR body before merging.
