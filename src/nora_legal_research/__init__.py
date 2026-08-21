"""nora-legal-research package."""

from .citation_guard import CitationGuard
from .contracts import (
    AuthorityScore,
    AuthorityType,
    Citation,
    CourtLevel,
    PrecedentialStatus,
    QuoteSpan,
    ResearchSnapshot,
)
from .courtlistener import CourtListenerNormalizer
from .quote_verifier import QuoteVerifier
from .treatment import TreatmentAnalyzer

__all__ = [
    "AuthorityScore",
    "AuthorityType",
    "Citation",
    "CitationGuard",
    "CourtLevel",
    "CourtListenerNormalizer",
    "PrecedentialStatus",
    "QuoteSpan",
    "QuoteVerifier",
    "ResearchSnapshot",
    "TreatmentAnalyzer",
]
__version__ = "0.0.1"
