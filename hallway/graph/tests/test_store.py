"""Tests for the in-memory Safe Scribe graph store."""
import importlib.util
import json
from pathlib import Path

import pytest

_spec = importlib.util.spec_from_file_location(
    "graph_store", Path(__file__).resolve().parents[1] / "store.py"
)
store = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(store)


@pytest.fixture(autouse=True)
def _reset():
    store.reset()


def test_merge_and_prior_encounters_oldest_first():
    first = store.write_approved({}, [], "p1", "e1")
    second = store.write_approved({}, [], "p1", "e2")
    store.write_approved({}, [], "p1", "e1")
    assert first["merged"] is False
    assert second["merged"] is True
    assert store.prior_encounters("p1") == ["e1", "e2"]


def test_who_saw_identifiers_sorted_and_empty():
    assert store.who_saw_identifiers() == []
    store.write_approved(
        {},
        [
            {"agent": "Desk", "field": "patient_name"},
            {"agent": "Scribe", "field": "dob"},
            {"agent": "Critic", "field": "mrn"},
            {"agent": "Desk", "field": "phone"},
            {"agent": "Scribe", "field": "address"},
            {"agent": "Grapher", "field": "meds"},
        ],
        "p",
        "e",
    )
    assert store.who_saw_identifiers() == ["Critic", "Desk", "Scribe"]


def test_open_followups_bucket_by_owner():
    store.write_approved(
        {
            "follow_ups": [
                {"owner": "Nurse", "text": "call", "status": "owned"},
                {"owner": "", "text": "labs", "status": "open"},
                {"text": "xray"},
            ]
        },
        [],
        "p",
        "e",
    )
    assert store.open_followups_by_owner() == {
        "Nurse": ["call"],
        "unresolved": ["labs", "xray"],
    }


def test_rewrite_replaces_findings():
    store.write_approved({"findings": [{"t": "a"}, {"t": "b"}]}, [], "p", "e")
    store.write_approved({"findings": [{"t": "c"}]}, [], "p", "e")
    assert len(store._store().encounters["e"]["findings"]) == 1


def test_transcript_is_never_stored():
    marker = "TRANSCRIPT-MARKER-XYZ"
    store.write_approved({"transcript": marker, "findings": [{"n": "ok"}]}, [], "p", "e")
    live = store._store()
    blob = json.dumps(
        {"encounters": live.encounters, "patients": live.patients}, default=list
    )
    assert marker not in blob


def test_caller_follow_up_is_not_aliased():
    item = {"owner": "Nurse", "text": "call", "status": "owned"}
    store.write_approved({"follow_ups": [item]}, [], "p", "e")
    item["text"] = "mutated"
    assert store._store().encounters["e"]["follow_ups"][0]["text"] == "call"


def test_write_and_read_share_backend_when_neo4j_configured(monkeypatch):
    import hallway.dashboard.queries as queries
    import hallway.graph.neo4j_store as neo4j_store
    import hallway.graph.store as graph_store

    monkeypatch.setenv("NEO4J_URI", "neo4j+s://stub")
    monkeypatch.setenv("NEO4J_USERNAME", "u")
    monkeypatch.setenv("NEO4J_PASSWORD", "p")
    monkeypatch.delenv("MOCK_NEO4J", raising=False)
    monkeypatch.setattr(graph_store, "_neo4j_instance", None)

    calls = []

    class StubNeo4jStore:
        def __init__(self):
            pass

        def write_approved(self, brief, manifest, pseudo_id, encounter_id):
            calls.append((brief, manifest, pseudo_id, encounter_id))
            return {"merged": False}

        def who_saw_identifiers(self):
            return ["Stub"]

    monkeypatch.setattr(neo4j_store, "Neo4jStore", StubNeo4jStore)

    result = graph_store.write_approved({"patient": {"pseudo_id": "p"}}, [], "p", "e")
    assert result["merged"] is False
    assert neo4j_store.get_store() is graph_store._store()
    assert queries.who_saw_identifiers()["agents"] == ["Stub"]
    assert calls  # recorded on the shared stub, not a second backend


def test_pending_with_owner_is_owned_and_pending_without_owner_is_unresolved():
    """The spine emits status pending/unresolved, never "owned" (PR #8 integration contract)."""
    brief = {
        "follow_ups": [
            {"owner": "night nurse", "text": "Repeat INR 06:00", "status": "pending"},
            {"owner": "", "text": "Call daughter about discharge", "status": "unresolved"},
            {"owner": "Maria", "text": "Home health referral", "status": "pending"},
            {"owner": "", "text": "Nutrition consult", "status": "pending"},
        ]
    }
    store.write_approved(brief, [], "p-1", "e-1")
    assert store.open_followups_by_owner() == {
        "night nurse": ["Repeat INR 06:00"],
        "Maria": ["Home health referral"],
        "unresolved": ["Call daughter about discharge", "Nutrition consult"],
    }
