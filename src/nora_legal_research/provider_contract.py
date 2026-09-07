from __future__ import annotations

from datetime import datetime
import math
import re
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .contracts import OpinionType


PROVIDER_CONTRACT_VERSION = 1
COURTLISTENER_MIRROR = "COURTLISTENER_MIRROR"
ACCESS_MODE_MIRROR_API = "MIRROR_API"
ACCESS_MODE_MCP = "MCP"
ACCESS_MODE_FIXTURE = "FIXTURE"
SUPPORTED_ACCESS_MODES = {ACCESS_MODE_MIRROR_API, ACCESS_MODE_MCP, ACCESS_MODE_FIXTURE}
SUPPORTED_CAPABILITIES = {
    "search",
    "opinion_retrieval",
    "cluster_retrieval",
    "court_metadata",
    "citation_graph_outbound",
    "citation_graph_inbound",
}

_SAFE_TEXT_TOKEN = re.compile(r"[\x00-\x1f\x7f]|(?:^|\s)(?:private|confidential|docket|case[_ -]?number|source[_ -]?text|chronology)(?:\s|$)", re.I)
_EMAIL = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
_ISO_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_GIT_OR_SHA256 = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def _safe_public_text(value: str, *, field: str, maximum: int = 512) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError(f"{field} must be bounded public text")
    if _EMAIL.search(value) or _SAFE_TEXT_TOKEN.search(value):
        raise ValueError(f"{field} contains private or unsafe text")
    if any(token in value for token in ("/Users/", "Dropbox/", "../", "\\")):
        raise ValueError(f"{field} contains a local path")
    return value


class ProviderProvenanceModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_id: Optional[str] = None
    snapshot_date: Optional[str] = None
    service_version: Optional[str] = None
    mirror_git_sha: Optional[str] = None
    query_plan_hash: Optional[str] = None
    provider_contract_version: Optional[int] = None
    retrieved_at: Optional[datetime] = None
    source: Optional[str] = None
    query_class: Optional[str] = None
    native_result_count: Optional[int] = None
    limitations: List[str] = Field(default_factory=list)

    @field_validator("snapshot_id", "service_version", "source")
    @classmethod
    def validate_bounded_metadata(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else _safe_public_text(value, field="provenance metadata", maximum=256)

    @field_validator("query_class")
    @classmethod
    def validate_query_class(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else _safe_public_text(value, field="query_class", maximum=128)

    @field_validator("native_result_count")
    @classmethod
    def validate_native_result_count(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and (value < 0 or value > 1000000):
            raise ValueError("native_result_count is out of bounds")
        return value

    @field_validator("snapshot_date")
    @classmethod
    def validate_snapshot_date(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _ISO_DATE.fullmatch(value):
            raise ValueError("snapshot_date must be ISO date")
        return value

    @field_validator("mirror_git_sha")
    @classmethod
    def validate_mirror_git_sha(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _GIT_OR_SHA256.fullmatch(value):
            raise ValueError("mirror_git_sha must be a lowercase Git SHA or SHA-256")
        return value

    @field_validator("query_plan_hash")
    @classmethod
    def validate_query_plan_hash(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _SHA256.fullmatch(value):
            raise ValueError("query_plan_hash must be a lowercase SHA-256")
        return value


class ProviderCandidateMetadata(BaseModel):
    """Small, public-only metadata allowlist emitted by the mirror envelope."""

    model_config = ConfigDict(extra="forbid")

    provider_score: Optional[float] = None

    @field_validator("provider_score")
    @classmethod
    def finite_score(cls, value: Optional[float]) -> Optional[float]:
        if value is not None and not math.isfinite(value):
            raise ValueError("provider_score must be finite")
        return value


class ProviderAuthorityCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_record_id: str
    case_name: str
    citation: str
    court: str
    decision_date: str
    authority_status: str = "UNKNOWN"
    binding_weight: str = "UNKNOWN"
    procedural_fit: str = "UNKNOWN"
    opinion_type: OpinionType = OpinionType.UNKNOWN
    exact_proposition: Optional[str] = None
    source_url: Optional[str] = None
    provider_rank: Optional[int] = None
    relationship: Optional[str] = None
    provider_cluster_id: Optional[str] = None
    opinion_id: Optional[str] = None
    metadata: ProviderCandidateMetadata = Field(default_factory=ProviderCandidateMetadata)

    @field_validator("opinion_type", mode="before")
    @classmethod
    def normalize_opinion_type(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.lower().replace("-", "_")
        return value

    @field_validator("provider_record_id", "case_name", "citation", "court")
    @classmethod
    def bounded_public_text(cls, value: str, info: Any) -> str:
        return _safe_public_text(value, field=info.field_name)

    @field_validator("exact_proposition", "relationship")
    @classmethod
    def bounded_optional_public_text(cls, value: Optional[str], info: Any) -> Optional[str]:
        return None if value is None else _safe_public_text(value, field=info.field_name, maximum=1024)

    @field_validator("provider_cluster_id", "opinion_id")
    @classmethod
    def bounded_optional_id(cls, value: Optional[str], info: Any) -> Optional[str]:
        return None if value is None else _safe_public_text(value, field=info.field_name, maximum=256)

    @field_validator("source_url")
    @classmethod
    def public_source_url(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        if not value.startswith("https://") or _EMAIL.search(value) or any(token in value for token in ("/Users/", "Dropbox/", "../", "\\")):
            raise ValueError("source_url must be an HTTPS public URL")
        return _safe_public_text(value, field="source_url", maximum=2048)

    @field_validator("decision_date")
    @classmethod
    def valid_date(cls, value: str) -> str:
        if not _ISO_DATE.fullmatch(value):
            raise ValueError("decision_date must be ISO date")
        return value

    @field_validator("provider_rank")
    @classmethod
    def valid_rank(cls, value: Optional[int]) -> Optional[int]:
        if value is not None and value < 1:
            raise ValueError("provider_rank must be positive")
        return value

class AuthorityResearchRequest(BaseModel):
    """The only request shape that may cross the provider boundary."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider_contract_version: int
    research_id: str
    jurisdiction: str
    court_level: str
    doctrinal_issue: str
    target_proposition: str
    query_variants: tuple[str, ...] = ()
    date_range: str = "ALL_AVAILABLE"
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: int = 12
    requested_capabilities: tuple[str, ...] = ("search",)

    @field_validator("provider_contract_version")
    @classmethod
    def supported_contract(cls, value: int) -> int:
        if value != PROVIDER_CONTRACT_VERSION:
            raise ValueError("unsupported provider contract version")
        return value

    @field_validator("research_id", "jurisdiction", "court_level", "doctrinal_issue", "target_proposition", "date_range")
    @classmethod
    def bounded_request_text(cls, value: str, info: Any) -> str:
        return _safe_public_text(value, field=info.field_name, maximum=256)

    @field_validator("query_variants")
    @classmethod
    def bounded_queries(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) > 16:
            raise ValueError("query plan has too many variants")
        return tuple(_safe_public_text(item, field="query_variant", maximum=256) for item in value)

    @field_validator("date_from", "date_to")
    @classmethod
    def bounded_date_bounds(cls, value: Optional[str], info: Any) -> Optional[str]:
        if value is not None and not _ISO_DATE.fullmatch(value):
            raise ValueError(f"{info.field_name} must be ISO date")
        return value

    @field_validator("limit")
    @classmethod
    def bounded_limit(cls, value: int) -> int:
        if value < 0 or value > 12:
            raise ValueError("provider limit exceeds public contract")
        return value

    @field_validator("requested_capabilities")
    @classmethod
    def supported_capabilities(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if any(item not in SUPPORTED_CAPABILITIES for item in value):
            raise ValueError("unsupported requested provider capability")
        return tuple(dict.fromkeys(value))

    @model_validator(mode="after")
    def valid_date_order(self) -> "AuthorityResearchRequest":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must not be after date_to")
        return self


# Compatibility name retained for consumers of the original provider slice.
ProviderSearchRequestModel = AuthorityResearchRequest


def serialize_provider_request(request: AuthorityResearchRequest) -> dict[str, Any]:
    """Serialize only the reviewed public request allowlist.

    This is intentionally explicit so adding a future model field cannot make
    it cross an HTTP/MCP boundary by accident.
    """

    value = AuthorityResearchRequest.model_validate(request)
    return {
        "provider_contract_version": value.provider_contract_version,
        "research_id": value.research_id,
        "jurisdiction": value.jurisdiction,
        "court_level": value.court_level,
        "doctrinal_issue": value.doctrinal_issue,
        "target_proposition": value.target_proposition,
        "query_variants": list(value.query_variants),
        "date_range": value.date_range,
        "date_from": value.date_from,
        "date_to": value.date_to,
        "limit": value.limit,
        "requested_capabilities": list(value.requested_capabilities),
    }


class ProviderSearchResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    provider_contract_version: int
    provider_name: str
    service_version: Optional[str] = None
    mirror_git_sha: Optional[str] = None
    snapshot_id: str
    snapshot_date: str
    research_id: str
    capabilities: dict[str, bool]
    authorities: List[ProviderAuthorityCandidate]
    partial: bool = False
    truncated: bool = False
    limitations: List[str]
    provenance: ProviderProvenanceModel

    @field_validator("provider_contract_version")
    @classmethod
    def supported_contract(cls, value: int) -> int:
        if value != PROVIDER_CONTRACT_VERSION:
            raise ValueError("unsupported provider contract version")
        return value

    @field_validator("provider_name", "research_id")
    @classmethod
    def valid_identity_text(cls, value: str, info: Any) -> str:
        return _safe_public_text(value, field=info.field_name, maximum=256)

    @field_validator("service_version")
    @classmethod
    def valid_service_version(cls, value: Optional[str]) -> Optional[str]:
        return None if value is None else _safe_public_text(value, field="service_version", maximum=256)

    @field_validator("mirror_git_sha")
    @classmethod
    def valid_mirror_git_sha(cls, value: Optional[str]) -> Optional[str]:
        if value is not None and not _GIT_OR_SHA256.fullmatch(value):
            raise ValueError("mirror_git_sha must be a lowercase Git SHA or SHA-256")
        return value

    @field_validator("snapshot_date")
    @classmethod
    def valid_snapshot_date(cls, value: str) -> str:
        if not _ISO_DATE.fullmatch(value):
            raise ValueError("snapshot_date must be ISO date")
        return value

    @field_validator("capabilities")
    @classmethod
    def valid_capabilities(cls, value: dict[str, bool]) -> dict[str, bool]:
        if set(value) - SUPPORTED_CAPABILITIES:
            raise ValueError("provider response advertises an unknown capability")
        return value

    @field_validator("authorities")
    @classmethod
    def bounded_authorities(cls, value: List[ProviderAuthorityCandidate]) -> List[ProviderAuthorityCandidate]:
        if len(value) > 12:
            raise ValueError("authority result exceeds limit")
        return value

    @model_validator(mode="after")
    def consistent_provenance(self) -> "ProviderSearchResponseModel":
        if self.provenance.snapshot_id is not None and self.provenance.snapshot_id != self.snapshot_id:
            raise ValueError("provider snapshot identity mismatch")
        if self.provenance.snapshot_date is not None and self.provenance.snapshot_date != self.snapshot_date:
            raise ValueError("provider snapshot date mismatch")
        return self
