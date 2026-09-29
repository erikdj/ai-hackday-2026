# DuploCloud devkit — hackday docs (vendored)

Copied from https://github.com/duplocloud/devkit/tree/main/hackday at commit `e9f016fd90a67611907fcf673701351669eaa47d` on 2026-09-29
so every agent session can read them offline. Licensed Apache-2.0 by DuploCloud (see the devkit
LICENSE and NOTICE). Image links are relative to the upstream repo and will not render here.

Files: Installing DevKit, Sponsor Integrations, Adding Providers, Adding MCP Servers, Adding Skills,
Adding Personas, Adding Workspaces, Getting Support.

Key facts pulled out:
- Platform is six Docker containers; `./run.sh` needs a work email (personal domains rejected).
- Ports 4210 (UI), 60031 (studio), 8010, 27018, 6061, 6333.
- Extensions are C# backend + Angular remote + provisioning skill, scaffolded by `/duplo-extension`
  in Claude Code from the devkit checkout. Adopt the devkit into your own repo with
  `./scripts/init-project.sh <remote>`.
- Crusoe/Nebius are reached through an OpenRouter preset pinned with `only: [crusoe]` and
  `allow_fallbacks: false`; switch the running stack with `./scripts/switch-llm.sh gateway ...`.
- DuploCloud judges two prizes: best agent overall (live, end to end) and most sponsor tools wired
  in meaningfully.
