# ADR-0001: Unified Legal Research Authority Model

- **Status:** Accepted
- **Date:** 2026-08-19
- **Deciders:** NORA Foundation Engineering Team

## Context

Previous legal research implementations were split across `lawllama-assurance` and `nora-legal-research-scaffold-v0-3-0`. We unify them into one high-assurance engine (`nora-legal-research`).

## Decision

We adopt unified contracts for:
1. `Jurisdiction` — Explicit geographic/forum code and authority level.
2. `AuthorityType` & `PrecedentialStatus` — Classification of binding vs persuasive vs overruled authority.
3. `Citation` & `QuoteSpan` — Verification contracts asserting exact pinpoint quotes.
4. `ResearchSnapshot` — Reproducible audit record carrying citations, verified quote spans, and treatment warnings.

## Consequences

- Fail-closed citation validation: unverified quotes or questioned precedent generate explicit status warnings.
- Unifies CourtListener bulk ingest, FTS baselines, and assurance verification into one repository.
