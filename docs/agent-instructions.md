# How agents work in this repo

The authoritative rules live in [CLAUDE.md](../CLAUDE.md). This page is the short version that
used to sit in the root README, kept here so the README can be the pitch.

## The shape

1. Every task is a Linear issue in project **AI Hackday 2026** (`P-JV-47`, Jaiven team). Create it
   before starting; move it to In Progress; move it to Completed/Released when the PR merges. Branch
   name is the issue's `gitBranchName`; the issue id goes in the PR title.
2. Three roles per contributor, three different agents: an **orchestrator** plans and reviews, a
   **coder** writes the code, an independent **reviewer** reads the diff locally before the PR
   opens. Erik's reference set: Claude Code orchestrating, Grok coding, Astra (`gpt-6-astra` via
   Codex CLI) reviewing. Jaiven's set differed. The shape is fixed, the vendors are not.
3. Everything ships as a pull request. A human (or the overseer session, under Erik's standing
   authorization) merges after reading the review and running the suite in a clean worktree. No
   branch protection, no required checks; the review runs in the session, never as a PR bot.
4. Every PR updates `changelog.md` and, when it changes future work, `backlog.md`.

## The overseer

A third Claude session acted as an independent overseer for the day: it held the clock (cut lines,
feature freeze, code freeze, recording window), posted checkpoints to Linear, merged reviewed PRs,
and challenged any claim not backed by a live run (offline tests were treated as necessary, never
sufficient). Its rules of engagement, learned the hard way:

- Review the commit GitHub will actually merge: fetch `refs/pull/N/head`, not a same-named branch.
- Run `date` before writing any time into Linear or a PR.
- One voice to the humans: the contributor session owns asks to Erik; the overseer routes through it.
- Never start Band agent processes from a second machine; one WebSocket per agent id.
- Doppler configuration keys (model pins, aliases) have one owner; others add credentials only.

## Commands

```bash
# review a PR head in a clean worktree
git fetch origin refs/pull/N/head:refs/remotes/pr/N
git worktree add ../ai-hackday-prN pr/N
make check VENV=../ai-hackday-pr8/.venv            # or your own venv with the Band SDK

# independent local review (Astra)
codex review --base origin/main -c model='"gpt-6-astra"' -c model_reasoning_effort='"medium"'
```

Model pins, flags and every credential come from Doppler (`doppler run -- <cmd>`); see
[hackday/secrets.md](hackday/secrets.md).
