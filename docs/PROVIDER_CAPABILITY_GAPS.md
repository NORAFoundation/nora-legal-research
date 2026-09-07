# Provider Capability Gaps

The canonical consumer is prepared for iterative bounded retrieval, but live
qualification depends on the separately owned CourtListener mirror service.
The latest read-only mirror status is `BLOCKED_BOUNDED_LIVE_PROOF`; no database
or importer change is made here.

## Required provider capabilities

- bounded lexical/metadata search;
- opinion and cluster retrieval with stable IDs;
- court and hierarchy metadata;
- outbound and inbound citation graph traversal;
- snapshot identity/date and mirror build provenance;
- explicit partial/truncated state and limitations;
- bounded repeated requests for discovery and qualification passes.

## Current gaps

`COURTLISTENER_MIRROR_PROVIDER` is not integration-ready until bounded live
serving is requalified.  A published MCP/stdio envelope is useful fixture
evidence but does not establish serving, currentness, quote verification, or
database reconciliation.  REST sidecar authentication and qualified live
network evidence also remain separate gates.

The canonical compiler therefore emits abstract requests and preserves all
unknowns.  It does not compensate for missing provider capabilities by
inventing authority status or silently broadening jurisdiction.
