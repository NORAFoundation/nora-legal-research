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
   - Comprehensive source catalog covering Wisconsin (8 sources), Minnesota (9 sources), and Federal Overlay (10 sources).
   - Strict separation of primary controlling authority vs explanatory/process materials.
   - CourtListener mirror explicitly modeled as an unofficial historical snapshot, distinct from live official judicial slip releases.
   - Earned coverage semantics: prevents uncertified `DEEP_COVERAGE` claims.

2. **People-to-Law Ontology V1 (`src/nora_legal_research/people_to_law.py`)**:
   - 25 canonical lived-problem concept families covering juvenile protection, CHIPS, visitation, ICPC, drug screening disputes, reasonable efforts, TPR, appeals, and civil-rights overlays.
   - Invariant: Maps lay complaints to research hypotheses (`USER_NOMINATED_*`), not pre-judged legal conclusions.
   - Flags false-friend terminology, urgency cues, and disambiguation requirements.

3. **NORA Bench V1 Framework & Adversarial Corpus (`src/nora_legal_research/bench/`)**:
   - Deterministic, offline benchmark scenario and metric contracts.
   - 25 synthetic adversarial scenarios testing wrong terminology, hidden deadlines, omitted jurisdictions, prompt injections, contradictory evidence, and multi-matter overlap.
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

## Contract Targets — Not Yet Implemented

- Centralized live external citator connector (Shepard's/KeyCite equivalent)
- Full automated bulk statute XML ingestion pipeline
- Production-scale Westlaw/Lexis/PACER parser adapters

## Verified

- `make test` / `pytest`: **94 passed in 0.44s**.
- `make validate`: Scaffold passed, all 30 JSON schemas generated and validated (`scripts/generate_schemas.py --check`), Python bytecode compiled cleanly.
- End-to-end citation parsing, quote verification, CourtListener normalization, treatment trace, jurisdiction validation, benchmark evaluation, and state machine transitions verified.
