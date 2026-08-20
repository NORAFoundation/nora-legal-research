# Architecture

## Invariants

1. The public repository contains reusable technology, not private Matter data.
2. Every important output has an inspectable basis appropriate to this project's domain.
3. Authorization is evaluated before data is exposed to retrieval/tool/model paths where applicable.
4. Model output is a transformation, not a source of truth.
5. Unknown and disputed states are valid outputs.
6. Tests/evals use synthetic or redistributable fixtures.
7. Migration provenance is explicit.

## Target-specific architecture

Authority ingestion/search:
CourtListener/local corpus → authority normalization → jurisdiction/hierarchy →
search/citation graph → citation validation → quote-span validation →
currentness/treatment → adverse-authority search → ResearchSnapshot → human review.

## Extension points

Court adapters, citation parsers, treatment providers, jurisdiction packs, local corpora, MCP/API adapters.

## Compatibility

Public contracts should be versioned and provider-neutral where practical.

## Architecture decisions

Record consequential changes under `docs/decisions/`.
