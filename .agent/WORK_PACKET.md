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

Research quality extension: keep the source-faithful CourtListener mirror
unchanged while adding separate versioned NarrativeResearchIntake,
ResearchIntent, IssueHypothesis, ResearchPlan, and GuidedResearchExplanation
artifacts. Preserve reported facts and uncertainty, resolve jurisdiction
explicitly, compile multiple discovery/qualification query classes, and ensure
only abstract allowlisted requests reach public providers. Qualify with messy
synthetic pro-se narratives; do not count fixture evidence as live mirror
qualification.
