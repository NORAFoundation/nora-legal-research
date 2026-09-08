"""Canonical V1 research contracts, state machines, and authority firewall.

Implements core architectural invariants:
- User-proposed theories are hypotheses, not conclusions.
- Primary controlling authority outranks semantic similarity.
- Unverified external data or private evidence cannot satisfy primary authority gates.
- Research coverage is multidimensional, not a win probability.
- War game evaluations are multi-sided, not one-sided critique theater.
- Citations require passage verification to establish propositions.
- Strict state-machine transitions prevent unearned credibility leaps.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


CANONICAL_RESEARCH_CONTRACT = "nora.legal-research/CanonicalResearch/1.0"


class AuthorityFirewallClassification(str, Enum):
    """Authority and evidence tiers for machine-enforceable security and provenance."""
    PRIMARY_AUTHORITY = "PRIMARY_AUTHORITY"
    PERSUASIVE_AUTHORITY = "PERSUASIVE_AUTHORITY"
    EXPLANATORY = "EXPLANATORY"
    USER_EVIDENCE = "USER_EVIDENCE"
    UNVERIFIED_EXTERNAL = "UNVERIFIED_EXTERNAL"


class LegalTheoryState(str, Enum):
    """Graduated lifecycle states for legal theories."""
    USER_PROPOSED = "USER_PROPOSED"
    DISCOVERED = "DISCOVERED"
    HYPOTHESIS = "HYPOTHESIS"
    RESEARCH_SUPPORTED = "RESEARCH_SUPPORTED"
    ADVERSELY_TESTED = "ADVERSELY_TESTED"
    STRONG = "STRONG"
    RELIED_UPON = "RELIED_UPON"
    REJECTED = "REJECTED"


class AuthorityQualificationState(str, Enum):
    """Graduated lifecycle states for legal authority."""
    DISCOVERED = "DISCOVERED"
    CANDIDATE = "CANDIDATE"
    IDENTITY_VERIFIED = "IDENTITY_VERIFIED"
    JURISDICTION_QUALIFIED = "JURISDICTION_QUALIFIED"
    HIERARCHY_QUALIFIED = "HIERARCHY_QUALIFIED"
    PASSAGE_VERIFIED = "PASSAGE_VERIFIED"
    CURRENTNESS_CHECKED = "CURRENTNESS_CHECKED"
    TREATMENT_ASSESSED = "TREATMENT_ASSESSED"
    RELIED_UPON = "RELIED_UPON"


class MatterScope(BaseModel):
    """Privacy and matter isolation scope separating private user matter from public law."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    user_scope_id: str
    matter_scope_id: str
    source_scope_id: str
    is_public_law_data: bool = False

    @field_validator("user_scope_id", "matter_scope_id", "source_scope_id")
    @classmethod
    def non_empty_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Scope identifiers must be non-empty strings")
        return v

    def assert_same_matter(self, other: "MatterScope") -> None:
        """Enforces that research artifacts do not contaminate across distinct user matters."""
        if not self.is_public_law_data and not other.is_public_law_data:
            if self.user_scope_id != other.user_scope_id or self.matter_scope_id != other.matter_scope_id:
                raise ValueError(
                    f"Cross-matter contamination detected between matter {self.matter_scope_id} "
                    f"and matter {other.matter_scope_id}"
                )


