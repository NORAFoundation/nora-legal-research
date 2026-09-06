from __future__ import annotations

from datetime import date
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    opinion_type: str = "UNKNOWN"
    exact_proposition: Optional[str] = None
    source_url: Optional[str] = None
    provider_rank: Optional[int] = None
    relationship: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("case_name", "citation", "court")
    @classmethod
    def bounded_public_text(cls, value: str) -> str:
        if len(value) > 512 or any(token in value for token in ("@", "\\", "/Users/", "Dropbox/", "../")):
            raise ValueError("authority public text is unsafe or oversized")
        return value

    @field_validator("decision_date")
    @classmethod
    def valid_date(cls, value: str) -> str:
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
            raise ValueError("decision_date must be ISO date")
        return value


class ProviderSearchRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_contract_version: int = 1
    research_id: str
    jurisdiction: str
    court_level: str
    doctrinal_issue: str
    target_proposition: str
    query_variants: List[str] = Field(default_factory=list)
    date_range: str = "ALL_AVAILABLE"
    limit: int = 12
    requested_capabilities: List[str] = Field(default_factory=list)

    @field_validator("research_id", "jurisdiction", "court_level", "doctrinal_issue", "target_proposition", "date_range")
    @classmethod
    def bounded_request_text(cls, value: str) -> str:
        if len(value) > 256 or any(token in value for token in ("@", "\\", "/Users/", "Dropbox/", "../", "\n", "\r")):
            raise ValueError("provider request contains unsafe text")
        return value

    @field_validator("query_variants")
    @classmethod
    def bounded_queries(cls, value: List[str]) -> List[str]:
        if len(value) > 16 or any(len(item) > 256 or any(token in item for token in ("@", "\\", "/Users/", "Dropbox/", "../", "\n", "\r")) for item in value):
            raise ValueError("provider query plan is unsafe or oversized")
        return value

    @field_validator("limit")
    @classmethod
    def bounded_limit(cls, value: int) -> int:
        if value < 0 or value > 12:
            raise ValueError("provider limit exceeds public contract")
        return value


class ProviderSearchResponseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_contract_version: int = 1
    provider_name: str
    service_version: Optional[str] = None
    snapshot_id: Optional[str] = None
    snapshot_date: Optional[str] = None
    research_id: str
    capabilities: Dict[str, bool] = Field(default_factory=dict)
    authorities: List[ProviderAuthorityCandidate] = Field(default_factory=list)
    partial: bool = False
    limitations: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("authorities")
    @classmethod
    def bounded_authorities(cls, value: List[ProviderAuthorityCandidate]) -> List[ProviderAuthorityCandidate]:
        if len(value) > 12:
            raise ValueError("authority result exceeds limit")
        return value
