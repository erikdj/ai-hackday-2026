"""Compliance narrative written by a Crusoe model from lineage metadata only.

The model receives agent names, identifier *field names* per agent, and pseudonymous counts.
It never receives a transcript, a brief, an identifier value or a pseudonymous id. The exact
payload sent is returned next to the narrative so a judge can verify that claim. If Crusoe is
unavailable the call fails closed; there is no other provider.
"""

from __future__ import annotations

import json
import re

from hallway.dashboard import queries
from hallway.graph.neo4j_store import get_store

IDENTIFIER_FIELDS = ("patient_name", "dob", "mrn", "phone", "address")
_SAFE_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9 _-]{0,40}$")
# Narrative uses the FAST tier client (Qwen, thinking off). The llm() factory keys options by
# runtime role; 'grapher' is the non-transcript role on that tier, so its client is reused here.
_CLIENT_ROLE = "grapher"

SYSTEM_PROMPT = (
    "You write a short compliance statement for a hospital privacy officer about an AI scribe "
    "system. Use only the JSON you are given. Do not invent agents, fields, patients, numbers or "
    "people. Do not name any person. Three sentences, plain language: which agents processed "
    "patient identifiers and which identifier categories, that downstream agents did not, and "
    "that the record is pseudonymous. No preamble."
)


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
    for row in store.lineage():
        agent = _safe(row.get("agent")) if isinstance(row, dict) else None
        if not agent:
            continue
        seen_agents.add(agent)
        field = row.get("field")
        if field in IDENTIFIER_FIELDS:
            fields_by_agent.setdefault(agent, set()).add(field)
    summary = queries.summary()
    return {
        "system": "Safe Scribe",
        "agents_with_identifier_access": sorted(fields_by_agent),
        "identifier_fields_by_agent": {a: sorted(f) for a, f in sorted(fields_by_agent.items())},
        "agents_without_identifier_access": sorted(seen_agents - set(fields_by_agent)),
        "pseudonymous_patients": len(summary.get("histories") or []),
        "encounters": sum(int(h.get("count") or 0) for h in summary.get("histories") or []),
        "lineage_edges": int(summary.get("lineage_edges") or 0),
        "unresolved_follow_ups": int((summary.get("open_followups") or {}).get("unresolved_count") or 0),
    }


def _client():
    from hallway.common.llm import llm

    return llm(_CLIENT_ROLE)


def compliance_narrative(client=None) -> dict:
    """Ask Crusoe for the narrative. Raises InferenceUnavailable (never falls back elsewhere)."""
    from langchain_core.messages import HumanMessage, SystemMessage

    inputs = narrative_inputs()
    client = client or _client()
    response = client.invoke(
        [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=json.dumps(inputs, sort_keys=True))]
    )
    text = response.content if isinstance(response.content, str) else ""
    if not text.strip():
        from hallway.common.llm import InferenceUnavailable

        raise InferenceUnavailable("Crusoe returned no narrative text")
    return {
        "provider": "crusoe",
        "model": getattr(client, "model_name", None) or getattr(client, "model", None),
        "inputs": inputs,
        "narrative": text.strip(),
    }
