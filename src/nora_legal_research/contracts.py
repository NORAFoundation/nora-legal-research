from __future__ import annotations
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

class AuthorityType(str, Enum):
    CONSTITUTIONAL = "constitutional"
    STATUTE = "statute"
    REGULATION = "regulation"
    PRECEDENT_BINDING = "precedent_binding"
    PRECEDENT_PERSUASIVE = "precedent_persuasive"
    SECONDARY = "secondary"

class PrecedentialStatus(str, Enum):
    BINDING = "binding"
    PERSUASIVE = "persuasive"
    OVERRULED = "overruled"
    QUESTIONED = "questioned"
    SUPERSEDED_BY_STATUTE = "superseded_by_statute"
    UNKNOWN = "unknown"


class TreatmentStatus(str, Enum):
    COMPLETE = "complete"
    LIMITED = "limited"
    NOT_AVAILABLE = "not_available"
    UNKNOWN = "unknown"


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    PARTIAL = "partial"
    NOT_AVAILABLE = "not_available"


class OpinionType(str, Enum):
    MAJORITY = "majority"
    CONCURRENCE = "concurrence"
    DISSENT = "dissent"
    PER_CURIAM = "per_curiam"
    UNKNOWN = "unknown"


class RetrievalStatus(str, Enum):
    COMPLETE = "complete"
    EMPTY = "empty"
    PARTIAL = "partial"


RESEARCH_SNAPSHOT_CONTRACT = "nora.legal-research/ResearchSnapshot/1.0"

class CourtLevel(str, Enum):
    FEDERAL_SUPREME = "federal_supreme"
    FEDERAL_APPELLATE = "federal_appellate"
    FEDERAL_DISTRICT = "federal_district"
    STATE_SUPREME = "state_supreme"
    STATE_APPELLATE = "state_appellate"
    STATE_TRIAL = "state_trial"

class AuthorityScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    citation: str
    authority_type: AuthorityType = AuthorityType.SECONDARY
    precedential_status: PrecedentialStatus = PrecedentialStatus.PERSUASIVE
    score: float = 0.5
    is_binding: bool = False
class Jurisdiction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    code: str  # e.g. US, US-WI, US-MN, US-8th-Cir
    level: str  # federal_supreme, federal_appellate, state_supreme, state_appellate, trial
    name: str

class Citation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    citation_text: str
    volume: Optional[int] = None
    reporter: Optional[str] = None
    page: Optional[int] = None
    year: Optional[int] = None
    jurisdiction_code: str
    normalized_cite: str


class AuthorityRecord(Citation):
    """Canonical public authority record; provider details remain provenance, not truth."""

    model_config = ConfigDict(extra="forbid")
    authority_id: Optional[str] = None
    case_name: Optional[str] = None
    court: Optional[str] = None
    decision_date: Optional[str] = None
    authority_type: AuthorityType = AuthorityType.PRECEDENT_PERSUASIVE
    precedential_status: PrecedentialStatus = PrecedentialStatus.UNKNOWN
    exact_proposition: Optional[str] = None
    procedural_posture: Optional[str] = None
    pinpoint: Optional[str] = None
    provider_relationship: Optional[str] = None
    quote_verification: VerificationStatus = VerificationStatus.NOT_AVAILABLE
    treatment_status: TreatmentStatus = TreatmentStatus.UNKNOWN
    adverse_relationship: Optional[str] = None
    provider: Optional[str] = None
    provider_record_id: Optional[str] = None
    provider_cluster_id: Optional[str] = None
    opinion_id: Optional[str] = None
    opinion_type: OpinionType = OpinionType.UNKNOWN
    provider_rank: Optional[int] = None
    retrieved_at: Optional[datetime] = None
    limitations: List[str] = Field(default_factory=list)

class QuoteSpan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    span_id: str
    citation_text: str
    exact_quote: str
    pinpoint_page: Optional[int] = None
    verified: bool = False


