# Rights / Provenance Review Register — nora-legal-research

**Gate:** G5 (licensing/provenance) — **STATUS: BLOCKED**

Formal external rights/provenance review is outstanding for every entry below.
This register is the durable record of each unresolved item. It is **not** a
resolution of any legal/rights question; no item below may be treated as cleared
until a named reviewer records a decision.

| ID | Source repo / commit / lineage | Source path(s) | Why review required | License / rights question | Evidence already collected | Required reviewer / decision | Remediation if rejected | Publication impact |
|----|-------------------------------|----------------|---------------------|---------------------------|---------------------------|------------------------------|-------------------------|--------------------|
| PROV-LEGAL-001 | `NORAFoundation/lawllama-assurance` @ `92122d6e` (internal NORA-authored, MIT) | `src/assurance/citation_guard.py`, `src/assurance/quote_verifier.py` → `src/nora_legal_research/citation_guard.py`, `src/nora_legal_research/quote_verifier.py` | MIT source imported into Apache-2.0 target; relicensing/attribution path must be explicitly authorized. | Is the MIT→Apache-2.0 relicensing authorized? Is MIT copyright attribution preserved correctly for the combined target? | SOURCE_PROVENANCE.yaml entry; MIT copyright attribution preserved (per changes note); secret/privacy/license scan pass (agent-level); `authorization_reference: INTERNAL_CLEANROOM_TRANSPLANT_PENDING_EXPLICIT_SIGN_OFF` | Named human reviewer; explicit sign-off on relicensing + attribution. | Restore per-source MIT licensing/notices, or re-derive clean-room content; re-run gates. | Blocks publication of nora-legal-research (hard blocker per G5). |
| PROV-LEGAL-002 | `NORAFoundation/nora-legal-research-scaffold-v0-3-0` @ `4659b902` (internal scaffold) | `ingest/courtlistener_bulk.py` → `src/nora_legal_research/courtlistener.py` | Original license recorded as Missing/Unknown; scaffold rewritten clean-room for OSS under Apache-2.0. | Is the clean-room rewrite sufficiently independent of the unknown-licensed scaffold? Any CourtListener/API-derived code or data rights questions? | SOURCE_PROVENANCE.yaml entry (treatment: CONCEPT_REWRITE); secret/privacy/license scan pass (agent-level); `authorization_reference: INTERNAL_CLEANROOM_TRANSPLANT_PENDING_EXPLICIT_SIGN_OFF` | Named human reviewer; clean-room independence + CourtListener API terms compliance decision. | Re-derive or replace any material found dependent on the scaffold; re-run gates. | Blocks publication of nora-legal-research (hard blocker per G5). |

**Rights review pending items (inherited from evidence file):**
- CourtListener / MCP-derived material (PROV-LEGAL-002 above: clean-room CourtListener bulk
  normalization; confirm API terms-of-service and any MCP-derived code lineage).

**Status line (required closeout language):**
Technical publication preparation complete. Formal rights/provenance review remains
outstanding. Repository remains private. No visibility authorization has been granted.