"""Canonical Jurisdiction Source Registry contract and authority definitions.

Enforces clear separation between primary controlling authority, persuasive authority,
explanatory/process material, and third-party snapshot providers.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


JURISDICTION_REGISTRY_CONTRACT = "nora.legal-research/JurisdictionSourceRegistry/1.0"


class AuthorityFamily(str, Enum):
    CONSTITUTION = "CONSTITUTION"
    STATUTE = "STATUTE"
    ADMINISTRATIVE_CODE = "ADMINISTRATIVE_CODE"
    COURT_RULES = "COURT_RULES"
    JUDICIAL_OPINION = "JUDICIAL_OPINION"
    FORMS_GUIDANCE = "FORMS_GUIDANCE"


class OfficialStatus(str, Enum):
    OFFICIAL = "OFFICIAL"
    UNOFFICIAL = "UNOFFICIAL"


class AuthorityLevel(str, Enum):
    PRIMARY_CONTROLLING = "PRIMARY_CONTROLLING"
    PRIMARY_PERSUASIVE = "PRIMARY_PERSUASIVE"
    EXPLANATORY = "EXPLANATORY"
    PROCESS = "PROCESS"


class GeographicScope(str, Enum):
    STATEWIDE = "STATEWIDE"
    CIRCUIT_7 = "CIRCUIT_7"
    CIRCUIT_8 = "CIRCUIT_8"
    FEDERAL_DISTRICT = "FEDERAL_DISTRICT"
    NATIONAL = "NATIONAL"


class LegalDomain(str, Enum):
    JUVENILE_CHILD_WELFARE = "JUVENILE_CHILD_WELFARE"
    CONSTITUTIONAL = "CONSTITUTIONAL"
    CIVIL_RIGHTS = "CIVIL_RIGHTS"
    CIVIL_PROCEDURE = "CIVIL_PROCEDURE"
    APPELLATE_PROCEDURE = "APPELLATE_PROCEDURE"
    EVIDENCE = "EVIDENCE"
    ADMINISTRATIVE = "ADMINISTRATIVE"
    GENERAL = "GENERAL"


class AcquisitionMethod(str, Enum):
    BULK_DOWNLOAD = "BULK_DOWNLOAD"
    REST_API = "REST_API"
    WEB_FETCH = "WEB_FETCH"
    MANUAL_PERIODIC = "MANUAL_PERIODIC"


class AcquisitionMode(str, Enum):
    DOWNLOAD_ARCHIVE = "DOWNLOAD_ARCHIVE"
    JSON_API = "JSON_API"
    HTML_DOCUMENT = "HTML_DOCUMENT"
    XML_FEED = "XML_FEED"
    RSS_FEED = "RSS_FEED"
    PDF_DOWNLOAD = "PDF_DOWNLOAD"


class UpdateCadence(str, Enum):
    CONTINUOUS = "CONTINUOUS"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    ANNUAL = "ANNUAL"
    BIENNIAL = "BIENNIAL"
    SESSIONAL = "SESSIONAL"
    IRREGULAR = "IRREGULAR"


class CurrentnessCapability(str, Enum):
    LIVE_FEED = "LIVE_FEED"
    OFFICIAL_BULLETIN = "OFFICIAL_BULLETIN"
    CITATOR_EXTERNAL = "CITATOR_EXTERNAL"
    SNAPSHOT_ONLY = "SNAPSHOT_ONLY"
    NONE = "NONE"


class AuthRequirement(str, Enum):
    NONE = "NONE"
    OPTIONAL_KEY = "OPTIONAL_KEY"
    REQUIRED_KEY = "REQUIRED_KEY"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    RESTRICTED = "RESTRICTED"
    UNSTABLE = "UNSTABLE"
    PLANNED = "PLANNED"


class ImplementationStatus(str, Enum):
    PLANNED = "PLANNED"
    IN_PROGRESS = "IN_PROGRESS"
    IMPLEMENTED = "IMPLEMENTED"
    VERIFIED = "VERIFIED"


class CoverageStatus(str, Enum):
    EXPERIMENTAL = "EXPERIMENTAL"
    BASIC = "BASIC"
    VERIFIED = "VERIFIED"
    DEEP_COVERAGE = "DEEP_COVERAGE"


class SourceDefinition(BaseModel):
    """Canonical registry entry for an authoritative legal source or provider."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    jurisdiction: str
    geographic_scope: GeographicScope
    legal_domain: LegalDomain
    authority_family: AuthorityFamily
    source_name: str
    provider_name: str
    official_status: OfficialStatus
    authority_level: AuthorityLevel
    canonical_url: str
    acquisition_method: AcquisitionMethod
    acquisition_mode: AcquisitionMode
    update_cadence: UpdateCadence
    temporal_version_semantics: str
    effective_date_semantics: str
    publication_date_semantics: str
    parser_normalizer_id: str
    citation_syntax: tuple[str, ...]
    currentness_capability: CurrentnessCapability
    historical_version_capability: bool
    provenance_capability: bool
    auth_requirement: AuthRequirement = AuthRequirement.NONE
    licensing_terms_notes: str
    availability_status: AvailabilityStatus
    implementation_status: ImplementationStatus
    coverage_status: CoverageStatus
    last_verified_date: date
    verification_evidence: str
    known_limitations: tuple[str, ...] = ()

    @field_validator("source_id")
    @classmethod
    def validate_source_id(cls, v: str) -> str:
        if not v or not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"Invalid source_id format: {v}")
        return v

    @field_validator("canonical_url")
    @classmethod
    def validate_canonical_url(cls, v: str) -> str:
        if not v.startswith("http://") and not v.startswith("https://"):
            raise ValueError(f"canonical_url must be an HTTP/HTTPS URL: {v}")
        return v

    @model_validator(mode="after")
    def validate_authority_and_official_semantics(self) -> "SourceDefinition":
        # 1. Controlling primary authority cannot be marked EXPLANATORY or PROCESS
        primary_families = {
            AuthorityFamily.CONSTITUTION,
            AuthorityFamily.STATUTE,
            AuthorityFamily.ADMINISTRATIVE_CODE,
            AuthorityFamily.COURT_RULES,
        }
        if self.authority_family in primary_families and self.authority_level in {
            AuthorityLevel.EXPLANATORY,
            AuthorityLevel.PROCESS,
        }:
            raise ValueError(
                f"Controlling authority family {self.authority_family.value} cannot be classified as "
                f"{self.authority_level.value}"
            )

        # 2. FORMS_GUIDANCE must be EXPLANATORY or PROCESS, never PRIMARY_CONTROLLING
        if self.authority_family == AuthorityFamily.FORMS_GUIDANCE and self.authority_level in {
            AuthorityLevel.PRIMARY_CONTROLLING,
            AuthorityLevel.PRIMARY_PERSUASIVE,
        }:
            raise ValueError("Forms and guidance must be classified as EXPLANATORY or PROCESS")

        # 3. Deep coverage requires formal certification evidence
        if self.coverage_status == CoverageStatus.DEEP_COVERAGE:
            if not self.verification_evidence or "CERTIFIED_DEEP_COVERAGE" not in self.verification_evidence:
                raise ValueError(
                    f"Source {self.source_id} cannot be marked DEEP_COVERAGE without CERTIFIED_DEEP_COVERAGE evidence"
                )

        # 4. Third-party snapshot mirrors cannot be marked OFFICIAL
        if "courtlistener" in self.source_id.lower() or "courtlistener" in self.provider_name.lower():
            if self.official_status == OfficialStatus.OFFICIAL:
                raise ValueError(
                    f"Third-party provider {self.provider_name} cannot be marked as OFFICIAL"
                )
            if self.currentness_capability == CurrentnessCapability.LIVE_FEED:
                raise ValueError(
                    "Snapshot mirror provider cannot be modeled as sufficient live currentness"
                )

        return self