class ProceduralAlert(BaseModel):
    """Detected procedural deadlines and urgency alerts."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    alert_id: str
    event: str
    date_or_deadline: Optional[str] = None
    jurisdiction: str
    source_evidence_ids: tuple[str, ...] = ()
    confidence: float
    consequence: str
    verification_state: str = "DETECTED_UNVERIFIED"  # DETECTED_UNVERIFIED, VERIFIED_LEGAL_DEADLINE, DISPUTED
    urgency: str = "HIGH"  # CRITICAL, HIGH, MEDIUM, LOW
    notes: str = "Possible deadline detected; not yet legally verified."

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
        return v


class LegalTheory(BaseModel):
    """A legal theory tracking user proposals through adversarial verification."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    theory_id: str
    statement: str
    issue_id: str
    state: LegalTheoryState = LegalTheoryState.USER_PROPOSED
    source_concept_id: Optional[str] = None
    supporting_evidence_ids: tuple[str, ...] = ()
    adverse_testing_ids: tuple[str, ...] = ()
    rationale: str = ""

    def advance(
        self,
        target_state: LegalTheoryState,
        *,
        evidence_ids: tuple[str, ...] = (),
        rationale: str = "",
    ) -> "LegalTheory":
        """Strict state transition rules enforcing research discipline."""
        current = self.state

        # Invariant: USER_PROPOSED cannot leap directly to STRONG or RELIED_UPON
        if current == LegalTheoryState.USER_PROPOSED:
            if target_state in {LegalTheoryState.STRONG, LegalTheoryState.RELIED_UPON}:
                raise ValueError(
                    f"Illegal transition: {current.value} cannot leap directly to {target_state.value} "
                    "without research support and adverse testing."
                )
            if target_state not in {LegalTheoryState.HYPOTHESIS, LegalTheoryState.DISCOVERED, LegalTheoryState.REJECTED}:
                raise ValueError(f"Illegal transition from {current.value} to {target_state.value}")

        if current == LegalTheoryState.HYPOTHESIS:
            if target_state in {LegalTheoryState.STRONG, LegalTheoryState.RELIED_UPON}:
                raise ValueError(
                    f"Illegal transition: {current.value} must be RESEARCH_SUPPORTED and ADVERSELY_TESTED "
                    "before reaching STRONG or RELIED_UPON."
                )
            if target_state not in {LegalTheoryState.RESEARCH_SUPPORTED, LegalTheoryState.REJECTED}:
                raise ValueError(f"Illegal transition from {current.value} to {target_state.value}")

        if current == LegalTheoryState.RESEARCH_SUPPORTED:
            if target_state == LegalTheoryState.RELIED_UPON:
                raise ValueError(
                    f"Illegal transition: {current.value} must be ADVERSELY_TESTED and STRONG before RELIED_UPON."
                )
            if target_state not in {LegalTheoryState.ADVERSELY_TESTED, LegalTheoryState.REJECTED}:
                raise ValueError(f"Illegal transition from {current.value} to {target_state.value}")

        if current == LegalTheoryState.ADVERSELY_TESTED:
            if target_state not in {LegalTheoryState.STRONG, LegalTheoryState.REJECTED}:
                raise ValueError(f"Illegal transition from {current.value} to {target_state.value}")

        if current == LegalTheoryState.STRONG:
            if target_state not in {LegalTheoryState.RELIED_UPON, LegalTheoryState.REJECTED}:
                raise ValueError(f"Illegal transition from {current.value} to {target_state.value}")

        # Accumulate evidence
        new_supporting = tuple(set(self.supporting_evidence_ids + evidence_ids))
        new_adverse = self.adverse_testing_ids
        if target_state == LegalTheoryState.ADVERSELY_TESTED:
            new_adverse = tuple(set(self.adverse_testing_ids + evidence_ids))

        return LegalTheory(
            theory_id=self.theory_id,
            statement=self.statement,
            issue_id=self.issue_id,
            state=target_state,
            source_concept_id=self.source_concept_id,
            supporting_evidence_ids=new_supporting,
            adverse_testing_ids=new_adverse,
            rationale=rationale or self.rationale,
        )


