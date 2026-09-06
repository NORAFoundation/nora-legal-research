"""nora-legal-research package."""

from .citation_guard import CitationGuard
from .contracts import (
    AuthorityScore,
    AuthorityRecord,
    AuthorityType,
    Citation,
    CourtLevel,
    PrecedentialStatus,
    QuoteSpan,
    ResearchSnapshot,
    CurrentnessAssessment,
    ProviderMetadata,
    Provenance,
    QueryPlanReference,
    TreatmentStatus,
    VerificationStatus,
)
from .providers import AuthorityProvider, AuthorityResearchRequest, CourtListenerMirrorProvider, ProviderCapabilities, ProviderSearchResult
from .provider_contract import ProviderAuthorityCandidate, ProviderSearchRequestModel, ProviderSearchResponseModel
from .transport import AuthorityProviderTransport, FixtureTransport, HttpMirrorTransport
from .normalize import normalize_provider_result
from .courtlistener import CourtListenerNormalizer, CourtListenerProviderAdapter
from .quote_verifier import QuoteVerifier
from .treatment import TreatmentAnalyzer

__all__ = [
    "AuthorityScore",
    "AuthorityRecord",
    "AuthorityProvider",
    "AuthorityResearchRequest",
    "AuthorityProviderTransport",
    "AuthorityType",
    "Citation",
    "CitationGuard",
    "CourtLevel",
    "CourtListenerNormalizer",
    "CourtListenerProviderAdapter",
    "CourtListenerMirrorProvider",
    "FixtureTransport",
    "HttpMirrorTransport",
    "PrecedentialStatus",
    "QuoteSpan",
    "QuoteVerifier",
    "ResearchSnapshot",
    "CurrentnessAssessment",
    "ProviderCapabilities",
    "ProviderAuthorityCandidate",
    "ProviderMetadata",
    "ProviderSearchResult",
    "ProviderSearchRequestModel",
    "ProviderSearchResponseModel",
    "Provenance",
    "QueryPlanReference",
    "TreatmentStatus",
    "TreatmentAnalyzer",
    "VerificationStatus",
    "normalize_provider_result",
]
__version__ = "0.0.1"
