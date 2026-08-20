import pytest
from nora_legal_research.courtlistener import CourtListenerNormalizer

def test_courtlistener_normalizer():
    norm = CourtListenerNormalizer()
    payload = {
        "case_name": "Synthetic v. State",
        "citation": "100 U.S. 500",
        "volume": 100,
        "reporter": "U.S.",
        "page": 500,
        "year": 1880,
        "jurisdiction": "US"
    }
    
    cite = norm.normalize_opinion(payload)
    assert cite.normalized_cite == "100 U.S. 500"
    assert "Synthetic v. State" in cite.citation_text
