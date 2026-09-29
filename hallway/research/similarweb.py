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
    "is at called visit website site to on the a an their our its of and it it's go try see".split()
)
_STOP_CHARS = set(",.;:!?\"'`“”‘’")
_ATTEMPTS = 3
_TIMEOUT_S = 10


def _normalize(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else " " for ch in text.lower())
    return " ".join(cleaned.split())


def _name_domain(normalized: str, name: str) -> str | None:
    words = _normalize(name).split()
    if not words:
        return None
    forms = (re.escape(" ".join(words)), re.escape("".join(words)))
    match = re.search(rf"\b(?:{forms[0]}|{forms[1]}) dot ({_TLDS})\b", normalized)
    if match is None:
        return None
    return "".join(words) + "." + match.group(1)


def _fallback_domain(text: str) -> str | None:
    match = _DOT.search(text)
    if match is None:
        return None
    words: list[str] = []
    for token in reversed(text[: match.start()].split()):
        if any(ch in token for ch in _STOP_CHARS) or token.lower() in _BOUNDARY:
            break
        if not re.fullmatch(r"[A-Za-z0-9]+", token):
            break
        words.append(token.lower())
        if len(words) == 4:
            break
    if not words:
        return None
    words.reverse()
    return "".join(words) + "." + match.group(1).lower()


def spoken_domain(text: str, name: str | None = None) -> str | None:
    """Pull a spoken domain ('example dot org') out of free text."""
    if not text:
        return None
    if name:
        named = _name_domain(_normalize(text), name)
        if named:
            return named
    return _fallback_domain(text)


def _shift_month(today: date, delta: int) -> str:
    index = today.year * 12 + (today.month - 1) + delta
    year, month = divmod(index, 12)
    return f"{year:04d}-{month + 1:02d}"


def _claim(name: str, domain: str, rank: int | None, visits: int | None, month: str | None) -> str:
    rank_bit = f"global rank {rank:,}" if rank is not None else "global rank unavailable"
    if visits is not None:
        when = f" ({month})" if month else ""
        visit_bit = f"about {visits:,} visits/month{when}"
    else:
        visit_bit = "visit count unavailable"
    return f"{name} ({domain}) is an active domain on Similarweb: {rank_bit}, {visit_bit}."


def _fact(name: str, domain: str, rank: int | None, visits: int | None, month: str | None) -> dict:
    return {
        "kind": "organization",
        "name": name,
        "domain": domain,
        "active": True,
        "rank": rank,
        "monthly_visits": visits,
        "month": month,
        "source": "similarweb",
        "url": SIMILARWEB_PAGE.format(domain=domain),
        "claim": _claim(name, domain, rank, visits, month),
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
            if 500 <= exc.code <= 599 and attempt + 1 < _ATTEMPTS:
                continue
            log.warning("similarweb request failed status=%s", exc.code)
            return None
        except (error.URLError, TimeoutError):
            if attempt + 1 < _ATTEMPTS:
                continue
            log.warning("similarweb request failed status=network")
            return None
        except (OSError, ValueError, json.JSONDecodeError):
            log.warning("similarweb request failed status=error")
            return None
        if not isinstance(payload, dict):
            log.warning("similarweb request failed status=bad-payload")
            return None
        return payload
    return None


def _rank(payload: dict) -> int | None:
    block = payload.get("similar_rank")
    if not isinstance(block, dict):
        return None
    try:
        return int(block["rank"])
    except (KeyError, TypeError, ValueError):
        return None


def _visits(payload: dict) -> tuple[int | None, str | None]:
    rows = payload.get("visits")
    if not isinstance(rows, list) or not rows or not isinstance(rows[-1], dict):
        return None, None
    last = rows[-1]
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
    if rank_payload is None:
        return None
    visits_payload = _get(fetch, visits_url)
    if visits_payload is None:
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
