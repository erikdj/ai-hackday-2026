"""Graph store selector. Memory by default; Neo4j when NEO4J_URI is set."""
import os

IDENTIFIER_FIELDS = {"patient_name", "dob", "mrn", "phone", "address"}

_BRIEF_LISTS = ("meds", "allergies", "pending_results", "findings", "follow_ups")

_instance = None
_neo4j_instance = None


def _copy_items(items):
    if not items:
        return []
    return [dict(item) if isinstance(item, dict) else item for item in items]


class MemoryStore:
    """Dict/set graph of patients, encounters, and field-access lineage."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.patients = {}
        self.encounters = {}
        self.accessed = []

    def write_approved(self, brief, manifest, pseudo_id, encounter_id):
        merged = pseudo_id in self.patients
        patient = self.patients.setdefault(pseudo_id, {"encounters": []})
        if encounter_id not in patient["encounters"]:
            patient["encounters"].append(encounter_id)
        fields = set()
        for entry in manifest or []:
            record = {
                "agent": entry.get("agent"),
                "field": entry.get("field"),
                "purpose": entry.get("purpose"),
                "ts": entry.get("ts"),
            }
            if record not in self.accessed:
                self.accessed.append(record)
            if record["field"]:
                fields.add(record["field"])
        brief = brief or {}
        self.encounters[encounter_id] = {
            "pseudo_id": pseudo_id,
            **{key: _copy_items(brief.get(key)) for key in _BRIEF_LISTS},
            "fields": fields,
        }
        return {"merged": merged, "patient": pseudo_id, "encounter": encounter_id}

    def who_saw_identifiers(self):
        agents = {
            entry["agent"]
            for entry in self.accessed
            if entry.get("field") in IDENTIFIER_FIELDS and entry.get("agent")
        }
        return sorted(agents)

    def open_followups_by_owner(self):
        grouped = {}
        unresolved = []
        for encounter in self.encounters.values():
            for item in encounter["follow_ups"]:
                owner = item.get("owner") or ""
                text = item.get("text")
                if item.get("status") == "owned" and owner:
                    grouped.setdefault(owner, []).append(text)
                else:
                    unresolved.append(text)
        if unresolved:
            grouped["unresolved"] = unresolved
        return grouped

    def prior_encounters(self, pseudo_id):
        patient = self.patients.get(pseudo_id)
        if not patient:
            return []
        return list(patient["encounters"])

    def patient_ids(self) -> list[str]:
        return sorted(self.patients)

    def lineage(self):
        return [dict(entry) for entry in self.accessed]


def _store():
    global _instance, _neo4j_instance
    if os.environ.get("MOCK_NEO4J") == "1" or not os.environ.get("NEO4J_URI"):
        if _instance is None:
            _instance = MemoryStore()
        return _instance
    if _neo4j_instance is None:
        from hallway.graph.neo4j_store import Neo4jStore

        _neo4j_instance = Neo4jStore()
    return _neo4j_instance


def reset():
    global _instance, _neo4j_instance
    if _instance is None:
        _instance = MemoryStore()
    else:
        _instance.reset()
    if _neo4j_instance is not None:
        _neo4j_instance.reset()


def write_approved(brief, manifest, pseudo_id, encounter_id):
    return _store().write_approved(brief, manifest, pseudo_id, encounter_id)


def who_saw_identifiers():
    return _store().who_saw_identifiers()


def open_followups_by_owner():
    return _store().open_followups_by_owner()


def prior_encounters(pseudo_id):
    return _store().prior_encounters(pseudo_id)


def patient_ids():
    return _store().patient_ids()


def lineage():
    return _store().lineage()