class Provenance(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str
    source_kind: str
    source_uri: Optional[str] = None
    source_record_id: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    snapshot_id: Optional[str] = None
    snapshot_date: Optional[str] = None
    service_version: Optional[str] = None
    mirror_git_sha: Optional[str] = None
    provider_contract_version: Optional[int] = None
    query_plan_hash: Optional[str] = None
    digest: Optional[str] = None
    limitations: List[str] = Field(default_factory=list)


class ProviderMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider_name: str
    provider_version: Optional[str] = None
    access_mode: str
    capabilities_used: List[str] = Field(default_factory=list)
    capabilities_unavailable: List[str] = Field(default_factory=list)
    snapshot_id: Optional[str] = None
    snapshot_date: Optional[str] = None
    service_version: Optional[str] = None
    mirror_git_sha: Optional[str] = None
    provider_contract_version: Optional[int] = None
    query_plan_hash: Optional[str] = None


class QueryPlanReference(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_id: str
    variants: List[str] = Field(default_factory=list)
    filters: Dict[str, str] = Field(default_factory=dict)
    jurisdiction: Optional[str] = None
    court_level: Optional[str] = None
    date_range: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    limit: Optional[int] = None
    capabilities_requested: List[str] = Field(default_factory=list)
    query_plan_hash: Optional[str] = None


class CurrentnessAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: TreatmentStatus = TreatmentStatus.UNKNOWN
    checked_at: Optional[datetime] = None
    unresolved_questions: List[str] = Field(default_factory=list)

class ResearchSnapshot(BaseModel):
    """Stable provider-neutral output consumed by NORA legal workflows."""

    model_config = ConfigDict(extra="forbid")
    snapshot_id: str
    contract: str = RESEARCH_SNAPSHOT_CONTRACT
    consumer_snapshot_id: Optional[str] = None
    query: str
    jurisdiction: Jurisdiction
    authorities: List[AuthorityRecord] = Field(default_factory=list)
    quote_spans: List[QuoteSpan] = Field(default_factory=list)
    status_warnings: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = "1.0"
    retrieval_status: RetrievalStatus = RetrievalStatus.COMPLETE
    research_id: Optional[str] = None
    checked_at: Optional[datetime] = None
    court_hierarchy_scope: Optional[str] = None
    doctrinal_issue: Optional[str] = None
    target_proposition: Optional[str] = None
    procedural_posture: Optional[str] = None
    query_plan: Optional[QueryPlanReference] = None
    provider: Optional[ProviderMetadata] = None
    adverse_authorities: List[AuthorityRecord] = Field(default_factory=list)
    currentness: CurrentnessAssessment = Field(default_factory=CurrentnessAssessment)
    unresolved_treatment_questions: List[str] = Field(default_factory=list)
    missing_verification: List[str] = Field(default_factory=list)
    confidence: Optional[str] = None
    limitations: List[str] = Field(default_factory=list)
    provenance: List[Provenance] = Field(default_factory=list)
    reproducibility: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("authorities", "adverse_authorities", mode="before")
    @classmethod
    def accept_legacy_citations(cls, value: Any) -> Any:
        if not isinstance(value, list):
            return value
        converted = []
        for item in value:
            if isinstance(item, Citation):
                converted.append(item.model_dump())
            else:
                converted.append(item)
        return converted

    @field_validator("schema_version")
    @classmethod
    def require_supported_schema_version(cls, value: str) -> str:
        if value != "1.0":
            raise ValueError("unsupported ResearchSnapshot schema version")
        return value

    @field_validator("contract")
    @classmethod
    def require_supported_contract(cls, value: str) -> str:
        if value != RESEARCH_SNAPSHOT_CONTRACT:
            raise ValueError("unsupported ResearchSnapshot contract")
        return value

    @model_validator(mode="after")
    def keep_snapshot_identities_distinct(self) -> "ResearchSnapshot":
        if self.consumer_snapshot_id is not None and self.consumer_snapshot_id != self.snapshot_id:
            raise ValueError("consumer snapshot identity mismatch")
        if self.provider is not None and self.provider.snapshot_id == self.snapshot_id:
            raise ValueError("consumer snapshot_id must not reuse provider snapshot identity")
        return self
