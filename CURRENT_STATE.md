# Current State — nora-legal-research

**Status:** OSS EXTRACTION / RECONCILIATION IN PROGRESS
**Version:** 0.0.1

## Implemented Reference Slice

The minimum reference vertical slice is complete and verified:
`citation parsing -> CourtListener normalization -> quote verification -> ResearchSnapshot generation -> treatment auditing`

- `src/nora_legal_research/contracts.py`: Dataclasses for `Jurisdiction`, `AuthorityType`, `PrecedentialStatus`, `Citation`, `QuoteSpan`, and `ResearchSnapshot`.
- `src/nora_legal_research/citation_guard.py`: `CitationGuard` parsing volume, reporter, page, and year citations.
- `src/nora_legal_research/quote_verifier.py`: `QuoteVerifier` asserting pinpoint exact quote matches against authority opinion text.
- `src/nora_legal_research/courtlistener.py`: `CourtListenerNormalizer` mapping raw API payloads into canonical authority citations.
- `src/nora_legal_research/treatment.py`: `TreatmentAnalyzer` auditing adverse authority and generating overruled status warnings.

## Implemented Foundations (V1 Foundation Pass)

1. **JurisdictionSourceRegistry (`src/nora_legal_research/jurisdiction_registry.py`, `jurisdiction_data.py`)**:
   - Comprehensive source catalog covering Wisconsin (9 sources), Minnesota (10 sources), and Federal Overlay (10 sources).
   - Strict separation of primary controlling authority vs explanatory/process materials.
   - CourtListener mirror explicitly modeled as an unofficial historical snapshot, distinct from live official judicial slip releases.
   - Earned coverage semantics: prevents uncertified `DEEP_COVERAGE` claims.

2. **People-to-Law Ontology V1 (`src/nora_legal_research/people_to_law.py`)**:
   - 25 canonical lived-problem concept families covering juvenile protection, CHIPS, visitation, ICPC, drug screening disputes, reasonable efforts, TPR, appeals, and civil-rights overlays.
   - Invariant: Maps lay complaints to research hypotheses (`USER_NOMINATED_*`), not pre-judged legal conclusions.
   - Flags false-friend terminology, urgency cues, and disambiguation requirements.

3. **NORA Bench V1 Framework & Evaluation Doctrine (`src/nora_legal_research/bench/`)**:
   - Deterministic, offline benchmark scenario and metric contracts with explicit `BenchmarkCorpusRole` (`DEVELOPMENT`, `VALIDATION`, `HOLDOUT`).
   - 25 synthetic adversarial scenarios designated as `DEVELOPMENT / ADVERSARIAL DESIGN SET`.
   - Evaluation doctrine: `BUILD WITH dev fixtures` -> `TUNE WITH dev evidence` -> `VALIDATE WITH separately curated cases` -> `RELEASE-GATE WITH untouched holdout`. Zero benchmark leakage permitted.
   - Deterministic rule-based evaluator (`DeterministicBenchEvaluator`) validating metrics without requiring live LLM calls.

4. **Canonical Research Contracts & State Machines (`src/nora_legal_research/canonical_research.py`)**:
   - `ProceduralAlert`: Unverified vs verified deadline alerts with urgency and jurisdiction bindings.
   - `LegalTheory`: Strict state machine preventing user-proposed theories from leaping directly to strong or relied-upon without research and adverse testing.
   - `AuthorityQualificationLifecycle`: Step-by-step qualification from discovery through pinpoint passage verification and currentness before reliance.
   - `LegalProposition`: Enforces that citations require supporting text passages to prove propositions.
   - `CurrentnessReceipt`: Explicit audit trail of checked sources and dates.
   - `ResearchCoverage`: Dimensional research coverage across 11 axes; never reduced to a win probability.
   - `WarGameResult`: Multi-sided adversarial evaluation enforcing opposition analysis.
   - `ResearchPackage`: Portable, auditable research artifact.
   - `MatterScope`: Enforces strict separation between public law data and private user matters.

5. **Narrative Compiler Integration (`src/nora_legal_research/narrative_compiler.py`)**:
   - Multi-channel issue discovery: General lay mappings + People-to-Law candidate hypotheses + user interpretations + procedural issues.
   - Epistemic discipline: Lexical/alias hits produce candidate hypotheses (`ISSUE_HYPOTHESIS`, confidence 0.5) without inflated confidence.
   - Retaliation allegations strictly preserved as `USER_NOMINATED_RETALIATION_THEORY`.
   - Bounded `JurisdictionSourceRegistry` candidate retrieval: Separates primary controlling authority from explanatory/forms guidance; conditions federal overlay on federal claims/questions and bounds appellate sources to the governing circuit (7th Cir for WI, 8th Cir for MN).

## Contract Targets — Not Yet Implemented

- Centralized live external citator connector (Shepard's/KeyCite equivalent)
- Full automated bulk statute XML ingestion pipeline
- Production-scale Westlaw/Lexis/PACER parser adapters
- Separate, untouched release-gating holdout benchmark corpus

## Verified

- `make test` / `pytest`: **102 passed in 0.62s**.
- `make validate`: Scaffold passed, all 30 JSON schemas generated and synchronized (`scripts/generate_schemas.py --check`), Python bytecode compiled cleanly.
- End-to-end citation parsing, quote verification, CourtListener normalization, treatment trace, jurisdiction validation, benchmark evaluation, P2L negative controls, and compiler state machine transitions verified.
