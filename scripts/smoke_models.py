#!/usr/bin/env python3
"""Discover Crusoe IDs and verify forced and automatic function calls on two candidates.

Usage: python scripts/smoke_models.py --list
       python scripts/smoke_models.py MODEL_ID_A MODEL_ID_B
Only nonsecret model IDs, outcomes, durations and exception types are recorded.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import time

from dotenv import load_dotenv
from openai import OpenAI


def valid_probe(message):
    calls = message.tool_calls or []
    if len(calls) != 1 or calls[0].function.name != "record_probe":
        return False
    try:
        return json.loads(calls[0].function.arguments) == {"value": "hallway"}
    except (TypeError, json.JSONDecodeError):
        return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("models", nargs="*")
    parser.add_argument("--list", action="store_true", help="Discover models without inference")
    parser.add_argument("--output", default="artifacts/crusoe-smoke.json")
    args = parser.parse_args()
    load_dotenv()
    if not os.getenv("CRUSOE_API_KEY"):
        parser.error("CRUSOE_API_KEY is required; no mock smoke test exists")
    if not args.list and (len(args.models) != 2 or len(set(args.models)) != 2):
        parser.error("Supply two distinct catalog model IDs, or use --list")
    report = {"provider": "crusoe", "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "results": []}
    success = False
    try:
        with OpenAI(api_key=os.environ["CRUSOE_API_KEY"],
                    base_url=os.getenv("CRUSOE_BASE_URL", "https://api.inference.crusoecloud.com/v1"),
                    timeout=10.0, max_retries=2) as client:
            catalog = sorted(model.id for model in client.models.list().data)
            report["catalog"] = catalog
            if args.list:
                print("\n".join(catalog))
                success = True
            else:
                missing = [model for model in args.models if model not in catalog]
                if missing:
                    report["error"] = "Candidate absent from discovered catalog"
                    print("Candidate absent from Crusoe catalog; use --list", file=sys.stderr)
                else:
                    for model in args.models:
                        for mode in ("forced", "auto"):
                            started = time.monotonic()
                            result = {"model": model, "mode": mode, "ok": False}
                            try:
                                response = client.chat.completions.create(
                                    model=model,
                                    max_tokens=128,
                                    messages=[{"role": "user", "content": "Call record_probe exactly once with value hallway."}],
                                    tools=[{"type": "function", "function": {
                                        "name": "record_probe", "description": "Record a smoke-test marker.",
                                        "parameters": {"type": "object", "properties": {"value": {"type": "string"}},
                                                       "required": ["value"], "additionalProperties": False}}}],
                                    tool_choice=({"type": "function", "function": {"name": "record_probe"}}
                                                 if mode == "forced" else "auto"),
                                )
                                result["ok"] = bool(response.choices and valid_probe(response.choices[0].message))
                                if not result["ok"]:
                                    result["error"] = "Invalid function call or arguments"
                            except Exception as exc:
                                result["error"] = type(exc).__name__
                                print(f"Crusoe chat.completions failed: {type(exc).__name__}", file=sys.stderr)
                            result["elapsed_seconds"] = round(time.monotonic() - started, 3)
                            report["results"].append(result)
                    success = all(result["ok"] for result in report["results"])
    except Exception as exc:
        report["error"] = type(exc).__name__
        print(f"Crusoe models.list failed: {type(exc).__name__}", file=sys.stderr)
    report["ok"] = success
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Crusoe smoke {'PASS' if success else 'FAIL'}; nonsecret evidence: {path}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
