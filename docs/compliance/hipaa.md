# HIPAA posture of Safe Scribe

Written 2026-09-29 at the hackday code freeze. This is an engineering statement of what the system
does and does not do, and what the vendors we used say in their public terms. It is not legal advice
and it is not a compliance certification. **Every patient in this repository is synthetic**, which
is the only reason the architecture below can be run against public AI services today.

## What HIPAA asks for, in the terms that matter here

- **Covered entities and business associates.** A hospital is a covered entity. Any vendor that
  creates, receives, maintains or transmits protected health information (PHI) on its behalf is a
  business associate and must sign a **business associate agreement (BAA)**.
- **Minimum necessary.** Each party sees only the PHI it needs for its function.
- **Security Rule safeguards.** Access control, audit controls (who accessed what, when), integrity,
  transmission security, and a documented risk analysis.
- **De-identification.** Either the Safe Harbor method (remove eighteen listed identifier types) or
  Expert Determination. Data that is not de-identified is PHI.

## What Safe Scribe does today, mapped to those

| HIPAA concept | What the system does | Where |
| --- | --- | --- |
| Minimum necessary | Audio never leaves the laptop. Only three agents (Desk, Scribe, Critic) and the nurse are in the room that holds the transcript. Everything downstream receives a pseudonymous brief and never the transcript. Room membership is enforced by Band and checked on every write. | `hallway/ingest/`, `hallway/common/room.py` (roster checks, approved room) |
| Access controls | Rooms are created by the runtime, not by agents' free choice; an unexpected participant raises; the approved room is created only after a digest-matched approval. | `publish_approved_boundary`, `approved_payload` |
| Audit controls | The access manifest records which agent processed which identifier field, with the source message id; it is written to the graph as `(Agent)-[:ACCESSED]->(Field)` and answers "which agents saw identifiers". Provenance is runtime processing evidence, not read receipts. | `hallway/common/room.py` (`processing_manifest`), `hallway/graph/` |
| Identifier boundary | A deterministic gate plus model judgment scans the outbound brief for name, date of birth, record number, phone and address; a hit is a veto the model cannot override. Readable room summaries are checked against the transcript and fall back to counts only. | `hallway/common/brief.py` (`identifier_violations`, `identifier_fields`), `readable_summary` |
| Pseudonymization | The patient is referred to by a pseudonymous id generated with a local salt; merge across encounters is by that id only, never by similarity. | `hallway/ingest/fixture.py`, `hallway/graph/store.py` |
| Human accountability | Ownership of a follow-up is never inferred; it comes from an authenticated human message in the room. | `ownership_errors` |
| Fail closed | If Crusoe is unavailable the case pauses; it never routes to another provider. Missing Neo4j configuration on the live path raises instead of falling back to memory. | `hallway/common/llm.py`, Grapher tool |

## What Safe Scribe does not do (the gaps)

- **Not de-identified.** The gate covers five identifier categories; Safe Harbor lists eighteen
  (dates other than year, ages over 89, geographic subdivisions, device ids, URLs, biometric
  identifiers, photographs, and more). The transcript itself is PHI by definition and is held in the
  case room.
- **No BAAs.** None of the vendors that see PHI were used under a BAA today.
- **No encryption-at-rest or key-management claims** for the vendors' storage; we rely on their terms.
- **No formal risk analysis, policies, training, or incident procedures.** Those are a program, not
  a hackday.
- **No enclave.** Nothing runs in confidential computing. Inference happens on the provider's GPUs
  in the provider's memory.
- **Provenance is processing evidence, not read receipts.** The manifest says an agent's runtime
  processed a field; it does not measure what a model attended to.

## Vendor terms as read on 2026-09-29

