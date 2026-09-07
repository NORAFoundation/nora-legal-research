# Canonical provider integration work packet

Objective: make the provider-neutral CourtListener mirror boundary safe to
consume and preserve ResearchSnapshot semantics through public-law adapters.

Scope: this repository's contracts, transports, normalization, schemas,
fixtures, tests, and the named public-demo/sidecar compatibility adapters.
The CourtListener mirror repository and litigation portfolio audit are out of
scope and are read-only dependencies.

Acceptance: strict versioned request/result/response/snapshot validation;
explicit request allowlist; typed provider failures; separate provider and
access-mode identities; stable query-plan hash; conservative authority
identity/opinion handling; explicit adverse-authority preservation; empty vs
partial vs failure separation; quarantine/fixed-event/human-promotion
compatibility; focused commit and normal push.
