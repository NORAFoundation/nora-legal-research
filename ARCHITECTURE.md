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

## Source, retrieval, and intelligence layers

The CourtListener source mirror remains source-faithful and reproducible. It is
not rewritten for lay terminology. Derived full-text, citation, hierarchy,
segmentation, concept, and semantic indexes are disposable Layer B structures
linked to source IDs, snapshots, and build versions. `nora-legal-research`
owns Layer C research intelligence: narrative intake, intent, issue
hypotheses, query families, qualification, and provider-neutral snapshots.

The lay compiler uses the same source corpus and research standard for every
user. Lay-language mappings are derived, versioned, jurisdiction-sensitive
navigation aids; they are never authority meaning or legal conclusions.

## Extension points

Court adapters, citation parsers, treatment providers, jurisdiction packs, local corpora, MCP/API adapters.

## Compatibility

Public contracts should be versioned and provider-neutral where practical.

## Architecture decisions

Record consequential changes under `docs/decisions/`.
