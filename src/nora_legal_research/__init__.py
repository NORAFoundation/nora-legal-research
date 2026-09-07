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
    OpinionType,
    RetrievalStatus,
    RESEARCH_SNAPSHOT_CONTRACT,
    ProviderMetadata,
    Provenance,
    QueryPlanReference,
    TreatmentStatus,
    VerificationStatus,
)
from .providers import AuthorityProvider, AuthorityResearchRequest, CourtListenerMirrorProvider, ProviderCapabilities, ProviderSearchResult, canonical_query_plan, query_plan_hash
from .provider_contract import ProviderAuthorityCandidate, ProviderCandidateMetadata, ProviderSearchRequestModel, ProviderSearchResponseModel, serialize_provider_request
from .transport import AuthorityProviderTransport, FixtureTransport, HttpMirrorTransport, McpMirrorTransport
from .errors import (
    ProviderAuthenticationError,
    ProviderContractError,
    ProviderError,
    ProviderErrorEnvelope,
    ProviderErrorInfo,
    ProviderPartialResult,
    ProviderRateLimited,
    ProviderUnavailable,
    UnsupportedProviderCapability,
)
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
    "McpMirrorTransport",
    "PrecedentialStatus",
    "QuoteSpan",
    "QuoteVerifier",
    "ResearchSnapshot",
    "CurrentnessAssessment",
    "OpinionType",
    "RetrievalStatus",
    "RESEARCH_SNAPSHOT_CONTRACT",
    "ProviderCapabilities",
    "ProviderAuthorityCandidate",
    "ProviderMetadata",
    "ProviderSearchResult",
    "ProviderSearchRequestModel",
    "ProviderSearchResponseModel",
    "ProviderCandidateMetadata",
    "ProviderError",
    "ProviderErrorEnvelope",
    "ProviderErrorInfo",
    "ProviderUnavailable",
    "ProviderAuthenticationError",
    "ProviderRateLimited",
    "ProviderContractError",
    "ProviderPartialResult",
    "UnsupportedProviderCapability",
    "Provenance",
    "QueryPlanReference",
    "TreatmentStatus",
    "TreatmentAnalyzer",
    "VerificationStatus",
    "normalize_provider_result",
    "serialize_provider_request",
    "canonical_query_plan",
    "query_plan_hash",
]
__version__ = "0.0.1"
