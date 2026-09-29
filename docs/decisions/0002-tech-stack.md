# ADR-0002: Tech stack

Status: Proposed (pending the idea from JV-95). Decide in JV-96.

## Context

_Paste the one-paragraph idea here when it lands._

The hackday rewards a live, end-to-end agent that uses Crusoe. DuploCloud provides a devkit with a
fixed extension archetype. Band rewards multi-agent coordination.

## Options

| Option | Best for | Cost |
| --- | --- | --- |
| A. DuploCloud devkit extension (C# backend + Angular remote + provisioning skill), LLM via OpenRouter preset pinned to Crusoe | Both DuploCloud prizes plus Crusoe qualification | Docker stack, .NET + Node build in a container, Angular federation; the `/duplo-extension` command scaffolds most of it |
| B. Standalone agent (Python or TypeScript) on Crusoe Managed Inference directly, optional Band | Crusoe overall prize, Band prize, fastest iteration | No DuploCloud prizes unless wrapped |
| C. Hybrid: standalone core (B) plus a thin DuploCloud extension that triggers it and shows results | All three prize families | Two surfaces to keep working in six hours |

## Decision

_TBD. Must name: language, runtime, LLM route to Crusoe (direct or OpenRouter preset), where the
demo runs, test framework, and the directory product code lives in._

## Consequences

_TBD._
