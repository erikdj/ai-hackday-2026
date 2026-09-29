"""Brave Search fact for a named drug. One request, one sourced fact with a URL.

Mock when MOCK_BRAVE=1 or no BRAVE_API_KEY (clearly labelled, never presented as
real evidence). Live: Brave Web Search API, 10 s timeout, 2 retries, key never logged.
"""
from __future__ import annotations

import logging
import os
import time

import httpx

ENDPOINT = "https://api.search.brave.com/res/v1/web/search"
log = logging.getLogger("safescribe.research")


def _mock(drug: str) -> dict:
    return {
        "drug": drug,
        "title": f"MOCK: no live Brave key; interaction guidance for {drug} not retrieved",
        "url": "https://example.invalid/mock-brave",
        "snippet": "Mock enrichment. Set BRAVE_API_KEY and MOCK_BRAVE=0 for a sourced fact.",
        "source": "mock",
        "mock": True,
    }


def fact(drug: str, *, timeout: float = 10.0, retries: int = 2, count: int = 5) -> dict | None:
    """Return {drug, title, url, snippet, source, mock} for the first usable result, or None."""
    drug = (drug or "").strip()
    if not drug:
        raise ValueError("drug name required")
    key = os.environ.get("BRAVE_API_KEY", "").strip()
    if os.environ.get("MOCK_BRAVE", "0") == "1" or not key:
        log.info("brave mock fact for %s (no key or MOCK_BRAVE=1)", drug)
        return _mock(drug)
    params = {"q": f"{drug} drug interactions guideline", "count": count, "safesearch": "moderate"}
    headers = {"Accept": "application/json", "X-Subscription-Token": key}
    last: Exception | None = None
    for attempt in range(retries + 1):
        started = time.monotonic()
        try:
            with httpx.Client(timeout=timeout) as client:
                response = client.get(ENDPOINT, params=params, headers=headers)
            response.raise_for_status()
            results = (response.json().get("web") or {}).get("results") or []
            for item in results:
                url = str(item.get("url") or "")
                if url.startswith("http"):
                    log.info("brave fact for %s in %.1fs: %s", drug, time.monotonic() - started, url)
                    return {"drug": drug, "title": str(item.get("title") or "").strip(),
                            "url": url, "snippet": str(item.get("description") or "").strip(),
                            "source": "brave", "mock": False}
            log.warning("brave returned no usable result for %s", drug)
            return None
        except Exception as exc:  # noqa: BLE001 - retried, then reported by type only
            last = exc
            log.warning("brave attempt %d failed for %s: %s", attempt + 1, drug, type(exc).__name__)
    log.error("brave failed after %d attempts for %s: %s", retries + 1, drug, type(last).__name__)
    return None


if __name__ == "__main__":
    import json
    import sys
    logging.basicConfig(level=logging.INFO)
    print(json.dumps(fact(sys.argv[1] if len(sys.argv) > 1 else "ciprofloxacin"), indent=2))
