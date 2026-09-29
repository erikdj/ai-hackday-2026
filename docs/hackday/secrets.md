# Secrets: Doppler is the source of truth

Project `ai-hackday-2026`, config `dev`, workplace Trustedge-AI. Erik owns it; Jaiven is invited
by email from the Doppler dashboard (Workplace > Team). Nothing is ever pasted into Slack, Linear,
a PR, or a Band room.

## Each laptop, once

```bash
curl -Ls https://cli.doppler.com/install.sh | sh      # or brew install dopplerhq/cli/doppler
doppler login
cd ai-hackday-2026 && doppler setup                    # pick ai-hackday-2026 / dev
```

## Run anything with secrets injected, nothing on disk

```bash
doppler run -- python3 scripts/check_crusoe_tools.py --max 20
doppler run -- python3 scripts/make_fixtures.py handoff_2
# once PR #8 lands (Makefile, docker-compose.yml):
doppler run -- make demo
doppler run -- docker compose up
```

## If a tool insists on a file

```bash
doppler secrets download --no-file --format env > .env     # .env is gitignored
```

Band credentials are read from the environment first (`BAND_<ROLE>_AGENT_ID` / `BAND_<ROLE>_API_KEY`
for desk, scribe, researcher, critic, grapher, closer). Under `doppler run` no `agent_config.yaml`
exists on disk; the YAML loader is only a fallback for a machine without Doppler, and that file is
gitignored.

## Vultr VM

Install the CLI. Do not `doppler login` on the VM (that is a browser login for a person). Create a
service token scoped to `dev` (Dashboard > Access > Service Tokens) and pass it in the environment:

```bash
export DOPPLER_TOKEN=dp.st....            # service token, dev config
doppler run -- docker compose up -d       # once PR #8 lands the compose file
```

Never bake secrets into the image.

## Rotation

Edit the value in the dashboard; every `doppler run` picks it up on the next start. If a key was
ever pasted somewhere it should not have been, rotate it at the provider first, then in Doppler.
