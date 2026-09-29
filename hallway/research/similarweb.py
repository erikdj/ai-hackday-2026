"""Similarweb organization-legitimacy facts. The API key never leaves this module."""

import json
import logging
import os
import re
from datetime import date
from urllib import error, parse, request

log = logging.getLogger(__name__)

SIMILARWEB_PAGE = "https://www.similarweb.com/website/{domain}/"
API_BASE = "https://api.similarweb.com/v1"
_TLDS = "com|org|net|health|care|io"
_DOT = re.compile(rf"\bdot\s+({_TLDS})\b", re.IGNORECASE)
_BOUNDARY = frozenset(
    "is at called visit website site to on the a an their our its of and it go try see".split()
)
_LABEL = re.compile(r"[A-Za-z0-9-]+")
_ATTEMPTS = 3
_TIMEOUT_S = 10
_NOT_FOUND = object()


def _spoken_candidates(text: str) -> list[str]:
    found: list[str] = []
    for match in _DOT.finditer(text):
        tokens: list[str] = []
        for token in reversed(text[: match.start()].split()):
            if token.lower() in _BOUNDARY or _LABEL.fullmatch(token) is None:
                break
            tokens.append(token.lower())
            if len(tokens) == 4:
                break
        if tokens:
            found.append("".join(reversed(tokens)) + "." + match.group(1).lower())
    return found


def spoken_domain(text: str, name: str | None = None) -> str | None:
    """Pull a spoken domain ('example dot org') out of free text."""
    if not text:
        return None
    candidates = _spoken_candidates(text)
    key = re.sub(r"[^a-z0-9]", "", (name or "").strip().lower())
    if not key:
        return candidates[0] if candidates else None
    for candidate in candidates:
        if candidate.rsplit(".", 1)[0].replace("-", "") == key:
            return candidate
    return None


def _shift_month(today: date, delta: int) -> str:
    index = today.year * 12 + (today.month - 1) + delta
    year, month = divmod(index, 12)
    return f"{year:04d}-{month + 1:02d}"


def _claim(name: str, domain: str, rank: int | None, visits: int | None, month: str | None) -> str:
    rank_bit = f"global rank {rank:,}" if rank is not None else "not in Similarweb's global ranking"
    when = f" ({month})" if month else ""
    visit_bit = f"about {visits:,} visits/month{when}" if visits is not None else "visit count unavailable"
    return f"{name} ({domain}) is an active domain on Similarweb: {rank_bit}, {visit_bit}."


def _fact(name: str, domain: str, rank: int | None, visits: int | None, month: str | None, *, found: bool = True) -> dict:
    claim = _claim(name, domain, rank, visits, month) if found else (
        f"{name} ({domain}) is not listed on Similarweb (no traffic data); "
        "treat this referral organization as unverified."
    )
    return {
        "kind": "organization",
        "name": name,
        "domain": domain,
        "active": found,
        "status": "active" if found else "not_found",
        "rank": rank,
        "monthly_visits": visits,
        "month": month,
        "low_traffic": (visits is not None and visits < 5000) if found else None,
        "source": "similarweb",
        "url": SIMILARWEB_PAGE.format(domain=domain),
        "claim": claim,
    }


def _default_fetch(url: str) -> dict:
    with request.urlopen(url, timeout=_TIMEOUT_S) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("similarweb payload was not an object")
    return payload


def _get(fetch, url: str) -> dict | None:
    for attempt in range(_ATTEMPTS):
        try:
            payload = fetch(url)
        except error.HTTPError as exc:
            if exc.code == 404:
                return _NOT_FOUND
            retry, status = 500 <= exc.code <= 599, exc.code
        except (error.URLError, TimeoutError):
            retry, status = True, "network"
        except (OSError, ValueError, json.JSONDecodeError):
            retry, status = False, "error"
        else:
            if isinstance(payload, dict):
                return payload
            retry, status = False, "bad-payload"
        if retry and attempt + 1 < _ATTEMPTS:
            continue
        log.warning("similarweb request failed status=%s", status)
        return None
    return None


def _rank(payload: dict) -> int | None:
    block = payload.get("similar_rank")
    if not isinstance(block, dict):
        return None
    try:
        rank = int(block["rank"])
    except (KeyError, TypeError, ValueError):
        return None
    return rank if rank > 0 else None


def _visits(payload: dict) -> tuple[int | None, str | None]:
    rows = payload.get("visits")
    last = rows[-1] if isinstance(rows, list) and rows and isinstance(rows[-1], dict) else None
    if last is None:
        return None, None
    raw_date = last.get("date")
    month = raw_date[:7] if isinstance(raw_date, str) and len(raw_date) >= 7 else None
    try:
        return int(float(last["visits"])), month
    except (KeyError, TypeError, ValueError):
        return None, month


def organization_fact(name: str, domain: str, *, fetch=None) -> dict | None:
    """Rank and visits for one domain. Fail closed: never raise, never echo the key."""
    if os.environ.get("MOCK_SIMILARWEB") == "1":
        return _fact(name, domain, 1_234_567, 12_000, "2026-08")
    key = os.environ.get("SIMILARWEB_API_KEY", "").strip()
    if not key:
        log.warning("similarweb request failed status=missing-key")
        return None
    fetch = fetch or _default_fetch
    today = date.today()
    query = parse.urlencode(
        {
            "api_key": key,
            "start_date": _shift_month(today, -3),
            "end_date": _shift_month(today, -1),
            "country": "world",
            "granularity": "monthly",
            "main_domain_only": "false",
            "format": "json",
        }
    )
    domain_q = parse.quote(domain, safe="")
    rank_url = f"{API_BASE}/similar-rank/{domain_q}/rank?api_key={parse.quote(key, safe='')}"
    visits_url = f"{API_BASE}/website/{domain_q}/total-traffic-and-engagement/visits?{query}"
    rank_payload = _get(fetch, rank_url)
    if rank_payload is _NOT_FOUND:
        return _fact(name, domain, None, None, None, found=False)
    visits_payload = _get(fetch, visits_url)
    if not isinstance(rank_payload, dict) or not isinstance(visits_payload, dict):
        return None
    rank = _rank(rank_payload)
    visits, month = _visits(visits_payload)
    if rank is None and visits is None:
        log.warning("similarweb request failed status=no-metrics")
        return None
    return _fact(name, domain, rank, visits, month)


def fact_from_transcript(transcript: str, name: str, *, fetch=None) -> dict | None:
    """Resolve a spoken domain in a transcript, then look it up."""
    domain = spoken_domain(transcript, name)
    if domain is None:
        return None
    return organization_fact(name, domain, fetch=fetch)
