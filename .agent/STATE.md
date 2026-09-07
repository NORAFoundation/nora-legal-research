# Implementation state

## Current status

- Canonical provider contract implementation is complete for the independent
  fixture lane.
- Canonical tests: 71 passed, including lay-narrative and research-quality qualification vectors.
- Public-law sidecar tests: 31 passed.
- Public-demo tests: 42 passed in the current checkout.
- Generated schema check and `git diff --check`: passed.
- `ruff` is unavailable in the environment and was not installed; it is an
  optional development extra, not a required release gate in `pyproject.toml`.
- Mirror `origin/main` at `ca9201f` reports
  `COURTLISTENER_MIRROR_PROVIDER=BLOCKED_BOUNDED_LIVE_PROOF`; no live E2E was
  attempted against its import/database infrastructure.
- Lay narrative compilation is a separate derived-artifact lane: intake,
  intent, issue hypotheses, query families, provider abstraction, and guided
  explanation are implemented and versioned independently of ResearchSnapshot
  v1.
- Narrative fixture gates pass for extraction, jurisdiction behavior, issue
  hypotheses, query compilation, privacy abstraction, multi-pass planning, and
  explanation. Live retrieval-recall qualification remains blocked by the
  mirror provider gate.
- Research quality is a separate derived-artifact lane: fact/source epistemology,
  multidimensional completeness, authority qualification, professional record,
  and non-lawyer guided explanation are versioned independently of
  ResearchSnapshot v1. Six generated quality schemas are current.
- Public consumers bundle the canonical generated ResearchSnapshot schema;
  `scripts/sync_public_snapshot_schema.py --check` passes for both scoped
  consumers. Sidecar source changes are reflected in image `0.1.4` at digest
  `sha256:875757c63d604cb471d0dd86a58f2b66aa080335904f3b2d62452f05a9a35c65`.

## Evidence boundaries

The sidecar remains the network/quarantine boundary. Canonical normalization
owns ResearchSnapshot construction and validation. Public rendering receives
only fixed aggregate events; ledger output remains quarantined and human
gated. No private matter data or credentials were added.
