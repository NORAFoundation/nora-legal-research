# Implementation state

## Current status

- Canonical provider contract implementation is complete for the independent
  fixture lane.
- Canonical tests: 61 passed, including lay-narrative qualification vectors.
- Public-law sidecar tests: 31 passed.
- Public-demo tests: 42 passed.
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

## Evidence boundaries

The sidecar remains the network/quarantine boundary. Canonical normalization
owns ResearchSnapshot construction and validation. Public rendering receives
only fixed aggregate events; ledger output remains quarantined and human
gated. No private matter data or credentials were added.
