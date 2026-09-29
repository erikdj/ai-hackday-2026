"""Compliance narrative written by a Crusoe model from lineage metadata only.

The model receives agent names, identifier *field names* per agent, and pseudonymous counts.
It never receives a transcript, a brief, an identifier value or a pseudonymous id. The exact
payload sent is returned next to the narrative so a judge can verify that claim. If Crusoe is
unavailable the call fails closed; there is no other provider.

Standard library only (urllib), so the dashboard can serve this on an interpreter that has
FastAPI and the Neo4j driver but not the agents' LangChain stack.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request

from hallway.dashboard import queries
from hallway.graph.neo4j_store import get_store

CRUSOE_ENDPOINT = "https://api.inference.crusoecloud.com/v1"
IDENTIFIER_FIELDS = ("patient_name", "dob", "mrn", "phone", "address")
# Purposes that mean the agent handled case evidence (transcript or brief) on the PHI side. An
# agent with such rows but no identifier-field rows has unverified evidence, not proven non-access.
_PHI_SIDE_PURPOSES = ("intake", "extraction", "review")
_SAFE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9 _-]{0,40}$")
_TIMEOUT_SECONDS = 30
_MAX_TOKENS = 400

SYSTEM_PROMPT = (
    "You write a short compliance statement for a hospital privacy officer about an AI scribe "
    "system. Use only the JSON you are given. Do not invent agents, fields, patients, numbers or "
    "people. Do not name any person. Three sentences, plain language: which agents processed "
    "patient identifiers and which identifier categories, which agents have no identifier access, "
    "which (if any) have unverified evidence and must not be described as non-accessing, and that "
    "the record is pseudonymous. No preamble."
)


class NarrativeUnavailable(RuntimeError):
    """Crusoe did not return a narrative. Nothing else is tried."""


def _safe(name) -> str | None:
    if not isinstance(name, str):
        return None
    name = name.strip()
    return name.title() if _SAFE_NAME.match(name) else None


def narrative_inputs() -> dict:
    """The complete, allowlisted payload the model sees: names, field categories, counts."""
    store = get_store()
    fields_by_agent: dict[str, set[str]] = {}
    seen_agents: set[str] = set()
    phi_side: set[str] = set()
    for row in store.lineage():
        agent = _safe(row.get("agent")) if isinstance(row, dict) else None
        if not agent:
            continue
        seen_agents.add(agent)
        field = row.get("field")
        if field in IDENTIFIER_FIELDS:
            fields_by_agent.setdefault(agent, set()).add(field)
        elif row.get("purpose") in _PHI_SIDE_PURPOSES:
            phi_side.add(agent)
    with_access = set(fields_by_agent)
    unverified = phi_side - with_access
    without_access = seen_agents - with_access - unverified
    summary = queries.summary()
    return {
        "system": "Safe Scribe",
        "agents_with_identifier_access": sorted(with_access),
        "identifier_fields_by_agent": {a: sorted(f) for a, f in sorted(fields_by_agent.items())},
        "agents_with_unverified_identifier_evidence": sorted(unverified),
        "agents_without_identifier_access": sorted(without_access),
        "pseudonymous_patients": len(summary.get("histories") or []),
        "encounters": sum(int(h.get("count") or 0) for h in summary.get("histories") or []),
        "lineage_edges": int(summary.get("lineage_edges") or 0),
        "unresolved_follow_ups": int((summary.get("open_followups") or {}).get("unresolved_count") or 0),
    }


def _models() -> list[str]:
    primary = os.environ.get("CRUSOE_MODEL_FAST", "").strip()
    fallback = (
        os.environ.get("CRUSOE_MODEL_FAST_FALLBACK", "").strip()
        or os.environ.get("CRUSOE_MODEL_FALLBACK", "").strip()
    )
    return [m for m in (primary, fallback) if m]


def crusoe_chat(messages: list[dict]) -> tuple[str, str]:
    """POST to Crusoe chat completions: primary FAST model, then the Crusoe fallback. Returns (text, model)."""
    endpoint = os.environ.get("CRUSOE_BASE_URL", CRUSOE_ENDPOINT).rstrip("/")
    if endpoint != CRUSOE_ENDPOINT:
        raise ValueError("Only the Crusoe managed inference endpoint is permitted")
    key = os.environ.get("CRUSOE_API_KEY", "").strip()
    models = _models()
    if not key or not models:
        raise ValueError("CRUSOE_API_KEY and CRUSOE_MODEL_FAST are required")
    thinking_off = {v.strip() for v in os.environ.get("CRUSOE_DISABLE_THINKING_MODELS", "").split(",") if v.strip()}
    last_error: Exception | None = None
    for model in models:
        body: dict = {"model": model, "messages": messages, "max_tokens": _MAX_TOKENS}
        if model in thinking_off:
            body["chat_template_kwargs"] = {"enable_thinking": False}
        if model == "zai-org/GLM-5.3":
            body["reasoning_effort"] = "low"
        request = urllib.request.Request(
            endpoint + "/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
                data = json.loads(response.read())
            text = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
            if text.strip():
                return text.strip(), str(data.get("model") or model)
            last_error = NarrativeUnavailable(f"{model} returned no text")
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError, OSError) as exc:
            last_error = exc
    raise NarrativeUnavailable(f"Crusoe narrative failed: {type(last_error).__name__}: {last_error}")


def compliance_narrative(chat=None) -> dict:
    """Ask Crusoe for the narrative. Raises NarrativeUnavailable; never falls back to another provider."""
    inputs = narrative_inputs()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps(inputs, sort_keys=True)},
    ]
    text, model = (chat or crusoe_chat)(messages)
    if not isinstance(text, str) or not text.strip():
        raise NarrativeUnavailable("Crusoe returned no narrative text")
    return {"provider": "crusoe", "model": model, "inputs": inputs, "narrative": text.strip()}
