import pytest
from nora_legal_research.citation_guard import CitationGuard
from nora_legal_research.contracts import Jurisdiction, QuoteSpan, ResearchSnapshot
from nora_legal_research.courtlistener import CourtListenerNormalizer
from nora_legal_research.quote_verifier import QuoteVerifier
from nora_legal_research.treatment import TreatmentAnalyzer

def test_nora_legal_research_minimum_vertical_slice():
    """
    Minimum Vertical Slice:
    citation parsing -> CourtListener normalization -> quote verification
    -> ResearchSnapshot generation -> treatment auditing
    """
    # 1. Parse and normalize legal citation
    guard = CitationGuard()
    cite = guard.parse_citation("See 544 U.S. 269 (2005)", default_jurisdiction="US")
    assert cite is not None
    assert cite.normalized_cite == "544 U.S. 269 (2005)"
    
    norm = CourtListenerNormalizer()
    cl_cite = norm.normalize_opinion({
        "case_name": "Roper v. Simmons",
        "citation": "543 U.S. 551",
        "volume": 543,
        "reporter": "U.S.",
        "page": 551,
        "year": 2005,
        "jurisdiction": "US"
    })
    
    # 2. Verify exact pinpoint quote span
    span = QuoteSpan(
        span_id="SPAN-ROPER",
        citation_text=cl_cite.citation_text,
        exact_quote="Evolving standards of decency"
    )
    
    authority_opinion_text = "The Eighth Amendment forbids capital punishment under evolving standards of decency."
    verifier = QuoteVerifier()
    valid, verified_span = verifier.verify_quote(span, authority_opinion_text)
    assert valid is True
    assert verified_span.verified is True

    # 3. Create ResearchSnapshot
    jur = Jurisdiction(code="US", level="federal_supreme", name="Supreme Court of the United States")
    snapshot = ResearchSnapshot(
        snapshot_id="SNAP-LEGAL-001",
        query="Eighth Amendment standards",
        jurisdiction=jur,
        authorities=[cite, cl_cite],
        quote_spans=[verified_span]
    )

    # 4. Audit treatment (overruled / adverse authority warnings)
    analyzer = TreatmentAnalyzer(overruled_db=[])
    audited_snapshot = analyzer.audit_research_snapshot(snapshot)

    assert len(audited_snapshot.authorities) == 2
    assert audited_snapshot.quote_spans[0].verified is True
