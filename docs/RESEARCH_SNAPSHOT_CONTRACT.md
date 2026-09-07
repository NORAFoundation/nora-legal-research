# ResearchSnapshot contract

`ResearchSnapshot` is the provider-neutral boundary for NORA legal research. It records what a provider returned and what remains unverified; it does not assert that an authority is good law merely because it was retrieved.

The contract separates:

- discovery and retrieval (`ProviderSearchResult`, `Provenance`);
- authority identity and public citation (`AuthorityRecord`);
- quote verification (`VerificationStatus`);
- precedential weight (`PrecedentialStatus`);
- treatment/currentness (`TreatmentStatus`, `CurrentnessAssessment`);
- application and downstream legal reasoning (owned by the caller).

Retrieval is not a legal conclusion. A provider-normalized snapshot defaults
to `currentness=unknown`, `treatment_status=unknown`,
`quote_verification=not_available`, `confidence=UNASSESSED`, and
`precedential_status=unknown`. Explicit adverse evidence is preserved, but a
non-empty provider relationship is not by itself adverse: only the contract's
explicit `ADVERSE`, `LIMITING`, `DISTINGUISHING`, or `NEGATIVE_TREATMENT`
relationship/status values qualify.

`ResearchSnapshot.snapshot_id` is the consumer/correlation identity. The
mirror's identity is kept separately in `ResearchSnapshot.provider.snapshot_id`
and provenance. A consumer snapshot cannot reuse the provider snapshot ID.
`provider.access_mode` separately records `FIXTURE`, `MIRROR_API`, or `MCP`.

The `reproducibility.query_plan_hash` is SHA-256 over the timestamp-free
substantive query plan: query variants, jurisdiction, court level, date
constraints, result limit, and requested capabilities. Mirror provenance may
also attest that same hash; timestamps never enter the stable hash.

`AuthorityProvider` is intentionally provider-neutral. CourtListener is implemented as an adapter boundary only. Acquisition, database serving, ranking, treatment analysis, and currentness remain outside the adapter.

The compatibility result emitted by the public-law sidecar carries the contract marker `nora.legal-research/ResearchSnapshot/1.0` and is converted into this model by the next integration slice.

Lay-narrative intake, research intent, issue hypotheses, query plans, quality
assessments, and guided explanations are separate derived artifacts. They
compile messy user stories into bounded public requests but do not alter this
snapshot contract or replace source-faithful authority records.
