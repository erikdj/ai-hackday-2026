"""Neo4j backend matching MemoryStore. The neo4j package is imported lazily."""
import os
import time
import warnings
from pathlib import Path

from hallway.graph.store import IDENTIFIER_FIELDS, _store

_cached = None
_SCHEMA = Path(__file__).with_name("schema.cypher")


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
        followups = [
            row for row in _rows(brief.get("follow_ups"), ("text", "quote", "status", "owner"))
            if row.get("text")
        ]
        for index, row in enumerate(followups):
            row["owner"] = row.get("owner") or ""
            row["key"] = f"{encounter_id}:{index}"
        findings = [row for row in findings if row.get("text")]
        accesses = [
            {k: entry.get(k) for k in ("agent", "field", "purpose", "ts")}
            for entry in (manifest or [])
            if entry.get("agent") and entry.get("field")
        ]
        existed = self._read(
            "MATCH (p:Patient {pseudo_id:$pid}) RETURN count(p) AS n", pid=pseudo_id
        )[0]["n"] > 0
        params = {
            "pid": pseudo_id,
            "eid": encounter_id,
            "at": int(time.time() * 1000),
            "findings": findings,
            "meds": meds,
            "followups": followups,
            "accesses": accesses,
        }

        def _write(tx):
            tx.run(
                "MATCH (e:Encounter {id:$eid}) "
                "OPTIONAL MATCH (e)-[:FOUND]->(f:Finding) DETACH DELETE f",
                eid=encounter_id,
            )
            tx.run(
                "MATCH (e:Encounter {id:$eid}) "
                "OPTIONAL MATCH (e)-[:HAS_FOLLOWUP]->(c:Commitment) DETACH DELETE c",
                eid=encounter_id,
            )
            tx.run(
                "MATCH (e:Encounter {id:$eid}) "
                "OPTIONAL MATCH (e)-[r:ON_MED]->(:Med) DELETE r",
                eid=encounter_id,
            )
            tx.run(
                "MATCH (e:Encounter {id:$eid}) "
                "OPTIONAL MATCH (e)-[r:TOUCHED]->(:Field) DELETE r",
                eid=encounter_id,
            )
            tx.run(
                "MERGE (p:Patient {pseudo_id:$pid}) ON CREATE SET p.created = timestamp() "
                "MERGE (e:Encounter {id:$eid}) "
                "ON CREATE SET e.at = $at, e.seq = timestamp() "
                "MERGE (e)-[:OF]->(p)",
                pid=pseudo_id,
                eid=encounter_id,
                at=params["at"],
            )
            tx.run(
                "MATCH (e:Encounter {id:$eid}) UNWIND $findings AS row "
                "MERGE (e)-[:FOUND]->(f:Finding {text:row.text, kind:row.kind}) "
                "SET f.quote = coalesce(row.quote, '')",
                eid=encounter_id,
                findings=findings,
            )
            tx.run(
                "MATCH (e:Encounter {id:$eid}) UNWIND $meds AS name "
                "MERGE (m:Med {name:name}) MERGE (e)-[:ON_MED]->(m)",
                eid=encounter_id,
                meds=meds,
            )
            tx.run(
                "MATCH (e:Encounter {id:$eid}) UNWIND $followups AS fu "
                "MERGE (e)-[:HAS_FOLLOWUP]->(c:Commitment {key:fu.key}) "
                "SET c.text = fu.text, c.quote = fu.quote, "
                "c.status = fu.status, c.owner = fu.owner "
                "WITH c, fu WHERE fu.owner <> '' "
                "MERGE (s:Staff {name:fu.owner}) MERGE (c)-[:OWNED_BY]->(s)",
                eid=encounter_id,
                followups=followups,
            )
            tx.run(
                "MATCH (e:Encounter {id:$eid}) UNWIND $accesses AS row "
                "MERGE (a:Agent {name:row.agent}) MERGE (f:Field {name:row.field}) "
                "MERGE (a)-[r:ACCESSED {field: row.field, purpose: coalesce(row.purpose, ''), "
                "ts: coalesce(row.ts, '')}]->(f) "
                "MERGE (e)-[:TOUCHED]->(f)",
                eid=encounter_id,
                accesses=accesses,
            )

        with self.driver.session(database=self.database) as session:
            session.execute_write(_write)
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
            "MATCH (c:Commitment) "
            "OPTIONAL MATCH (c)-[:OWNED_BY]->(s) "
            "WITH CASE WHEN c.status = 'owned' AND coalesce(s.name, '') <> '' "
            "THEN s.name ELSE 'unresolved' END AS owner, c "
            "RETURN owner, collect(c.text) AS texts"
        )
        return {record["owner"]: list(record["texts"]) for record in records}

    def prior_encounters(self, pseudo_id):
        records = self._read(
            "MATCH (e:Encounter)-[:OF]->(:Patient {pseudo_id:$pid}) "
            "RETURN e.id AS id ORDER BY e.seq, e.at",
            pid=pseudo_id,
        )
        return [record["id"] for record in records]

    def patient_ids(self) -> list[str]:
        records = self._read(
            "MATCH (p:Patient) RETURN p.pseudo_id ORDER BY p.pseudo_id"
        )
        return [record["p.pseudo_id"] for record in records]

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
