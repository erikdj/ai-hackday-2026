"""Read-only dashboard queries over the in-memory graph store."""

import os

from hallway.graph import store

EXPECTED_AGENTS = ["Critic", "Desk", "Scribe"]


def who_saw_identifiers() -> dict:
    agents = store.who_saw_identifiers()
    return {
        "question": "which agents saw identifiers?",
        "agents": agents,
        "expected_on_demo": list(EXPECTED_AGENTS),
        "matches_expected": agents == EXPECTED_AGENTS,
    }


def open_followups() -> dict:
    by_owner = store.open_followups_by_owner()
    unresolved = by_owner.get("unresolved") or []
    return {"by_owner": by_owner, "unresolved_count": len(unresolved)}


def patient_history(pseudo_id) -> dict:
    encounters = store.prior_encounters(pseudo_id)
    return {"pseudo_id": pseudo_id, "encounters": encounters, "count": len(encounters)}


def summary() -> dict:
    patients = getattr(store._store(), "patients", None) or {}
    histories = [patient_history(pseudo_id) for pseudo_id in patients]
    return {
        "who_saw_identifiers": who_saw_identifiers(),
        "open_followups": open_followups(),
        "histories": histories,
        "lineage_edges": len(store.lineage()),
    }


def band_room_url(room_id: str) -> str | None:
    template = os.environ.get("BAND_ROOM_URL_TEMPLATE")
    if not template:
        return None
    return template.format(room_id=room_id)