class AuthorityQualificationLifecycle(BaseModel):
    """Enforces strict graduation of retrieved legal citations before reliance."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    authority_id: str
    citation_text: str
    classification: AuthorityFirewallClassification
    state: AuthorityQualificationState = AuthorityQualificationState.DISCOVERED
    pinpoint_passage: Optional[str] = None
    currentness_checked: bool = False
    negative_treatment: Optional[str] = None
    verification_notes: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_lifecycle_invariants(self) -> "AuthorityQualificationLifecycle":
        # Invariant: Only PRIMARY_AUTHORITY or PERSUASIVE_AUTHORITY can be RELIED_UPON as legal authority
        if self.state == AuthorityQualificationState.RELIED_UPON:
            if self.classification in {
                AuthorityFirewallClassification.USER_EVIDENCE,
                AuthorityFirewallClassification.UNVERIFIED_EXTERNAL,
                AuthorityFirewallClassification.EXPLANATORY,
            }:
                raise ValueError(
                    f"Firewall violation: {self.classification.value} cannot be RELIED_UPON as controlling authority"
                )
            if not self.pinpoint_passage:
                raise ValueError("Authority cannot be RELIED_UPON without a verified pinpoint passage")
            if not self.currentness_checked:
                raise ValueError("Authority cannot be RELIED_UPON without currentness verification")
            if self.negative_treatment and "overruled" in self.negative_treatment.lower():
                raise ValueError("Overruled authority cannot be RELIED_UPON as good law")

        return self

    def advance(
        self,
        target_state: AuthorityQualificationState,
        *,
        pinpoint_passage: Optional[str] = None,
        currentness_checked: Optional[bool] = None,
        negative_treatment: Optional[str] = None,
        note: str = "",
    ) -> "AuthorityQualificationLifecycle":
        """Advances authority along its qualification path."""
        valid_successors = {
            AuthorityQualificationState.DISCOVERED: {AuthorityQualificationState.CANDIDATE},
            AuthorityQualificationState.CANDIDATE: {AuthorityQualificationState.IDENTITY_VERIFIED},
            AuthorityQualificationState.IDENTITY_VERIFIED: {AuthorityQualificationState.JURISDICTION_QUALIFIED},
            AuthorityQualificationState.JURISDICTION_QUALIFIED: {AuthorityQualificationState.HIERARCHY_QUALIFIED},
            AuthorityQualificationState.HIERARCHY_QUALIFIED: {AuthorityQualificationState.PASSAGE_VERIFIED},
            AuthorityQualificationState.PASSAGE_VERIFIED: {AuthorityQualificationState.CURRENTNESS_CHECKED},
            AuthorityQualificationState.CURRENTNESS_CHECKED: {AuthorityQualificationState.TREATMENT_ASSESSED},
            AuthorityQualificationState.TREATMENT_ASSESSED: {AuthorityQualificationState.RELIED_UPON},
        }

        expected = valid_successors.get(self.state, set())
        if target_state not in expected:
            raise ValueError(
                f"Illegal authority lifecycle transition from {self.state.value} to {target_state.value}. "
                f"Expected one of: {[s.value for s in expected]}"
            )

        new_notes = self.verification_notes + ((note,) if note else ())
        return AuthorityQualificationLifecycle(
            authority_id=self.authority_id,
            citation_text=self.citation_text,
            classification=self.classification,
            state=target_state,
            pinpoint_passage=pinpoint_passage or self.pinpoint_passage,
            currentness_checked=currentness_checked if currentness_checked is not None else self.currentness_checked,
            negative_treatment=negative_treatment or self.negative_treatment,
            verification_notes=new_notes,
        )


class LegalProposition(BaseModel):
    """A specific proposition of law tied to verified supporting passages and adverse authority."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    proposition_id: str
    exact_proposition: str
    supporting_authorities: tuple[str, ...]
    supporting_passages: tuple[str, ...]
    adverse_authorities: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    currentness_status: str = "VERIFIED_CURRENT"
    verification_state: str = "PASSAGE_VERIFIED"

    @model_validator(mode="after")
    def proposition_requires_passages(self) -> "LegalProposition":
        if not self.supporting_authorities:
            raise ValueError("Legal proposition must have at least one supporting authority")
        if not self.supporting_passages:
            raise ValueError(
                "A citation alone does not prove a proposition: at least one supporting passage is required."
            )
        return self


