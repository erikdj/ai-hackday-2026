"""Read-only dashboard queries over the configured graph store."""

import os

from hallway.graph.neo4j_store import get_store

EXPECTED_AGENTS = ["Critic", "Desk", "Scribe"]


def _display_agents(raw) -> list[str]:
    if not isinstance(raw, list):
        return []
    return sorted(
        {name.strip().title() for name in raw if isinstance(name, str) and name.strip()}
    )


def _matches_expected(agents: list[str]) -> bool:
    return {name.casefold() for name in agents} == {
        name.casefold() for name in EXPECTED_AGENTS
    }


def who_saw_identifiers() -> dict:
    agents = _display_agents(get_store().who_saw_identifiers())
    return {
        "question": "which agents saw identifiers?",
        "agents": agents,
        "expected_on_demo": list(EXPECTED_AGENTS),
        "matches_expected": _matches_expected(agents),
    }


def open_followups() -> dict:
    by_owner = get_store().open_followups_by_owner()
    unresolved = by_owner.get("unresolved") or []
    return {"by_owner": by_owner, "unresolved_count": len(unresolved)}


def patient_history(pseudo_id) -> dict:
    encounters = get_store().prior_encounters(pseudo_id)
    return {"pseudo_id": pseudo_id, "encounters": encounters, "count": len(encounters)}


def summary() -> dict:
    backend = get_store()
    if hasattr(backend, "patient_ids"):
        patient_ids = backend.patient_ids()
    else:
        patient_ids = sorted(getattr(backend, "patients", {}).keys())
    histories = [patient_history(pseudo_id) for pseudo_id in patient_ids]
    return {
        "who_saw_identifiers": who_saw_identifiers(),
        "open_followups": open_followups(),
        "histories": histories,
        "lineage_edges": len(backend.lineage()),
    }


def band_room_url(room_id: str) -> str | None:
    template = os.environ.get("BAND_ROOM_URL_TEMPLATE")
    if not template:
        return None
    return template.format(room_id=room_id)
