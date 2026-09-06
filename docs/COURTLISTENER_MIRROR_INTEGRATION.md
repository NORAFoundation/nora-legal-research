# CourtListener mirror integration handshake

## Ownership

- Consumer: `nora-legal-research`
- Provider: `NORAFoundation/nora-courtlistener-mirror-p1-v0.1`
- Provider responsibilities: acquisition, storage, query execution, citation graph, serving, and raw-source provenance.
- Consumer responsibilities: provider-neutral validation, normalization, treatment/currentness boundaries, and `ResearchSnapshot` semantics.

## Service contract

- Request schema: `schemas/provider-search-request-v1.schema.json`
- Response schema: `schemas/provider-search-response-v1.schema.json`
- Endpoint shape: versioned provider envelope. The current mirror checkout publishes a read-only MCP/stdio service; an approved broker or HTTP facade must return this envelope before consumption. The consumer does not parse mirror-native MCP payloads.
- Contract version: `1`
- Required request fields: research ID, jurisdiction, court scope, doctrinal issue, target proposition, query variants, bounded date range/limit.
- Forbidden request content: party names, private facts, case-derived chronology, local paths, source text, or private identifiers.

## Provider semantics

The provider returns bounded authority candidates and capability metadata. It must not be required to assert good law, currentness, treatment, or legal effect. Empty success, partial success, authentication failure, rate limiting, contract mismatch, and unavailable service remain distinct outcomes.

Read-only inspection of mirror commit `057ded9` found an MCP/stdio tool surface whose native search result is not yet this versioned envelope. `McpMirrorTransport` is prepared for a qualified broker that emits the envelope; live provider integration remains blocked pending that handshake.

Every successful response should identify `provider_name`, `research_id`, and—when available—the underlying mirror `snapshot_id`/`snapshot_date` and service version. Missing snapshot identity limits reproducibility; it must not be fabricated.

## Consumer behavior

`FixtureTransport` proves the contract offline. `HttpMirrorTransport` is HTTPS-only, bounded, redirect-rejecting, size-limited, and typed-error based. `McpMirrorTransport` accepts only the same versioned envelope from an approved MCP broker. `CourtListenerMirrorProvider` is a thin facade over either transport. Database details, ranking, treatment, and currentness remain outside the provider adapter.

## Security and legal boundaries

The provider request is serialized by an explicit allowlist. Provider results are normalized conservatively: treatment/currentness remain unknown unless separately qualified, and quote verification remains unavailable unless exact opinion text is independently checked. The public-law sidecar continues to own network compartmentalization and quarantine crossing.

## Authentication placeholder

The client supports an optional bearer token from runtime configuration; no credential is committed, invented, or required for fixture qualification. The mirror agent defines the eventual authentication mechanism.
