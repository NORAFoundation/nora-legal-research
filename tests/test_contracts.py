import pytest
from nora_legal_research.contracts import (
    AuthorityType,
    Citation,
    Jurisdiction,
    PrecedentialStatus,
    QuoteSpan,
    ResearchSnapshot
)

def test_legal_research_unified_contracts():
    jur = Jurisdiction(
        code="US-WI",
        level="state_supreme",
        name="Supreme Court of Wisconsin"
    )
    
    cite = Citation(
        citation_text="2026 WI 42",
        volume=2026,
        reporter="WI",
        page=42,
        year=2026,
        jurisdiction_code="US-WI",
        normalized_cite="2026 WI 42"
    )
    
    span = QuoteSpan(
        span_id="SPAN-001",
        citation_text="2026 WI 42",
        exact_quote="Synthetic holding regarding evidence reconstructability",
        pinpoint_page=45,
        verified=True
    )
    
    snapshot = ResearchSnapshot(
        snapshot_id="SNAP-001",
        query="reconstructability of digital evidence",
        jurisdiction=jur,
        authorities=[cite],
        quote_spans=[span],
        status_warnings=[]
    )
    
    assert snapshot.jurisdiction.code == "US-WI"
    assert snapshot.authorities[0].normalized_cite == "2026 WI 42"
    assert snapshot.quote_spans[0].verified is True
