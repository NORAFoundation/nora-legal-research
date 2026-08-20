# Security Policy

Do not file public issues containing secrets, private evidence, personal data, or vulnerability exploit details.

Report security issues privately to the NORA Foundation security contact configured by the organization.

## Public repository security invariants

- no secret values in Git;
- no real private Matter data;
- no cross-tenant/cross-scope access in tests or examples;
- synthetic fixtures only;
- dependency and static analysis enabled;
- security-sensitive changes require explicit tests.