| Vendor | What it sees in Safe Scribe | Public terms found | Source |
| --- | --- | --- | --- |
| **Crusoe** Managed Inference | Transcript (Desk, Scribe, Critic prompts), briefs, verdicts | Inputs and outputs "not stored to disk", processed only as long as necessary; not used for training without opt-in; metadata logged. Restrictions: customers will not use the service "to transmit, store, or process health information subject to United States HIPAA regulations." No BAA offered. Crusoe Cloud holds ISO 27001 and ISO 42001. No enclave claim. | [Crusoe Legal Center](https://legal.crusoe.ai/), [Managed Inference TOS](https://legal.crusoe.ai/open-router), [ISO announcement](https://www.crusoe.ai/resources/blog/crusoe-cloud-achieves-iso-27001-and-42001-certifications) |
| **Band** | Every room message: transcript, briefs, verdicts, the nurse's reply, the redacted envelope | Terms of Service and Privacy Policy (effective July 6, 2026) contain no clause on HIPAA, PHI, BAA, encryption, subprocessors or hosting location; retention "as long as reasonably necessary". | [Terms](https://band.ai/terms-of-service), [Privacy Policy](https://band.ai/privacy-policy) |
| **Neo4j** Aura | Pseudonymous patient and encounter nodes, clinical items, lineage edges. Never the transcript, never identifier values (field names only). | Neo4j's AuraDB FAQ: "Yes. Neo4j AuraDB is now HIPAA-compliant. If you need to store protected health information (PHI), you can sign a Business Associate Agreement (BAA) with Neo4j." The FAQ does not list eligible tiers; the cloud agreement requires the BAA to be in place before HIPAA-covered use. The AuraDB Free instance used today has no BAA. | [Neo4j AuraDB FAQ](https://neo4j.com/cloud/platform/aura-graph-database/faq/), [Neo4j Hybrid Cloud & Software Agreement](https://neo4j.com/legal-terms/hybrid-agreement/) |
| **DuploCloud** | The lineage answer only (agent names and field names) | Vendor pages describe a platform that automates SOC 2, HIPAA, PCI and HITRUST controls for customer infrastructure; they do not state an attestation held by DuploCloud itself. The devkit trial used today carries no compliance attestation and is licensed for local development only. | [DuploCloud SOC 2](https://duplocloud.com/compliance/soc2/), [HIPAA white paper](https://duplocloud.com/white-papers/pci-and-hipaa-compliance-with-duplocloud), devkit `TERMS.md` |
| **Brave Search** | Drug names from a bounded vocabulary | No PHI by construction. | `hallway/common/research_room.py` (`DRUGS`) |
| **Similarweb** | One domain name spoken in the visit | No PHI by construction. | `hallway/research/similarweb.py` |
| **faster-whisper** | Audio, on the laptop | Local open-source model; nothing leaves the machine. | `hallway/ingest/transcribe.py` |
| **xAI** text-to-speech | Scripted synthetic text | Used once to synthesize the fixtures; never to be given real audio or real text. | `scripts/make_fixtures.py` |

## What a real deployment needs

1. **BAAs or hospital-controlled substitutes for every PHI-touching component.** Crusoe: a
   negotiated dedicated deployment with a BAA, or open models on GPUs the hospital controls (the
   client is OpenAI-compatible and the endpoint is a single configuration value). Band: an
   enterprise agreement with a BAA, or a hospital-controlled room service with the same roster and
   message-authentication semantics. Neo4j: Aura under a signed BAA, or self-managed Neo4j inside
   the hospital network.
2. **Compliant infrastructure.** DuploCloud's platform provisioning the deployment in the hospital's
   cloud account or on Crusoe Cloud compute, with its HIPAA control set applied and audited.
3. **Identifier gate to Safe Harbor.** Extend detection to the eighteen categories, add a human
   review of every redaction, and store the review as lineage.
4. **Encryption and keys.** Encryption in transit everywhere (already TLS), at rest under
   hospital-managed keys for the graph and any message store.
5. **Risk analysis, policies, training, breach procedures, retention schedule.** Program work.
6. **Real audit semantics.** Keep the processing manifest, and add gateway-level logging of every
   inference request so "who saw what" is measured, not inferred.

## What we say and do not say

Say: identifier gate, boundary control, access lineage, pseudonymous, synthetic patients, "the
audio never leaves the laptop", "three named agents in one room see the transcript and we can prove
it". Do not say: HIPAA compliant, de-identified, enclave, BAA in place, "no one sees patient data".
