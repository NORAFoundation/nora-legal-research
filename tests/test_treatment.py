import pytest
from nora_legal_research.contracts import Citation, Jurisdiction, PrecedentialStatus, ResearchSnapshot
from nora_legal_research.treatment import TreatmentAnalyzer

def test_treatment_analyzer_overruled_detection():
    analyzer = TreatmentAnalyzer(overruled_db=["500 U.S. 100"])
    
    good_cite = Citation(
        citation_text="544 U.S. 269",
        volume=544,
        reporter="U.S.",
        page=269,
        year=2005,
        jurisdiction_code="US",
        normalized_cite="544 U.S. 269"
    )
    
    bad_cite = Citation(
        citation_text="500 U.S. 100",
        volume=500,
        reporter="U.S.",
        page=100,
        year=1991,
        jurisdiction_code="US",
        normalized_cite="500 U.S. 100"
    )

    jur = Jurisdiction(code="US", level="federal_supreme", name="Supreme Court")
    snapshot = ResearchSnapshot(
        snapshot_id="SNAP-TEST",
        query="test query",
        jurisdiction=jur,
        authorities=[good_cite, bad_cite]
    )
    
    audited = analyzer.audit_research_snapshot(snapshot)
    assert len(audited.status_warnings) == 1
    assert "OVERRULED" in audited.status_warnings[0]
