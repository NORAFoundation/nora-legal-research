import pytest
from nora_legal_research.citation_guard import CitationGuard
from nora_legal_research.contracts import QuoteSpan
from nora_legal_research.quote_verifier import QuoteVerifier

def test_citation_guard_parsing():
    guard = CitationGuard()
    cite = guard.parse_citation("See 544 U.S. 269 (2005) for controlling standard", default_jurisdiction="US")
    
    assert cite is not None
    assert cite.volume == 544
    assert cite.reporter == "U.S."
    assert cite.page == 269
    assert cite.year == 2005
    assert cite.normalized_cite == "544 U.S. 269 (2005)"

def test_quote_verifier():
    verifier = QuoteVerifier()
    span = QuoteSpan(
        span_id="SPAN-100",
        citation_text="544 U.S. 269",
        exact_quote="synthetic legal text holding"
    )
    
    auth_text = "This opinion contains synthetic legal text holding for verification."
    valid, updated_span = verifier.verify_quote(span, auth_text)
    assert valid is True
    assert updated_span.verified is True
