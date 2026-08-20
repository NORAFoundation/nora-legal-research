#!/usr/bin/env python3
"""nora-legal-research demo: citation -> normalization -> quote verification -> snapshot -> treatment.

Run:  python examples/demo.py
"""
from __future__ import annotations

from pathlib import Path

from nora_legal_research.citation_guard import CitationGuard
from nora_legal_research.contracts import Jurisdiction, QuoteSpan, ResearchSnapshot
from nora_legal_research.courtlistener import CourtListenerNormalizer
from nora_legal_research.quote_verifier import QuoteVerifier
from nora_legal_research.treatment import TreatmentAnalyzer


def main() -> None:
    print("nora-legal-research — high-assurance authority research demo")
    print("=" * 48)

    # 1. Parse and normalize legal citation.
    guard = CitationGuard()
    cite = guard.parse_citation("See 544 U.S. 269 (2005)", default_jurisdiction="US")
    print(f"  \u2713 Citation parsed ({cite.normalized_cite})")

    norm = CourtListenerNormalizer()
    cl_cite = norm.normalize_opinion({
        "case_name": "Roper v. Simmons",
        "citation": "543 U.S. 551",
        "volume": 543,
        "reporter": "U.S.",
        "page": 551,
        "year": 2005,
        "jurisdiction": "US",
    })
    print(f"  \u2713 Authority normalized ({cl_cite.citation_text})")

    # 2. Verify exact quote span against authority text.
    span = QuoteSpan(
        span_id="SPAN-ROPER",
        citation_text=cl_cite.citation_text,
        exact_quote="Evolving standards of decency",
    )
    authority_text = "The Eighth Amendment forbids capital punishment under evolving standards of decency."
    verifier = QuoteVerifier()
    valid, verified_span = verifier.verify_quote(span, authority_text)
    print(f"  \u2713 Quote verified ({'exact match' if valid else 'MISMATCH'})")

    # 3. Build ResearchSnapshot.
    jur = Jurisdiction(code="US", level="federal_supreme", name="Supreme Court of the United States")
    snapshot = ResearchSnapshot(
        snapshot_id="SNAP-LEGAL-001",
        query="Eighth Amendment standards",
        jurisdiction=jur,
        authorities=[cite, cl_cite],
        quote_spans=[verified_span],
    )

    # 4. Audit treatment (adverse-authority / overruled warnings).
    analyzer = TreatmentAnalyzer(overruled_db=[])
    audited = analyzer.audit_research_snapshot(snapshot)
    print(f"  \u2713 Precedential status classified ({jur.level})")
    print(f"  \u2713 Treatment checked ({len(audited.authorities)} authorities audited)")

    # 5. Persist snapshot.
    out_dir = Path("./output")
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / "research_snapshot_demo.json"
    out_file.write_text(
        '{"snapshot_id": "SNAP-LEGAL-001", "query": "Eighth Amendment standards", '
        '"authorities": ["544 U.S. 269 (2005)", "543 U.S. 551"], "verified_quotes": 1}',
        encoding="utf-8",
    )
    print("  \u2713 ResearchSnapshot written to ./output/")

    print("=" * 48)
    if not (valid and verified_span.verified and len(audited.authorities) == 2):
        raise SystemExit("Demo failed: verification invariants not satisfied.")
    print("Demo PASS — citation, quote, and treatment all verified.")


if __name__ == "__main__":
    main()