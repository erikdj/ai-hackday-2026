"""Neo4j backend matching MemoryStore. The neo4j package is imported lazily."""
import os
import time
import warnings
from pathlib import Path

from hallway.graph.store import IDENTIFIER_FIELDS, _store

_cached = None
_SCHEMA = Path(__file__).with_name("schema.cypher")
_WRITE = """
MERGE (p:Patient {pseudo_id:$pid}) ON CREATE SET p.created = timestamp()
MERGE (e:Encounter {id:$eid}) SET e.at = $at
MERGE (e)-[:OF]->(p)
WITH e
CALL (e) { WITH e UNWIND $findings AS row
  MERGE (e)-[:FOUND]->(:Finding {text:row.text, quote:row.quote, kind:row.kind})
  RETURN count(*) AS n }
CALL (e) { WITH e UNWIND $meds AS name
  MERGE (m:Med {name:name}) MERGE (e)-[:ON_MED]->(m) RETURN count(*) AS n }
CALL (e) { WITH e UNWIND $followups AS fu
  MERGE (e)-[:HAS_FOLLOWUP]->(c:Commitment {text:fu.text})
  SET c.quote = fu.quote, c.status = fu.status, c.owner = fu.owner
  WITH c, fu WHERE fu.owner <> ''
  MERGE (s:Staff {name:fu.owner}) MERGE (c)-[:OWNED_BY]->(s) RETURN count(*) AS n }
CALL (e) { WITH e UNWIND $accesses AS row
  MERGE (a:Agent {name:row.agent}) MERGE (f:Field {name:row.field})
  MERGE (a)-[:ACCESSED {field:row.field, purpose:row.purpose, ts:row.ts}]->(f)
  MERGE (e)-[:TOUCHED]->(f) RETURN count(*) AS n }
RETURN 1 AS ok
"""


def _need(name):
    value = os.environ.get(name)
    if not value:
        raise ValueError(name)
    return value


def _rows(items, fields):
    out = []
    for item in items or []:
        item = item if isinstance(item, dict) else {"text": item}
        out.append({key: item.get(key) for key in fields})
    return out


class Neo4jStore:
    def __init__(self):
        import neo4j

        self._neo4j = neo4j
        self.database = os.environ.get("NEO4J_DATABASE") or None
        self.driver = neo4j.GraphDatabase.driver(
            _need("NEO4J_URI"),
            auth=(_need("NEO4J_USERNAME"), _need("NEO4J_PASSWORD")),
            notifications_min_severity="OFF",
        )

    def reset(self):
        warnings.warn("Neo4jStore.reset() does not wipe the database", stacklevel=2)

    def apply_schema(self):
        for line in _SCHEMA.read_text().splitlines():
            stmt = line.strip()
            if stmt and not stmt.startswith("//"):
                self.driver.execute_query(stmt, database_=self.database)

    def _read(self, cypher, **params):
        neo4j = self._neo4j
        records, _, _ = self.driver.execute_query(
            neo4j.Query(cypher, timeout=20),
            params,
            routing_=neo4j.RoutingControl.READ,
            database_=self.database,
        )
        return records

    def write_approved(self, brief, manifest, pseudo_id, encounter_id):
        brief = brief or {}
        findings = []
        for kind in ("findings", "pending_results", "allergies"):
            for row in _rows(brief.get(kind), ("text", "quote")):
                row["kind"] = kind
                findings.append(row)
        meds = [item.get("name") if isinstance(item, dict) else item for item in (brief.get("meds") or [])]
        meds = [name for name in meds if name]
        followups = _rows(brief.get("follow_ups"), ("text", "quote", "status", "owner"))
        for row in followups:
            row["owner"] = row.get("owner") or ""
        accesses = [{k: e.get(k) for k in ("agent", "field", "purpose", "ts")} for e in (manifest or [])]
        existed = self._read(
            "MATCH (p:Patient {pseudo_id:$pid}) RETURN count(p) AS n", pid=pseudo_id
        )[0]["n"] > 0
        self.driver.execute_query(
            _WRITE,
            {
                "pid": pseudo_id,
                "eid": encounter_id,
                "at": int(time.time() * 1000),
                "findings": findings,
                "meds": meds,
                "followups": followups,
                "accesses": accesses,
            },
            database_=self.database,
        )
        return {"merged": existed, "patient": pseudo_id, "encounter": encounter_id}

    def who_saw_identifiers(self):
        records = self._read(
            "MATCH (a:Agent)-[:ACCESSED]->(f:Field) WHERE f.name IN $ids "
            "RETURN DISTINCT a.name AS name ORDER BY a.name",
            ids=list(IDENTIFIER_FIELDS),
        )
        return [record["name"] for record in records]

    def open_followups_by_owner(self):
        records = self._read(
            "MATCH (c:Commitment) WHERE c.status = 'owned' "
            "OPTIONAL MATCH (c)-[:OWNED_BY]->(s) "
            "RETURN coalesce(s.name, 'unresolved') AS owner, collect(c.text) AS texts"
        )
        return {record["owner"]: list(record["texts"]) for record in records}

    def prior_encounters(self, pseudo_id):
        records = self._read(
            "MATCH (e:Encounter)-[:OF]->(:Patient {pseudo_id:$pid}) "
            "RETURN e.id AS id ORDER BY e.at",
            pid=pseudo_id,
        )
        return [record["id"] for record in records]

    def lineage(self):
        records = self._read(
            "MATCH (a:Agent)-[r:ACCESSED]->(f:Field) "
            "RETURN a.name AS agent, r.field AS field, r.purpose AS purpose, r.ts AS ts"
        )
        return [record.data() for record in records]


def get_store():
    global _cached
    if os.environ.get("MOCK_NEO4J") == "1" or not os.environ.get("NEO4J_URI"):
        return _store()
    if _cached is None:
        _cached = Neo4jStore()
    return _cached
