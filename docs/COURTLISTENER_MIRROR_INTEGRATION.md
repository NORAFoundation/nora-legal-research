# CourtListener mirror integration handshake

## Ownership

- Consumer: `nora-legal-research`
- Provider: `NORAFoundation/nora-courtlistener-mirror-p1-v0.1`
- Provider responsibilities: acquisition, storage, query execution, citation graph, serving, and raw-source provenance.
- Consumer responsibilities: provider-neutral validation, normalization, treatment/currentness boundaries, and `ResearchSnapshot` semantics.

The mirror remains a source-faithful Layer A canon. Lay-language expansion,
semantic retrieval, aliases, segmentation, and ranking are disposable,
versioned Layer B structures derived from source records; narrative-to-intent
and qualification remain Layer C responsibilities of this repository. The
mirror must not mutate authority meaning to accommodate pro-se searches.

## Service contract

- Request schema: `schemas/provider-search-request-v1.schema.json`
- Canonical request schema alias: `schemas/authority-research-request-v1.schema.json`
- Provider result schema: `schemas/provider-search-result-v1.schema.json`
- Response schema: `schemas/provider-search-response-v1.schema.json`
- Endpoint shape: versioned provider envelope. The current mirror checkout publishes a read-only MCP/stdio service; an approved broker or HTTP facade must return this envelope before consumption. The consumer does not parse mirror-native MCP payloads.
- Contract version: `1`
- Required request fields: research ID, jurisdiction, court scope, doctrinal issue, target proposition, query variants, bounded date range/limit, and requested capabilities.
- Forbidden request content: party names, private facts, case-derived chronology, local paths, source text, or private identifiers.

## Provider semantics

The provider returns bounded authority candidates and capability metadata. It must not be required to assert good law, currentness, treatment, or legal effect. Empty success, partial success, authentication failure, rate limiting, contract mismatch, and unavailable service remain distinct outcomes.

Read-only inspection of mirror `origin/main` at `ca9201f` reports `COURTLISTENER_MIRROR_PROVIDER=BLOCKED_BOUNDED_LIVE_PROOF`. Its MCP/stdio provider mode emits the versioned envelope, but the mirror is not yet requalified for bounded live serving. `McpMirrorTransport` is prepared for the qualified broker boundary; live provider integration remains blocked pending the mirror handoff and qualification evidence.

Every successful response identifies `provider_name`, `research_id`, `snapshot_id`, `snapshot_date`, capabilities, authorities, partial/truncated state, limitations, and provenance. Provenance may additionally identify service version, mirror Git SHA, query-plan hash, and retrieval time. Missing optional provenance reduces reproducibility; it must not be fabricated.

## Consumer behavior

`FixtureTransport` proves the contract offline. `HttpMirrorTransport` is HTTPS-only, bounded, redirect-rejecting, size-limited, and typed-error based. `McpMirrorTransport` accepts only the same versioned envelope from an approved MCP broker. `CourtListenerMirrorProvider` is a thin facade over either transport. Database details, ranking, treatment, and currentness remain outside the provider adapter.

## Security and legal boundaries

The provider request is serialized by an explicit allowlist. Provider results are normalized conservatively: treatment/currentness remain unknown unless separately qualified, and quote verification remains unavailable unless exact opinion text is independently checked. The public-law sidecar continues to own network compartmentalization and quarantine crossing.

## Authentication placeholder

The client supports an optional bearer token from runtime configuration; no credential is committed, invented, or required for fixture qualification. The mirror agent defines the eventual authentication mechanism.
