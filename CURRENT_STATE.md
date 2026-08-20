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

## Verified

- `make test` / `pytest`: **7 passed in 0.11s**.
- Vertical-slice test path: `tests/test_vertical_slice.py`.
- End-to-end citation parsing, quote verification, CourtListener normalization, and treatment trace verified.

## Not Yet Established

- canonical feature parity (public candidate contains 163 LOC vs canonical `legal-core` 5,556 LOC);
- public extraction completeness;
- production deployment status;
- reconciliation of full entity resolution, relational sync, and bulk CourtListener importers.
