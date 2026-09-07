"""Auditable research completeness and fact/source epistemology artifacts."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


RESEARCH_QUALITY_CONTRACT = "nora.legal-research/ResearchQuality/1.0"


class EpistemicStatus(str, Enum):
    USER_REPORTED = "USER_REPORTED"
    USER_INTERPRETATION = "USER_INTERPRETATION"
    INFERRED = "INFERRED"
    DOCUMENT_REPORTED = "DOCUMENT_REPORTED"
    PROVIDER_RETRIEVED = "PROVIDER_RETRIEVED"
    PRIMARY_SOURCE_VERIFIED = "PRIMARY_SOURCE_VERIFIED"
    DISPUTED = "DISPUTED"
    UNKNOWN = "UNKNOWN"


class SourceType(str, Enum):
    USER_NARRATIVE = "USER_NARRATIVE"
    USER_DOCUMENT = "USER_DOCUMENT"
    PRIMARY_AUTHORITY = "PRIMARY_AUTHORITY"
    PROVIDER_METADATA = "PROVIDER_METADATA"
    SECONDARY_SOURCE = "SECONDARY_SOURCE"
    REASONING_RECORD = "REASONING_RECORD"


class AssessmentStatus(str, Enum):
    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    UNVERIFIED = "UNVERIFIED"
    UNKNOWN = "UNKNOWN"
    NOT_AVAILABLE = "NOT_AVAILABLE"
    BLOCKED = "BLOCKED"
    CONTRADICTED = "CONTRADICTED"


class CompletenessStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    BLOCKED = "BLOCKED"


class ResearchDimension(str, Enum):
    JURISDICTION = "JURISDICTION"
    FACTS = "FACTS"
    PROCEDURAL_POSTURE = "PROCEDURAL_POSTURE"
    CONTROLLING_AUTHORITY = "CONTROLLING_AUTHORITY"
    GOVERNING_TEXT = "GOVERNING_TEXT"
    AUTHORITY_HIERARCHY = "AUTHORITY_HIERARCHY"
    ADVERSE_AUTHORITY = "ADVERSE_AUTHORITY"
    LIMITING_AUTHORITY = "LIMITING_AUTHORITY"
    QUOTE_VERIFICATION = "QUOTE_VERIFICATION"
    CURRENTNESS_TREATMENT = "CURRENTNESS_TREATMENT"
    APPLICATION = "APPLICATION"


class AuthorityQualificationStatus(str, Enum):
    RETRIEVED = "RETRIEVED"
    PROVISIONAL = "PROVISIONAL"
    QUALIFIED = "QUALIFIED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"


class FactEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fact_id: str
    statement: str
    epistemic_status: EpistemicStatus
    source_ids: tuple[str, ...] = ()
    materiality: str = "UNKNOWN"
    adverse_to_user_position: bool = False
    verification_limitations: tuple[str, ...] = ()


class SourceEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    source_type: SourceType
    locator: Optional[str] = None
    public: bool = False
    provenance: tuple[str, ...] = ()
    supports_fact_ids: tuple[str, ...] = ()
    epistemic_status: EpistemicStatus = EpistemicStatus.UNKNOWN
    limitations: tuple[str, ...] = ()


class DimensionAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    dimension: ResearchDimension
    status: CompletenessStatus
    basis: str
    evidence_ids: tuple[str, ...] = ()
    unresolved_questions: tuple[str, ...] = ()
    blocking_reason: Optional[str] = None

    @model_validator(mode="after")
    def blocked_has_reason(self) -> "DimensionAssessment":
        if self.status == CompletenessStatus.BLOCKED and not self.blocking_reason:
            raise ValueError("blocked research dimension requires a reason")
        return self


class ResearchCompleteness(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str = RESEARCH_QUALITY_CONTRACT
    schema_version: str = "1.0"
    assessment_id: str
    research_id: str
    dimensions: tuple[DimensionAssessment, ...]
    required_dimensions: tuple[ResearchDimension, ...]
    overall_status: CompletenessStatus
    stopping_rule_met: bool = False
    stop_basis: tuple[str, ...] = ()
    unresolved_dimensions: tuple[ResearchDimension, ...] = ()
    blocked_dimensions: tuple[ResearchDimension, ...] = ()

    @field_validator("contract")
    @classmethod
    def supported_contract(cls, value: str) -> str:
        if value != RESEARCH_QUALITY_CONTRACT:
            raise ValueError("unsupported ResearchQuality contract")
        return value

    @field_validator("schema_version")
    @classmethod
    def supported_version(cls, value: str) -> str:
        if value != "1.0":
            raise ValueError("unsupported ResearchQuality schema version")
        return value

    @model_validator(mode="after")
    def completeness_is_auditable(self) -> "ResearchCompleteness":
        if len({item.dimension for item in self.dimensions}) != len(self.dimensions):
            raise ValueError("research completeness cannot contain duplicate dimensions")
        if len(set(self.required_dimensions)) != len(self.required_dimensions):
            raise ValueError("required research dimensions must be unique")
        by_dimension = {item.dimension: item for item in self.dimensions}
        if any(dimension not in by_dimension for dimension in self.required_dimensions):
            raise ValueError("every required research dimension must be assessed")
        unresolved = tuple(
            dimension for dimension in self.required_dimensions
            if by_dimension[dimension].status != CompletenessStatus.COMPLETE
        )
        blocked = tuple(
            dimension for dimension in unresolved
            if by_dimension[dimension].status == CompletenessStatus.BLOCKED
        )
        if self.unresolved_dimensions != unresolved or self.blocked_dimensions != blocked:
            raise ValueError("research completeness status lists do not match dimension assessments")
        if self.overall_status == CompletenessStatus.COMPLETE:
            if any(by_dimension[dimension].status != CompletenessStatus.COMPLETE for dimension in self.required_dimensions):
                raise ValueError("research completeness cannot be complete with an incomplete required dimension")
            if not self.stopping_rule_met or not self.stop_basis:
                raise ValueError("complete research requires an explicit stopping basis")
        return self


class AuthorityQualification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    authority_id: str
    source_id: Optional[str] = None
    retrieval: AssessmentStatus = AssessmentStatus.UNKNOWN
    identity: AssessmentStatus = AssessmentStatus.UNKNOWN
    jurisdiction: AssessmentStatus = AssessmentStatus.UNKNOWN
    hierarchy: AssessmentStatus = AssessmentStatus.UNKNOWN
    opinion_voice: AssessmentStatus = AssessmentStatus.UNKNOWN
    procedural_fit: AssessmentStatus = AssessmentStatus.UNKNOWN
    quote_verification: AssessmentStatus = AssessmentStatus.NOT_AVAILABLE
    currentness: AssessmentStatus = AssessmentStatus.UNKNOWN
    treatment: AssessmentStatus = AssessmentStatus.UNKNOWN
    qualification_status: AuthorityQualificationStatus = AuthorityQualificationStatus.PROVISIONAL
    evidence_ids: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @model_validator(mode="after")
    def qualification_requires_all_dimensions(self) -> "AuthorityQualification":
        core = (self.retrieval, self.identity, self.jurisdiction, self.hierarchy, self.opinion_voice, self.procedural_fit)
        if self.qualification_status == AuthorityQualificationStatus.QUALIFIED:
            if any(status != AssessmentStatus.VERIFIED for status in core):
                raise ValueError("qualified authority requires verified identity, jurisdiction, hierarchy, voice, and fit")
            if self.quote_verification != AssessmentStatus.VERIFIED or self.currentness != AssessmentStatus.VERIFIED or self.treatment != AssessmentStatus.VERIFIED:
                raise ValueError("qualified authority requires verified quote, currentness, and treatment dimensions")
        if self.qualification_status == AuthorityQualificationStatus.RETRIEVED and self.retrieval == AssessmentStatus.UNKNOWN:
            raise ValueError("retrieved authority must have retrieval evidence")
        return self


class ProfessionalFinding(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    finding_id: str
    statement: str
    status: EpistemicStatus
    evidence_ids: tuple[str, ...] = ()
    limitation: Optional[str] = None


class ProfessionalResearchRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    record_id: str
    research_id: str
    facts: tuple[FactEvidence, ...] = ()
    sources: tuple[SourceEvidence, ...] = ()
    authority_qualifications: tuple[AuthorityQualification, ...] = ()
    findings: tuple[ProfessionalFinding, ...] = ()
    completeness: ResearchCompleteness
    review_required: tuple[str, ...] = ()

    @model_validator(mode="after")
    def evidence_references_exist(self) -> "ProfessionalResearchRecord":
        if self.completeness.research_id != self.research_id:
            raise ValueError("completeness research_id does not match professional record")
        fact_ids = {fact.fact_id for fact in self.facts}
        source_ids = {source.source_id for source in self.sources}
        if any(source_id not in source_ids for fact in self.facts for source_id in fact.source_ids):
            raise ValueError("fact references unknown source evidence")
        if any(fact_id not in fact_ids for source in self.sources for fact_id in source.supports_fact_ids):
            raise ValueError("source references unknown fact evidence")
        evidence_ids = fact_ids | source_ids
        for finding in self.findings:
            if not set(finding.evidence_ids).issubset(evidence_ids):
                raise ValueError("finding references unknown evidence")
        return self


class NonLawyerGuidedExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    explanation_id: str
    professional_record_id: str
    user_summary: str
    reported_facts: tuple[str, ...] = ()
    independently_verified_findings: tuple[str, ...] = ()
    unresolved_or_disputed: tuple[str, ...] = ()
    why_clarification_matters: tuple[str, ...] = ()
    next_research_steps: tuple[str, ...] = ()
    research_standard_note: str = "The explanation is simplified for readability; the underlying research standard is unchanged."


def assess_completeness(
    assessment_id: str,
    research_id: str,
    dimensions: tuple[DimensionAssessment, ...],
    *,
    required_dimensions: tuple[ResearchDimension, ...] = (
        ResearchDimension.JURISDICTION,
        ResearchDimension.FACTS,
        ResearchDimension.PROCEDURAL_POSTURE,
        ResearchDimension.CONTROLLING_AUTHORITY,
        ResearchDimension.GOVERNING_TEXT,
        ResearchDimension.AUTHORITY_HIERARCHY,
        ResearchDimension.ADVERSE_AUTHORITY,
        ResearchDimension.LIMITING_AUTHORITY,
        ResearchDimension.QUOTE_VERIFICATION,
        ResearchDimension.CURRENTNESS_TREATMENT,
        ResearchDimension.APPLICATION,
    ),
) -> ResearchCompleteness:
    by_dimension = {item.dimension: item for item in dimensions}
    missing = tuple(
        DimensionAssessment(
            dimension=dimension, status=CompletenessStatus.BLOCKED,
            basis="No assessment was supplied.", blocking_reason="dimension was not assessed",
        )
        for dimension in required_dimensions if dimension not in by_dimension
    )
    complete_dimensions = dimensions + missing
    by_dimension = {item.dimension: item for item in complete_dimensions}
    statuses = [by_dimension[dimension].status for dimension in required_dimensions]
    if all(status == CompletenessStatus.COMPLETE for status in statuses):
        overall = CompletenessStatus.COMPLETE
    elif all(status in {CompletenessStatus.UNKNOWN, CompletenessStatus.NOT_STARTED} for status in statuses):
        overall = CompletenessStatus.UNKNOWN
    elif any(status == CompletenessStatus.BLOCKED for status in statuses) and not any(status == CompletenessStatus.COMPLETE for status in statuses):
        overall = CompletenessStatus.BLOCKED
    else:
        overall = CompletenessStatus.PARTIAL
    unresolved = tuple(dimension for dimension in required_dimensions if by_dimension[dimension].status != CompletenessStatus.COMPLETE)
    blocked = tuple(dimension for dimension in unresolved if by_dimension[dimension].status == CompletenessStatus.BLOCKED)
    return ResearchCompleteness(
        assessment_id=assessment_id, research_id=research_id, dimensions=complete_dimensions,
        required_dimensions=required_dimensions, overall_status=overall,
        stopping_rule_met=overall == CompletenessStatus.COMPLETE,
        stop_basis=("All required research dimensions are complete and auditable.",) if overall == CompletenessStatus.COMPLETE else (),
        unresolved_dimensions=unresolved, blocked_dimensions=blocked,
    )


def to_non_lawyer_explanation(
    record: ProfessionalResearchRecord,
    *,
    explanation_id: str,
    user_summary: str,
) -> NonLawyerGuidedExplanation:
    reported = tuple(fact.statement for fact in record.facts if fact.epistemic_status in {EpistemicStatus.USER_REPORTED, EpistemicStatus.DOCUMENT_REPORTED})
    verified = tuple(finding.statement for finding in record.findings if finding.status == EpistemicStatus.PRIMARY_SOURCE_VERIFIED)
    unresolved = tuple(
        finding.statement for finding in record.findings
        if finding.status in {EpistemicStatus.INFERRED, EpistemicStatus.DISPUTED, EpistemicStatus.UNKNOWN}
    )
    dimension_status = {item.dimension: item.status for item in record.completeness.dimensions}
    unresolved += tuple(
        f"{dimension.value} remains {dimension_status[dimension].value}."
        for dimension in record.completeness.unresolved_dimensions
    )
    return NonLawyerGuidedExplanation(
        explanation_id=explanation_id, professional_record_id=record.record_id,
        user_summary=user_summary, reported_facts=reported,
        independently_verified_findings=verified, unresolved_or_disputed=unresolved,
        why_clarification_matters=tuple(
            question for dimension in record.completeness.dimensions for question in dimension.unresolved_questions
        ),
        next_research_steps=("Confirm the unresolved research dimensions before drawing a legal conclusion.",),
    )
