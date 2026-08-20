# Publication Review — nora-legal-research

**Status: BLOCKED**

This review is fail-closed. A scaffold cannot pass it merely because required files exist.

## Result

- G0 identity, G1 technical validation (doctor/validate/test 7 passed, demo PASS), G2 docs,
  G3/G4 privacy/secret scans, G6 contributor readiness: PASS with evidence (2026-08-20).
- G5 licensing/provenance: LICENSE + SOURCE_PROVENANCE.yaml present, but formal external
  rights review still recorded as `pending_formal_rights_review`.
- G7 remote CI/security: ci workflow PASS on pushed main; codeql SARIF upload BLOCKED
  ("Advanced Security must be enabled for this repository to use code scanning" — GitHub
  Advanced Security not available for private repos on GitHub Free); branch protection/
  rulesets API 403 on GitHub Free private org. Features unlock at public visibility switch.

Full evidence and run IDs in PUBLICATION_EVIDENCE.yaml (authoritative).

**Not publishable until: (1) formal rights review completes, (2) codeql/security features
are enabled or confirmed available post-visibility switch, and (3) explicit visibility
decision is made.**