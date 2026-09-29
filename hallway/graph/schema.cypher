// Relationships: (Encounter)-[:OF]->(Patient), (Encounter)-[:FOUND]->(Finding), (Encounter)-[:ON_MED]->(Med), (Encounter)-[:HAS_FOLLOWUP]->(Commitment), (Commitment)-[:OWNED_BY]->(Staff), (Agent)-[:ACCESSED {field,purpose,ts}]->(Field), (Encounter)-[:TOUCHED]->(Field).
CREATE CONSTRAINT patient_pseudo_id IF NOT EXISTS FOR (p:Patient) REQUIRE p.pseudo_id IS UNIQUE;
CREATE CONSTRAINT encounter_id IF NOT EXISTS FOR (e:Encounter) REQUIRE e.id IS UNIQUE;
CREATE CONSTRAINT staff_name IF NOT EXISTS FOR (s:Staff) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT field_name IF NOT EXISTS FOR (f:Field) REQUIRE f.name IS UNIQUE;
CREATE CONSTRAINT agent_name IF NOT EXISTS FOR (a:Agent) REQUIRE a.name IS UNIQUE;
CREATE CONSTRAINT med_name IF NOT EXISTS FOR (m:Med) REQUIRE m.name IS UNIQUE;
CREATE VECTOR INDEX patient_embedding IF NOT EXISTS FOR (p:Patient) ON (p.embedding) OPTIONS {indexConfig: {`vector.dimensions`: 1024, `vector.similarity_function`: 'cosine'}};
