#!/usr/bin/env bash
# Smoke test for the Crusoe Managed Inference path (prize qualification gate, Linear JV-97).
# Usage: ./scripts/check-crusoe.sh            (reads .env)
#        CRUSOE_API_KEY=... ./scripts/check-crusoe.sh
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -f .env ]; then set -a; . ./.env; set +a; fi
: "${CRUSOE_API_KEY:?set CRUSOE_API_KEY in .env}"
BASE="${CRUSOE_BASE_URL:-https://api.inference.crusoecloud.com/v1}"

echo "==> GET $BASE/models"
MODELS=$(curl -fsS "$BASE/models" -H "Authorization: Bearer $CRUSOE_API_KEY")
echo "$MODELS" | python3 -c 'import json,sys; [print(" -", m["id"]) for m in json.load(sys.stdin)["data"]]'

MODEL="${CRUSOE_MODEL:-$(echo "$MODELS" | python3 -c 'import json,sys; print(json.load(sys.stdin)["data"][0]["id"])')}"
echo "==> chat completion with $MODEL"
curl -fsS "$BASE/chat/completions" \
  -H "Authorization: Bearer $CRUSOE_API_KEY" -H "content-type: application/json" \
  -d "{\"model\":\"$MODEL\",\"max_tokens\":20,\"messages\":[{\"role\":\"user\",\"content\":\"Say only OK\"}]}" \
  | python3 -c 'import json,sys; r=json.load(sys.stdin); print("reply:", r["choices"][0]["message"]["content"]); print("model:", r.get("model"))'
echo "==> Crusoe path OK"