class JurisdictionSourceRegistry(BaseModel):
    """Top-level registry maintaining authoritative sources across jurisdictions."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str = JURISDICTION_REGISTRY_CONTRACT
    schema_version: str = "1.0"
    registry_id: str = "nora-jurisdiction-registry-v1"
    sources: tuple[SourceDefinition, ...] = ()

    @field_validator("contract")
    @classmethod
    def supported_contract(cls, value: str) -> str:
        if value != JURISDICTION_REGISTRY_CONTRACT:
            raise ValueError(f"unsupported JurisdictionSourceRegistry contract: {value}")
        return value

    @model_validator(mode="after")
    def validate_unique_sources(self) -> "JurisdictionSourceRegistry":
        ids: set[str] = set()
        for source in self.sources:
            if source.source_id in ids:
                raise ValueError(f"Duplicate source_id in registry: {source.source_id}")
            ids.add(source.source_id)
        return self

    def filter_by_jurisdiction(self, jurisdiction: str) -> tuple[SourceDefinition, ...]:
        return tuple(s for s in self.sources if s.jurisdiction == jurisdiction)

    def filter_by_domain(self, domain: LegalDomain) -> tuple[SourceDefinition, ...]:
        return tuple(s for s in self.sources if s.legal_domain == domain or s.legal_domain == LegalDomain.GENERAL)

    def get_source(self, source_id: str) -> Optional[SourceDefinition]:
        for s in self.sources:
            if s.source_id == source_id:
                return s
        return None
