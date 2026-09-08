# NORA Legal Intelligence Foundation V1 Architecture

## 1. Jurisdiction Source Registry

The `JurisdictionSourceRegistry` (`src/nora_legal_research/jurisdiction_registry.py`) defines a structured, provider-neutral catalog of governing primary law, administrative regulations, procedural rules, official slip opinions, and explanatory guidance.

Every source entry records:
- **Stable ID**: deterministic identifier (e.g., `US-WI-STATUTES-CH48`, `US-MN-MRJPP`, `US-FED-USC-CIVIL-RIGHTS-CHILD-WELFARE`).
- **Jurisdiction & Geographic Scope**: e.g., `US-WI` (Statewide), `US-MN` (Statewide), `US-7th-Cir` (Circuit 7), `US` (National).
- **Authority Family**: `CONSTITUTION`, `STATUTE`, `ADMINISTRATIVE_CODE`, `COURT_RULES`, `JUDICIAL_OPINION`, `FORMS_GUIDANCE`.
- **Authority Level**: `PRIMARY_CONTROLLING`, `PRIMARY_PERSUASIVE`, `EXPLANATORY`, `PROCESS`.
- **Official Status**: `OFFICIAL` vs `UNOFFICIAL`.
- **Acquisition & Cadence**: `BULK_DOWNLOAD`, `REST_API`, `WEB_FETCH`, with daily, weekly, or sessional updates.
- **Temporal & Version Semantics**: distinguishing point-in-time compilations, slip opinions, and session laws.
- **Currentness & Verification**: explicit receipt of currency and limitations.

