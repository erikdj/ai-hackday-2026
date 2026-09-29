#!/usr/bin/env python3
"""List Crusoe Managed Inference models and probe OpenAI-style tool calling."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

TRANSPORT = None
WEATHER_TOOL = {
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get the current weather for a city.",
        "parameters": {
            "type": "object",
            "properties": {"city": {"type": "string"}},
            "required": ["city"],
        },
    },
}


def load_dotenv() -> None:
    path = Path(__file__).resolve().parent.parent / ".env"
    if not path.is_file():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key, value = key.strip(), value.strip().strip("'\"")
        if key and not os.environ.get(key):
            os.environ[key] = value


def request_json(method, url, headers, body, timeout):
    if TRANSPORT is not None:
        return TRANSPORT(method, url, headers, body, timeout)
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        err = RuntimeError(f"HTTP {exc.code}: {exc.read().decode(errors='replace')[:300]}")
        err.status = exc.code  # type: ignore[attr-defined]
        raise err from exc


def list_models(base, key):
    payload = request_json("GET", f"{base.rstrip('/')}/models", {"Authorization": f"Bearer {key}"}, None, 30)
    return list(payload.get("data") or [])


def _classify(message):
    calls = message.get("tool_calls") or []
    if not calls:
        return "FAIL", "no tool_calls"
    fn = (calls[0].get("function") or {})
    if fn.get("name") != "get_weather":
        return "FAIL", f"unexpected tool {fn.get('name')}"
    raw = fn.get("arguments")
    try:
        parsed = json.loads(raw) if isinstance(raw, str) else raw
    except (json.JSONDecodeError, TypeError):
        return "WEAK", "arguments not valid JSON"
    if isinstance(parsed, dict) and "city" in parsed:
        return "PASS", ""
    return "WEAK", "arguments missing city"


def test_tool_call(base, key, model):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": "What is the weather in Paris? Use the tool."}],
        "tools": [WEATHER_TOOL],
        "tool_choice": "auto",
        "max_tokens": 200,
    }
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    url = f"{base.rstrip('/')}/chat/completions"
    started, last = time.perf_counter(), None
    for attempt in range(2):
        try:
            payload = request_json("POST", url, headers, body, 30)
            message = ((payload.get("choices") or [{}])[0].get("message") or {})
            result, note = _classify(message)
            return {
                "model": model,
                "result": result,
                "latency_ms": int((time.perf_counter() - started) * 1000),
                "tokens": (payload.get("usage") or {}).get("total_tokens"),
                "note": note[:120],
            }
        except Exception as exc:  # noqa: BLE001 — retry once
            last = exc
            if attempt == 0:
                continue
    if getattr(last, "status", None) in (401, 403):
        raise last
    return {
        "model": model, "result": "FAIL",
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "tokens": None, "note": str(last)[:120],
    }


def _context(entry):
    if not isinstance(entry, dict):
        return 0
    for field in ("context_length", "max_model_len"):
        if isinstance(entry.get(field), int):
            return entry[field]
    return 0


def recommend(results, models):
    by_id = {m.get("id"): m for m in models if isinstance(m, dict)}
    passes = [r for r in results if r.get("result") == "PASS"]
    note = f"{len(passes)} PASS" + ("; fewer than 3 models passed tool calling" if len(passes) < 3 else "")
    empty = {"fast": None, "strong": None, "critic": None, "note": note}
    if not passes:
        return empty
    fast = min(passes, key=lambda r: r.get("latency_ms") or 0)["model"]
    if any(_context(by_id.get(r["model"])) for r in passes):
        strong = max(passes, key=lambda r: _context(by_id.get(r["model"])))["model"]
    else:
        others = [r["model"] for r in passes if r["model"] != fast]
        strong = others[0] if others else fast
    vendor = lambda mid: (mid or "").split("/", 1)[0]
    critic = next((r["model"] for r in passes if vendor(r["model"]) != vendor(strong)), None)
    return {"fast": fast, "strong": strong, "critic": critic, "note": note}


def _mock_transport():
    catalog = [
        {"id": "moonshotai/Kimi-K2.6", "context_length": 262144},
        {"id": "zai/GLM-5.2", "context_length": 128000},
        {"id": "nvidia/Nemotron-3-Nano", "context_length": 131072},
        {"id": "qwen/Qwen3-8B", "context_length": 8192},
    ]

    def transport(method, url, headers, body, timeout):
        time.sleep(0)
        if str(url).rstrip("/").endswith("/models"):
            return {"data": catalog}
        model = (body or {}).get("model", "")
        message = {"content": "no tools"} if "Qwen" in model else {
            "tool_calls": [{"function": {"name": "get_weather", "arguments": json.dumps({"city": "Paris"})}}]
        }
        return {"choices": [{"message": message}], "usage": {"total_tokens": 12}}

    return transport


def main(argv=None) -> int:
    global TRANSPORT
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", default="")
    parser.add_argument("--max", type=int, default=4)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args(argv)
    if args.mock:
        TRANSPORT = _mock_transport()
    key = os.environ.get("CRUSOE_API_KEY", "")
    base = os.environ.get("CRUSOE_BASE_URL") or "https://api.inference.crusoecloud.com/v1"
    if not key and not args.mock:
        print("CRUSOE_API_KEY is required", file=sys.stderr)
        return 2
    key = key or "mock"
    try:
        models = list_models(base, key)
    except RuntimeError as exc:
        print(str(exc)[:200], file=sys.stderr)
        return 2 if getattr(exc, "status", None) in (401, 403) else 1
    wanted = {m.strip() for m in args.models.split(",") if m.strip()} if args.models else None
    ids = [e.get("id") for e in models if isinstance(e, dict) and e.get("id") and (wanted is None or e.get("id") in wanted)]
    results = []
    try:
        for mid in ids[: args.max]:
            results.append(test_tool_call(base, key, mid))
    except RuntimeError as exc:
        if getattr(exc, "status", None) in (401, 403):
            print(str(exc)[:200], file=sys.stderr)
            return 2
        raise
    rec = recommend(results, models)
    if args.json:
        json.dump({"models": models, "results": results, "recommendation": rec}, sys.stdout)
        sys.stdout.write("\n")
    else:
        print(f"{'model':<32} {'result':<6} {'latency_ms':>10} {'tokens':>8}  note")
        for row in results:
            print(f"{row['model']:<32} {row['result']:<6} {row['latency_ms']:>10} {str(row['tokens']):>8}  {row['note']}")
        print(f"recommend fast={rec['fast']} strong={rec['strong']} critic={rec['critic']} ({rec['note']})")
    return 0 if any(r["result"] == "PASS" for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
