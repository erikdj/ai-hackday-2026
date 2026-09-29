"""Query tests. No network and no FastAPI."""

import os

os.environ["MOCK_NEO4J"] = "1"

from hallway.dashboard import queries
from hallway.graph import store


def test_lineage_followups_history_and_band_url(monkeypatch):
    store.reset()
    store.write_approved(
        {
            "follow_ups": [
                {"owner": "Nurse", "text": "call", "status": "owned"},
                {"text": "labs"},
            ]
        },
        [
            {"agent": "Desk", "field": "patient_name"},
            {"agent": "Scribe", "field": "dob"},
            {"agent": "Critic", "field": "mrn"},
            {"agent": "Grapher", "field": "meds"},
        ],
        "pseudo-1",
        "enc-1",
    )
    seen = queries.who_saw_identifiers()
    assert seen["agents"] == ["Critic", "Desk", "Scribe"]
    assert seen["matches_expected"] is True
    followups = queries.open_followups()
    assert followups["unresolved_count"] == 1
    assert followups["by_owner"]["Nurse"] == ["call"]
    history = queries.patient_history("pseudo-1")
    assert history["encounters"] == ["enc-1"]
    assert history["count"] == 1
    assert queries.summary()["lineage_edges"] == 4
    monkeypatch.delenv("BAND_ROOM_URL_TEMPLATE", raising=False)
    assert queries.band_room_url("room") is None
    monkeypatch.setenv("BAND_ROOM_URL_TEMPLATE", "https://band.example/{room_id}")
    assert queries.band_room_url("room") == "https://band.example/room"


def _seed_identifier_agents(agents):
    store.reset()
    store.write_approved(
        {},
        [{"agent": name, "field": "patient_name"} for name in agents],
        "pseudo-1",
        "enc-1",
    )


def test_who_saw_identifiers_title_cases_lowercase_spine_names():
    _seed_identifier_agents(["desk", "scribe", "critic"])
    seen = queries.who_saw_identifiers()
    assert seen["agents"] == ["Critic", "Desk", "Scribe"]
    assert seen["matches_expected"] is True


def test_who_saw_identifiers_partial_set_does_not_match():
    _seed_identifier_agents(["Desk"])
    seen = queries.who_saw_identifiers()
    assert seen["agents"] == ["Desk"]
    assert seen["matches_expected"] is False
