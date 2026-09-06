from __future__ import annotations
from typing import Any, Callable, Dict, Optional
from nora_legal_research.contracts import AuthorityRecord, Citation, PrecedentialStatus
from nora_legal_research.providers import (
    AuthorityResearchRequest,
    ProviderCapabilities,
    ProviderSearchResult,
)

class CourtListenerNormalizer:
    """
    Normalizes CourtListener bulk API payload objects into canonical Citations
    and authority records (derived from legal-research-scaffold).
    """
    def normalize_opinion(self, payload: Dict[str, Any]) -> Citation:
        case_name = payload.get("case_name", "Unknown Case")
        cite_str = payload.get("citation", "Unknown Citation")
        vol = payload.get("volume")
        rep = payload.get("reporter")
        pg = payload.get("page")
        yr = payload.get("year")
        jur = payload.get("jurisdiction", "US")

        return Citation(
            citation_text=f"{case_name}, {cite_str}",
            volume=vol,
            reporter=rep,
            page=pg,
            year=yr,
            jurisdiction_code=jur,
            normalized_cite=cite_str
        )

    def normalize_authority(self, payload: Dict[str, Any], *, provider_record_id: str | None = None) -> AuthorityRecord:
        citation = self.normalize_opinion(payload)
        status = payload.get("precedential_status", "unknown")
        if status not in {item.value for item in PrecedentialStatus}:
            status = "unknown"
        return AuthorityRecord(
            **citation.model_dump(),
            authority_id=provider_record_id,
            case_name=payload.get("case_name") or payload.get("caseName"),
            court=payload.get("court") if isinstance(payload.get("court"), str) else None,
            decision_date=(payload.get("dateFiled") or payload.get("date_filed") or payload.get("date")),
            precedential_status=status,
            exact_proposition=payload.get("exact_proposition"),
            procedural_posture=payload.get("procedural_posture"),
            adverse_relationship=payload.get("relationship"),
            provider="COURTLISTENER",
            provider_record_id=provider_record_id,
            limitations=["Provider retrieval does not establish treatment or currentness."],
        )


class CourtListenerProviderAdapter:
    """Provider boundary only; acquisition, ranking and treatment stay outside this adapter."""

    name = "COURTLISTENER"
    capabilities = ProviderCapabilities(
        search=True,
        opinion_retrieval=True,
        cluster_retrieval=True,
        court_metadata=True,
        citation_graph_outbound=True,
        citation_graph_inbound=True,
    )

    def __init__(self, search_fn: Callable[[AuthorityResearchRequest], list[Dict[str, Any]]]):
        self._search_fn = search_fn

    def search(self, request: AuthorityResearchRequest) -> ProviderSearchResult:
        records = self._search_fn(request)
        if not isinstance(records, list):
            raise ValueError("CourtListener provider returned a non-list result")
        return ProviderSearchResult(
            provider=self.name,
            capabilities=self.capabilities,
            authorities=tuple(records),
            limitations=("Treatment and currentness require separate verification.",),
        )
