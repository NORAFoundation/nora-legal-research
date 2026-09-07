from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Protocol

from pydantic import BaseModel, ConfigDict, Field, field_validator

from .contracts import ResearchSnapshot, RetrievalStatus
from .errors import ProviderContractError, UnsupportedProviderCapability
from .provider_contract import (
    ACCESS_MODE_FIXTURE,
    COURTLISTENER_MIRROR,
    PROVIDER_CONTRACT_VERSION,
    SUPPORTED_ACCESS_MODES,
    ProviderAuthorityCandidate,
    ProviderProvenanceModel,
    AuthorityResearchRequest,
)


class ProviderCapabilities(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    search: bool = False
    opinion_retrieval: bool = False
    cluster_retrieval: bool = False
    court_metadata: bool = False
    citation_graph_outbound: bool = False
    citation_graph_inbound: bool = False
    unsupported: tuple[str, ...] = ()


class ProviderSearchResult(BaseModel):
    """Validated provider-neutral result after a transport envelope is consumed."""

    model_config = ConfigDict(extra="forbid")

    provider: str
    access_mode: str = ACCESS_MODE_FIXTURE
    provider_contract_version: int = PROVIDER_CONTRACT_VERSION
    research_id: str | None = None
    capabilities: ProviderCapabilities
    authorities: tuple[Mapping[str, Any], ...] = ()
    partial: bool = False
    truncated: bool = False
    provenance: dict[str, Any] = Field(default_factory=dict)
    limitations: tuple[str, ...] = ()

    @field_validator("provider", "access_mode")
    @classmethod
    def bounded_identity(cls, value: str) -> str:
        if not isinstance(value, str) or not value or len(value) > 128 or any(token in value for token in ("@", "\\", "/Users/", "Dropbox/", "../")):
            raise ValueError("provider identity is invalid")
        return value

    @field_validator("provider_contract_version")
    @classmethod
    def supported_contract(cls, value: int) -> int:
        if value != PROVIDER_CONTRACT_VERSION:
            raise ValueError("unsupported provider contract version")
        return value

    @field_validator("research_id")
    @classmethod
    def bounded_research_id(cls, value: str | None) -> str | None:
        if value is not None and (not value or len(value) > 128 or any(token in value for token in ("@", "\\", "/Users/", "Dropbox/", "../"))):
            raise ValueError("provider research_id is invalid")
        return value

    @field_validator("access_mode")
    @classmethod
    def supported_access_mode(cls, value: str) -> str:
        if value not in SUPPORTED_ACCESS_MODES:
            raise ValueError("unsupported provider access mode")
        return value

    @field_validator("authorities")
    @classmethod
    def bounded_authorities(cls, value: tuple[Mapping[str, Any], ...], info: Any) -> tuple[Mapping[str, Any], ...]:
        if len(value) > 12:
            raise ValueError("provider result exceeds authority limit")
        if info.data.get("provider") == COURTLISTENER_MIRROR:
            validated = tuple(ProviderAuthorityCandidate.model_validate(item).model_dump(mode="json") for item in value)
            return validated
        if any(not isinstance(item, Mapping) for item in value):
            raise ValueError("provider authority record must be an object")
        return value

    @field_validator("provenance")
    @classmethod
    def bounded_provenance(cls, value: dict[str, Any]) -> dict[str, Any]:
        return ProviderProvenanceModel.model_validate(value).model_dump(mode="json", exclude_none=True)

    @property
    def retrieval_status(self) -> RetrievalStatus:
        if self.partial or self.truncated:
            return RetrievalStatus.PARTIAL
        if not self.authorities:
            return RetrievalStatus.EMPTY
        return RetrievalStatus.COMPLETE


def canonical_query_plan(request: AuthorityResearchRequest) -> dict[str, Any]:
    """Return the timestamp-free substantive query plan representation."""

    value = AuthorityResearchRequest.model_validate(request)
    return {
        "query_variants": list(value.query_variants),
        "jurisdiction": value.jurisdiction,
        "court_level": value.court_level,
        "date_range": value.date_range,
        "date_from": value.date_from,
        "date_to": value.date_to,
        "limit": value.limit,
        "capabilities_requested": list(value.requested_capabilities),
    }


def query_plan_hash(request: AuthorityResearchRequest) -> str:
    canonical = json.dumps(canonical_query_plan(request), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


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
        raise UnsupportedProviderCapability(f"provider capability unsupported: {capability}")


class CourtListenerMirrorProvider:
    """Canonical provider facade over a transport; mirror storage stays outside this package."""

    name = COURTLISTENER_MIRROR

    def __init__(self, transport: AuthorityProvider):
        self.transport = transport
        self.capabilities = transport.capabilities

    def search(self, request: AuthorityResearchRequest) -> ProviderSearchResult:
        request = AuthorityResearchRequest.model_validate(request)
        require_capability(self, "search")
        result = ProviderSearchResult.model_validate(self.transport.search(request))
        if result.provider != self.name:
            raise ProviderContractError("provider identity does not match CourtListener mirror")
        if result.research_id is not None and result.research_id != request.research_id:
            raise ProviderContractError("provider research_id does not match request")
        for capability in request.requested_capabilities:
            if not getattr(result.capabilities, capability, False):
                raise UnsupportedProviderCapability(f"provider did not negotiate capability: {capability}")
        return result.model_copy(update={"research_id": request.research_id})
