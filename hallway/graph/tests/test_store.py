"""Tests for the in-memory HANDOFF graph store."""
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
