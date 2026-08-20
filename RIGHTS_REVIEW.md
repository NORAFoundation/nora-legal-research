# Rights / Provenance Review Register — nora-legal-research

**Gate:** G5 (licensing/provenance) — **STATUS: BLOCKED**

**Review executed 2026-08-20.** Every lineage entry below received an evidence-based disposition
(verified via GitHub API commit/license checks, candidate git-history searches, and harvest-commit
file inspection). BLOCKED entries may not be treated as cleared until a named human reviewer
records a decision. This register is the durable record.

## Verification record (2026-08-20)

- Source commits checked with `gh api repos/{owner}/{repo}/commits/{sha}`.
- Source licenses checked with `gh api repos/{owner}/{repo}/license` and by reading the LICENSE
  file at the recorded commit.
- Contamination search (`git log --all -S`) across this repo for: RAGEmbed, Meridian-Canon,
  NECCL, nora-canon, blakeox, legal-mcp, LawLLama, CC BY-NC, courtlistener-mcp, mcro-mcp,
  agent-canon → **0 hits**.
- Harvested files inspected at harvest commits (`git show`): small derived implementations
  importing `nora_legal_research` contracts, docstring-attributed to sources; not verbatim copies.
  No vendor directories.
- Evidence artifacts: `/tmp/g5deep.log`, `/tmp/g5verify.log`, `/tmp/g5ev_nora-legal-research.log`.

## Dispositions

| ID | Source repo / commit | Source → target | License verification (2026-08-20) | Disposition | Required reviewer / decision |
|----|----------------------|-----------------|-----------------------------------|-------------|------------------------------|
| PROV-LEGAL-001 | `NORAFoundation/lawllama-assurance` @ `92122d6e` | `src/assurance/citation_guard.py`, `src/assurance/quote_verifier.py` → `src/nora_legal_research/citation_guard.py`, `src/nora_legal_research/quote_verifier.py` | Commit **EXISTS**. LICENSE = **MIT** ("MIT License / Copyright (c) 2026 Product Pat"). | **PASS WITH ATTRIBUTION ACTION** — MIT permits redistribution with attribution; attribution action **completed** (MIT notice added to THIRD_PARTY_NOTICES.md 2026-08-20) | None blocking; human may confirm notice placement |
| PROV-LEGAL-002 | `NORAFoundation/nora-legal-research-scaffold-v0-3-0` @ `4659b902` | `ingest/courtlistener_bulk.py` → `src/nora_legal_research/courtlistener.py` | Commit **EXISTS**. Source repo has **no LICENSE file**. | **BLOCKED — RIGHTS UNCLEAR** (clean-room rewrite must be independently verified; CourtListener API terms-of-service compliance decision) | Named human reviewer: clean-room independence + API-terms decision |

## Rights review pending items (2026-08-20)

- Scaffold-derived CourtListener normalization (PROV-LEGAL-002): source repo carries no license;
  clean-room independence and CourtListener API terms remain unverified.
- External-lineage note: the canon map flagged `NORA-BITSY/courtlistener-mcp2` as referencing an
  external `blakeox/legal-mcp` lineage. README grep found **no such reference**, and contamination
  searches in this repo's history found **0 hits**. `courtlistener-mcp2` is not a recorded source
  of any candidate material; the canon-map flag remains unconfirmed (INFERRED — NEEDS CONFIRMATION)
  but does not block this candidate.

**Status line (required closeout language):**
G5 rights/provenance review executed 2026-08-20 — **result: BLOCKED** (1/2 lineages clear after
attribution action). Repository remains private. No visibility authorization has been granted.
**NOT READY FOR PUBLICATION — G5 RIGHTS/PROVENANCE BLOCKERS REMAIN.**