# ResearchSnapshot contract

`ResearchSnapshot` is the provider-neutral boundary for NORA legal research. It records what a provider returned and what remains unverified; it does not assert that an authority is good law merely because it was retrieved.

The contract separates:

- discovery and retrieval (`ProviderSearchResult`, `Provenance`);
- authority identity and public citation (`AuthorityRecord`);
- quote verification (`VerificationStatus`);
- precedential weight (`PrecedentialStatus`);
- treatment/currentness (`TreatmentStatus`, `CurrentnessAssessment`);
- application and downstream legal reasoning (owned by the caller).

`AuthorityProvider` is intentionally provider-neutral. CourtListener is implemented as an adapter boundary only. Acquisition, database serving, ranking, treatment analysis, and currentness remain outside the adapter.

The compatibility result emitted by the public-law sidecar carries the contract marker `nora.legal-research/ResearchSnapshot/1.0` and is converted into this model by the next integration slice.