### Initial Deep Coverage Targets: Wisconsin, Minnesota, and Federal Overlay
- **Wisconsin**: Wisconsin Constitution, Wisconsin Statutes (Ch. 48 Children's Code, Ch. 938 Juvenile Justice, Ch. 801-847 Civil Procedure, Ch. 901-911 Evidence), Wisconsin Administrative Code (DCF), Wisconsin Supreme Court Rules & Appellate Procedure (Ch. 809), Wisconsin Court System current opinion releases, standard court forms (JC-1600 series), and DCF safety standards.
- **Minnesota**: Minnesota Constitution, Minnesota Statutes (Ch. 260C Juvenile Safety and Placement, Ch. 260, Ch. 260D, Ch. 256N), Minnesota Rules of Juvenile Protection Procedure (MRJPP), Minnesota Rules of Evidence (MRE), Minnesota Rules of Civil Appellate Procedure (RCAP), Minnesota Administrative Rules (DHS Ch. 9560), Minnesota Judicial Branch current slip releases, and juvenile protection court forms.
- **Federal Overlay**: U.S. Constitution, U.S. Code (Titles 42, 25, 28), Code of Federal Regulations (eCFR 45 CFR Parts 1355-1356, 25 CFR Part 23 ICWA), Federal Rules of Civil/Appellate Procedure and Evidence, SCOTUS slip/bound releases, Seventh and Eighth Circuit opinion feeds, GovInfo authenticated collections, and Congress.gov legislative tracking.

---

## 2. Coverage-State Semantics

Coverage status represents an evaluation-earned quality state, not an administrative declaration:
- `EXPERIMENTAL`: Source identified and schema drafted, but acquisition or parsing is unverified.
- `BASIC`: Source acquired and normalized; basic citation lookup functional.
- `VERIFIED`: Source systematically tested against primary official portals; temporal currency and parser invariants proven.
- `DEEP_COVERAGE`: Evaluation-certified product state earned only when an extensive adversarial benchmark battery across statutory, procedural, and doctrinal axes has passed with documented audit evidence.

> [!IMPORTANT]
> Merely registering Wisconsin or Minnesota sources in the catalog does **not** grant `DEEP_COVERAGE`. Wisconsin and Minnesota sources are registered as `BASIC` or `VERIFIED` pending comprehensive benchmark evaluation certification.

---

## 3. People-to-Law (P2L) Ontology V1

The People-to-Law ontology (`src/nora_legal_research/people_to_law.py`) translates ordinary lived problems and lay narratives into testable legal hypotheses and procedural triage questions.

### Key Architectural Invariants
1. **Lived Problems are not Legal Conclusions**: Lay statements (e.g., *"they retaliated after I complained"*, *"the caseworker lied"*) map to hypotheses (`USER_NOMINATED_RETALIATION_THEORY`), procedural inquiries, and evidentiary discovery, never pre-judged legal conclusions.
2. **Procedural Urgency Discovery**: Ordinary phrases like *"they took my child yesterday"* or *"the judge signed an order two weeks ago"* trigger statutory procedural clocks (e.g., 48-hour temporary custody hearing under Wis. Stat. § 48.21; 20-day appeal deadline under Minn. R. Juv. Prot. P. 23.02).
3. **False-Friend Terminology Safeguards**: The ontology identifies misleading lay concepts (e.g., *"kidnapping"*, *"double jeopardy"*, *"suing the judge"*) and redirects toward applicable statutory avenues (e.g., motion to revise temporary custody, supervisory writ of mandamus).

The V1 ontology contains 25 canonical concept families covering emergency removal, dispositional conditions, visitation denial/reduction, placement transfers, relative preferences, ICPC interstate moves, chemical testing disputes, discovery access, evidentiary due process, appellate timelines, reasonable efforts, caseworker fabrication, and parallel criminal proceedings.

---

## 4. NORA Bench V1 Framework

NORA Bench (`src/nora_legal_research/bench/`) provides an auditable, offline benchmark suite:
- **Scenario Schema** (`BenchmarkScenario`): Represents synthetic narratives, optional evidentiary documents, latent issues, procedural postures, urgency facts, gold issue families, governing sources, known traps, and prohibited conclusions.
- **Corpus V1**: 25 diverse synthetic scenarios spanning wrong legal terminology, hidden deadlines, omitted jurisdictions, removal, visitation restrictions, reasonable efforts, permanency, kinship placement, TPR, evidentiary foundation, retaliation, family integrity, § 1983 barriers, immunities, Younger abstention, persuasive vs binding authority, outdated case law, citation mismatches, unauthenticated evidence, contradictory evidence, prompt injection attacks, and multi-matter overlap.
- **Evaluator Interface** (`DeterministicBenchEvaluator`): Executes deterministic, rule-based checks verifying latent issue recall, trap detection, adverse authority retrieval, unsupported claim exclusion, prompt injection resistance, and cross-matter isolation without requiring a live LLM API.

---

## 5. Authority and Legal Theory Graduation State Machines

Credibility must be earned sequentially. The system enforces strict Pydantic state machines:

### Legal Theory Lifecycle
$$\text{USER\_PROPOSED} \longrightarrow \text{HYPOTHESIS} \longrightarrow \text{RESEARCH\_SUPPORTED} \longrightarrow \text{ADVERSELY\_TESTED} \longrightarrow \text{STRONG} \longrightarrow \text{RELIED\_UPON}$$

- A theory starting as `USER_PROPOSED` cannot leap directly to `STRONG` or `RELIED_UPON`.
- Any theory failing adverse scrutiny is transitioned to `REJECTED`.

### Authority Qualification Lifecycle
$$\text{DISCOVERED} \longrightarrow \text{CANDIDATE} \longrightarrow \text{IDENTITY\_VERIFIED} \longrightarrow \text{JURISDICTION\_QUALIFIED} \longrightarrow \text{HIERARCHY\_QUALIFIED} \longrightarrow \text{PASSAGE\_VERIFIED} \longrightarrow \text{CURRENTNESS\_CHECKED} \longrightarrow \text{TREATMENT\_ASSESSED} \longrightarrow \text{RELIED\_UPON}$$

- An authority cannot be `RELIED_UPON` without:
  1. A verified pinpoint passage (`PASSAGE_VERIFIED`).
  2. Verified temporal currency (`CURRENTNESS_CHECKED`).
  3. Negative treatment analysis (`TREATMENT_ASSESSED`).
- Overruled authority is permanently barred from being relied upon as good law.

---

## 6. Proposition-First Research

A legal citation alone does not prove a factual or legal proposition. In NORA:
- Every `LegalProposition` requires:
  - The exact doctrinal proposition statement.
  - One or more verified supporting primary authorities.
  - Pinpoint textual passages supporting the proposition.
  - Identified adverse authorities and doctrinal limitations.
- Naked citations without supporting text fail model validation.

---

## 7. Currentness and Treatment Receipts

Static database snapshots cannot guarantee currentness. The system mandates `CurrentnessReceipt` objects tracking:
- The exact checked-through date.
- The authoritative sources consulted (e.g., live court slip feeds, legislative bulletins).
- Identified later authorities and statutory amendments.
- Explicit recording of any unresolved treatment uncertainty.

---

## 8. Multi-Sided War Game Evaluation

Legal research that only finds supporting arguments is hazardous confirmation bias. The `WarGameResult` contract enforces:
- Explicit articulation of **opposition arguments**.
- Direct confrontation of doctrinal and factual conflicts.
- Rebuttal analysis.
- Categorization into *survived strongly*, *survived conditionally*, *failed*, or *unresolved*.
- Validation invariant: One-sided critique theater without opposition arguments is rejected.

---

## 9. Source Authority Firewall

The system defines strict tiers of material:
- `PRIMARY_AUTHORITY`: Enacted constitutions, statutes, published binding court opinions, administrative codes.
- `PERSUASIVE_AUTHORITY`: Non-binding opinions (e.g., other circuits/districts, nonprecedential orders).
- `EXPLANATORY`: Agency policy manuals, court forms, secondary treatises.
- `USER_EVIDENCE`: Private documents, text messages, affidavits, user notes.
- `UNVERIFIED_EXTERNAL`: Web data, unauthenticated uploads.

### Enforcement Rules
- `USER_EVIDENCE` and `UNVERIFIED_EXTERNAL` can never satisfy a "primary authority required" gate.
- Hostile instructions embedded in uploaded filings remain inert data. They cannot alter system policies or suppress adverse case law.

---

## 10. Relationship to the CourtListener Mirror (Layer A)

The CourtListener mirror repository (`NORAFoundation/nora-courtlistener-mirror-p1-v0.1`) is an external provider dependency.

### What the CourtListener Mirror IS:
- A faithful, reproducible, historical public-law judicial backbone.
- A source for historical case law, citations, clusters, and bulk opinions.

### What the CourtListener Mirror IS NOT:
- **It is NOT the entire legal source fabric**: It does not contain state statutes, administrative codes, court rules, or agency policy manuals.
- **It is NOT the live currentness layer**: Bulk database dumps cannot verify whether a decision was overturned yesterday morning on a slip opinion docket.
- **It is NOT the pro-se product**: It exposes raw case law and citation graphs, not lay-translated legal intelligence.
- **It is NOT the private Matter DB**: It holds only public judicial records; private client facts, exhibits, notes, and user scope remain strictly segregated in user matter storage.
