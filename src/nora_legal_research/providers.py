from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, Sequence

from .contracts import AuthorityRecord, ResearchSnapshot


@dataclass(frozen=True)
class ProviderCapabilities:
    search: bool = False
    opinion_retrieval: bool = False
    cluster_retrieval: bool = False
    court_metadata: bool = False
    citation_graph_outbound: bool = False
    citation_graph_inbound: bool = False
    unsupported: tuple[str, ...] = ()


@dataclass(frozen=True)
class AuthorityResearchRequest:
    research_id: str
    jurisdiction: str
    court_level: str
    doctrinal_issue: str
    target_proposition: str
    query_variants: tuple[str, ...] = ()
    date_range: str = "ALL_AVAILABLE"


@dataclass(frozen=True)
class ProviderSearchResult:
    provider: str
    capabilities: ProviderCapabilities
    authorities: tuple[Mapping[str, Any], ...] = ()
    provenance: Mapping[str, Any] = field(default_factory=dict)
    limitations: tuple[str, ...] = ()


class AuthorityProvider(Protocol):
    name: str
    capabilities: ProviderCapabilities

    def search(self, request: AuthorityResearchRequest) -> ProviderSearchResult:
        """Return provider-native records; no treatment/ranking decisions belong here."""


class CanonicalAuthorityNormalizer(Protocol):
    def normalize(self, request: AuthorityResearchRequest, result: ProviderSearchResult) -> ResearchSnapshot:
        """Convert provider records into a canonical ResearchSnapshot."""


def require_capability(provider: AuthorityProvider, capability: str) -> None:
    if not getattr(provider.capabilities, capability, False):
        raise NotImplementedError(f"provider capability unsupported: {capability}")