class CurrentnessReceipt(BaseModel):
    """Audit receipt recording date and sources checked for temporal currency."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    receipt_id: str
    checked_through_date: str
    sources_checked: tuple[str, ...]
    later_authorities: tuple[str, ...] = ()
    statutory_or_rule_changes: tuple[str, ...] = ()
    treatment_candidates: tuple[str, ...] = ()
    unresolved_uncertainty: tuple[str, ...] = ()

    @model_validator(mode="after")
    def receipt_has_sources(self) -> "CurrentnessReceipt":
        if not self.sources_checked:
            raise ValueError("Currentness receipt must list sources checked; static corpora cannot establish currentness")
        return self


class ResearchCoverage(BaseModel):
    """Dimensional research coverage metrics across 11 distinct dimensions. Never a win probability."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    jurisdiction: float
    governing_text: float
    controlling_authority: float
    fact_analogies: float
    procedure: float
    adverse_research: float
    local_rules: float
    currentness: float
    treatment: float
    quote_verification: float
    evidence_application: float

    @field_validator(
        "jurisdiction",
        "governing_text",
        "controlling_authority",
        "fact_analogies",
        "procedure",
        "adverse_research",
        "local_rules",
        "currentness",
        "treatment",
        "quote_verification",
        "evidence_application",
    )
    @classmethod
    def validate_dimension_range(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Coverage dimensions must be calibrated between 0.0 and 1.0")
        return v

    def is_complete_research(self) -> bool:
        """Strict completeness rule: favorable research without adverse research is incomplete."""
        if self.adverse_research < 0.5:
            return False
        if self.controlling_authority < 0.5 or self.governing_text < 0.5:
            return False
        if self.currentness < 0.5 or self.quote_verification < 0.5:
            return False
        return True


class WarGameResult(BaseModel):
    """Multi-perspective stress-test results across advocate and opposing viewpoints."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    wargame_id: str
    target_objective: str
    advocate_arguments: tuple[str, ...]
    opposition_arguments: tuple[str, ...]
    conflicts: tuple[str, ...]
    rebuttals: tuple[str, ...]
    survived_strongly: tuple[str, ...] = ()
    survived_conditionally: tuple[str, ...] = ()
    failed: tuple[str, ...] = ()
    unresolved: tuple[str, ...] = ()
    evidence_needed: tuple[str, ...] = ()
    research_needed: tuple[str, ...] = ()

    @model_validator(mode="after")
    def validate_multi_sided_inquiry(self) -> "WarGameResult":
        # Invariant: War Game cannot be one-sided critique theater
        if not self.opposition_arguments:
            raise ValueError("WarGameResult must assess opposition arguments; one-sided analysis is invalid")
        if not self.advocate_arguments:
            raise ValueError("WarGameResult must assess advocate arguments")
        return self


class ResearchPackage(BaseModel):
    """Portable, durable, inspectable research artifact combining all research findings."""
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str = CANONICAL_RESEARCH_CONTRACT
    schema_version: str = "1.0"
    package_id: str
    matter_scope: MatterScope
    question_or_objective: str
    jurisdiction_and_posture: str
    procedural_alerts: tuple[ProceduralAlert, ...] = ()
    theories: tuple[LegalTheory, ...] = ()
    issue_map: tuple[str, ...] = ()
    governing_law: tuple[str, ...] = ()
    verified_propositions: tuple[LegalProposition, ...] = ()
    relied_upon_authorities: tuple[str, ...] = ()
    adverse_authorities: tuple[str, ...] = ()
    currentness_receipt: CurrentnessReceipt
    wargame_result: WarGameResult
    coverage: ResearchCoverage
    provenance: tuple[str, ...] = ()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("contract")
    @classmethod
    def validate_contract(cls, v: str) -> str:
        if v != CANONICAL_RESEARCH_CONTRACT:
            raise ValueError(f"unsupported ResearchPackage contract: {v}")
        return v

    @model_validator(mode="after")
    def validate_package_invariants(self) -> "ResearchPackage":
        # Invariant: Favorable research without adverse research is incomplete
        if self.relied_upon_authorities and not self.adverse_authorities:
            if not self.wargame_result.opposition_arguments:
                raise ValueError("ResearchPackage cannot claim relied-upon authority without adverse research")
        return self
