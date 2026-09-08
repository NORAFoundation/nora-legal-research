"""Privacy-preserving compilation of lay narratives into research plans.

This module intentionally produces separate derived artifacts.  The narrative
is evidence of what a user reported, not a legal query or a legal conclusion.
Only the bounded, abstract ``AuthorityResearchRequest`` objects produced by a
``ResearchPlan`` may cross a public provider boundary.
"""

from __future__ import annotations

import hashlib
import re
from enum import Enum
from typing import Iterable, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .provider_contract import AuthorityResearchRequest, PROVIDER_CONTRACT_VERSION
from .people_to_law import (
    PEOPLE_TO_LAW_CONTRACT,
    PeopleToLawConcept,
    PeopleToLawOntology,
    build_canonical_ontology,
)
from .jurisdiction_data import build_canonical_registry
from .jurisdiction_registry import AuthorityFamily, JurisdictionSourceRegistry


NARRATIVE_INTAKE_CONTRACT = "nora.legal-research/NarrativeResearchIntake/1.0"
RESEARCH_INTENT_CONTRACT = "nora.legal-research/ResearchIntent/1.0"
RESEARCH_PLAN_CONTRACT = "nora.legal-research/ResearchPlan/1.0"
RESEARCH_QUALITY_ASSESSMENT_CONTRACT = "nora.legal-research/ResearchQualityAssessment/1.0"
GENERAL_LANGUAGE_CARTRIDGE = "nora.general-lay-language/1.0"


class ResolutionState(str, Enum):
    KNOWN = "KNOWN"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    CONFLICTING = "CONFLICTING"


class IssueStatus(str, Enum):
    ISSUE_HYPOTHESIS = "ISSUE_HYPOTHESIS"
    VERIFIED_RESEARCH_ISSUE = "VERIFIED_RESEARCH_ISSUE"
    REJECTED_ISSUE = "REJECTED_ISSUE"
    UNRESOLVED_ISSUE = "UNRESOLVED_ISSUE"


class EvidenceCategory(str, Enum):
    USER_ASSERTED_FACT = "USER_ASSERTED_FACT"
    USER_QUESTION = "USER_QUESTION"
    USER_INTERPRETATION = "USER_INTERPRETATION"
    UNKNOWN_OR_AMBIGUOUS_FACT = "UNKNOWN_OR_AMBIGUOUS_FACT"
    DOCUMENT_REFERENCE = "DOCUMENT_REFERENCE"
    DATE = "DATE"
    PERSON_OR_ENTITY = "PERSON_OR_ENTITY"
    LOCATION = "LOCATION"
    COURT_OR_AGENCY = "COURT_OR_AGENCY"
    PROCEDURAL_EVENT = "PROCEDURAL_EVENT"


class QueryClass(str, Enum):
    DOCTRINAL_QUERY = "DOCTRINAL_QUERY"
    CONTROLLING_AUTHORITY_QUERY = "CONTROLLING_AUTHORITY_QUERY"
    STATUTE_RULE_QUERY = "STATUTE_RULE_QUERY"
    FACT_PATTERN_QUERY = "FACT_PATTERN_QUERY"
    PROCEDURAL_POSTURE_QUERY = "PROCEDURAL_POSTURE_QUERY"
    ADVERSE_AUTHORITY_QUERY = "ADVERSE_AUTHORITY_QUERY"
    LIMITING_AUTHORITY_QUERY = "LIMITING_AUTHORITY_QUERY"
    CURRENTNESS_TREATMENT_QUERY = "CURRENTNESS_TREATMENT_QUERY"
    CITATION_GRAPH_QUERY = "CITATION_GRAPH_QUERY"
    DEFINITION_TERMINOLOGY_QUERY = "DEFINITION_TERMINOLOGY_QUERY"


class RetrievalMode(str, Enum):
    DISCOVERY = "DISCOVERY"
    QUALIFICATION = "QUALIFICATION"


class QualityGateStatus(str, Enum):
    PASS = "PASS"
    PASS_FIXTURE_ONLY = "PASS_FIXTURE_ONLY"
    BLOCKED_DEPENDENCY = "BLOCKED_DEPENDENCY"
    NOT_STARTED = "NOT_STARTED"


class NarrativeFact(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    fact_id: str
    text: str
    category: EvidenceCategory = EvidenceCategory.USER_ASSERTED_FACT
    state: ResolutionState = ResolutionState.KNOWN
    source_span: Optional[str] = None
    adverse_signal: bool = False
    materially_relevant: bool = False


class ExtractedDate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    date_id: str
    text: str
    normalized_date: Optional[str] = None
    state: ResolutionState = ResolutionState.KNOWN
    legally_material: bool = False
    identity_sensitive: bool = False


class EntityReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    entity_id: str
    text: str
    entity_type: str
    private: bool = True


class DocumentReference(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reference_id: str
    description: str
    reference_type: str
    understood: bool = False


class ProceduralEvent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    event_id: str
    event_type: str
    description: str
    state: ResolutionState = ResolutionState.INFERRED
    fact_id: Optional[str] = None
    legally_material: bool = True


class NarrativeResearchIntake(BaseModel):
    """Raw intake plus extracted evidence categories; never provider-bound."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str = NARRATIVE_INTAKE_CONTRACT
    schema_version: str = "1.0"
    intake_id: str
    narrative: str
    user_asserted_facts: tuple[NarrativeFact, ...] = ()
    user_questions: tuple[str, ...] = ()
    user_interpretations: tuple[str, ...] = ()
    unknown_or_ambiguous_facts: tuple[NarrativeFact, ...] = ()
    document_references: tuple[DocumentReference, ...] = ()
    dates: tuple[ExtractedDate, ...] = ()
    people_or_entities: tuple[EntityReference, ...] = ()
    locations: tuple[EntityReference, ...] = ()
    courts_or_agencies: tuple[EntityReference, ...] = ()
    procedural_events: tuple[ProceduralEvent, ...] = ()

    @field_validator("contract")
    @classmethod
    def supported_contract(cls, value: str) -> str:
        if value != NARRATIVE_INTAKE_CONTRACT:
            raise ValueError("unsupported NarrativeResearchIntake contract")
        return value

    @field_validator("schema_version")
    @classmethod
    def supported_version(cls, value: str) -> str:
        if value != "1.0":
            raise ValueError("unsupported NarrativeResearchIntake schema version")
        return value

    @field_validator("intake_id")
    @classmethod
    def bounded_id(cls, value: str) -> str:
        if not value or len(value) > 128 or any(token in value for token in ("@", "\\", "/Users/", "Dropbox/", "../")):
            raise ValueError("intake_id must be a bounded non-private identifier")
        return value

    @field_validator("narrative")
    @classmethod
    def bounded_narrative(cls, value: str) -> str:
        if not value.strip() or len(value) > 100_000 or "\x00" in value:
            raise ValueError("narrative must be bounded non-empty text")
        return value

    @property
    def narrative_sha256(self) -> str:
        return hashlib.sha256(self.narrative.encode("utf-8")).hexdigest()


class ResolvedValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: Optional[str] = None
    state: ResolutionState = ResolutionState.UNKNOWN
    evidence_ids: tuple[str, ...] = ()
    alternatives: tuple[str, ...] = ()

    @model_validator(mode="after")
    def state_matches_value(self) -> "ResolvedValue":
        if self.state == ResolutionState.UNKNOWN and self.value is not None:
            raise ValueError("unknown resolution cannot carry a value")
        if self.state == ResolutionState.CONFLICTING and len(self.alternatives) < 2:
            raise ValueError("conflicting resolution requires alternatives")
        return self


class JurisdictionResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    country: ResolvedValue = Field(default_factory=ResolvedValue)
    state: ResolvedValue = Field(default_factory=ResolvedValue)
    county: ResolvedValue = Field(default_factory=ResolvedValue)
    court_system: ResolvedValue = Field(default_factory=ResolvedValue)
    matter_type: ResolvedValue = Field(default_factory=ResolvedValue)
    trial_appellate_posture: ResolvedValue = Field(default_factory=ResolvedValue)
    relevant_event_date: ResolvedValue = Field(default_factory=ResolvedValue)


class OntologyMapping(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    concept_id: str
    label: str
    domain: str
    subdomain: str
    procedure_or_substance: str
    issue: str
    subissue: str
    lay_triggers: tuple[str, ...]
    legal_terms: tuple[str, ...]
    source: str = GENERAL_LANGUAGE_CARTRIDGE
    version: str = "1.0"
    confidence: float = 0.5
    jurisdiction_applicability: tuple[str, ...] = ("GENERAL",)


class IssueHypothesis(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    issue_id: str
    status: IssueStatus = IssueStatus.ISSUE_HYPOTHESIS
    concept_id: str
    label: str
    domain: str
    subdomain: str
    procedure_or_substance: str
    issue: str
    subissue: str
    confidence: float
    why_inferred: str
    trigger_fact_ids: tuple[str, ...] = ()
    context_needed: tuple[str, ...] = ()
    legal_terms: tuple[str, ...] = ()
    jurisdiction_sensitive: bool = True
    ontology_source: str = GENERAL_LANGUAGE_CARTRIDGE
    ontology_version: str = "1.0"

    @field_validator("confidence")
    @classmethod
    def bounded_confidence(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("confidence must be between 0 and 1")
        return value


class ResearchQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: str
    issue_id: str
    question: str
    why_needed: str
    remains_hypothetical: bool = True


class ClarificationQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    question_id: str
    question: str
    information_needed: str
    expected_research_impact: str
    priority: str = "HIGH"


class GoverningSourceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_id: str
    description: str
    source_kind: str
    issue_id: Optional[str] = None
    status: ResolutionState = ResolutionState.INFERRED
    official_status: Optional[str] = None
    authority_level: Optional[str] = None
    currentness_capability: Optional[str] = None


class ResearchIntent(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str = RESEARCH_INTENT_CONTRACT
    schema_version: str = "1.0"
    intent_id: str
    user_goal: str
    user_problem_summary: str
    jurisdiction: JurisdictionResolution
    jurisdiction_state: ResolvedValue
    procedural_posture: ResolvedValue
    matter_type: ResolvedValue
    issue_hypotheses: tuple[IssueHypothesis, ...] = ()
    important_dates: tuple[ExtractedDate, ...] = ()
    known_facts: tuple[NarrativeFact, ...] = ()
    inferred_facts: tuple[NarrativeFact, ...] = ()
    unknown_facts: tuple[NarrativeFact, ...] = ()
    disputed_facts: tuple[NarrativeFact, ...] = ()
    potential_governing_sources: tuple[GoverningSourceCandidate, ...] = ()
    research_questions: tuple[ResearchQuestion, ...] = ()
    clarifications_needed: tuple[ClarificationQuestion, ...] = ()
    urgency_flags: tuple[str, ...] = ()
    deadline_questions: tuple[str, ...] = ()
    research_constraints: tuple[str, ...] = ()
    source_narrative_sha256: str

    @field_validator("contract")
    @classmethod
    def supported_contract(cls, value: str) -> str:
        if value != RESEARCH_INTENT_CONTRACT:
            raise ValueError("unsupported ResearchIntent contract")
        return value

    @field_validator("schema_version")
    @classmethod
    def supported_version(cls, value: str) -> str:
        if value != "1.0":
            raise ValueError("unsupported ResearchIntent schema version")
        return value


class ResearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    query_id: str
    issue_id: str
    query_class: QueryClass
    retrieval_mode: RetrievalMode
    why_this_query_exists: str
    jurisdiction_constraints: tuple[str, ...] = ()
    court_hierarchy_constraints: tuple[str, ...] = ()
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    capabilities_required: tuple[str, ...] = ()
    query_variants: tuple[str, ...]
    target_proposition: str


class ResearchPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str = RESEARCH_PLAN_CONTRACT
    schema_version: str = "1.0"
    plan_id: str
    intent_id: str
    source_narrative_sha256: str
    queries: tuple[ResearchQuery, ...] = ()
    blocked_dimensions: tuple[str, ...] = ()
    provisional_assumptions: tuple[str, ...] = ()
    stopping_conditions: tuple[str, ...] = (
        "controlling authority identified or explicitly blocked",
        "adverse and limiting authority searches completed or explicitly blocked",
        "authority hierarchy and procedural fit checked",
        "currentness/treatment checked or explicitly unavailable",
        "material conflicts and uncertainties surfaced",
    )
    research_budget: int = 24

    @field_validator("contract")
    @classmethod
    def supported_contract(cls, value: str) -> str:
        if value != RESEARCH_PLAN_CONTRACT:
            raise ValueError("unsupported ResearchPlan contract")
        return value

    @field_validator("schema_version")
    @classmethod
    def supported_version(cls, value: str) -> str:
        if value != "1.0":
            raise ValueError("unsupported ResearchPlan schema version")
        return value

    @field_validator("research_budget")
    @classmethod
    def bounded_budget(cls, value: int) -> int:
        if value < 1 or value > 100:
            raise ValueError("research budget is out of bounds")
        return value

    def to_provider_requests(
        self,
        intent: ResearchIntent,
        *,
        research_id_prefix: str = "LAY-RESEARCH",
        provider_contract_version: int = PROVIDER_CONTRACT_VERSION,
    ) -> tuple[AuthorityResearchRequest, ...]:
        """Compile only abstract public requests; raw intake is unavailable here."""

        state = intent.jurisdiction_state
        if state.state not in {ResolutionState.KNOWN, ResolutionState.INFERRED} or not state.value:
            return ()

        requests: list[AuthorityResearchRequest] = []
        posture_known = intent.procedural_posture.state == ResolutionState.KNOWN
        for index, query in enumerate(self.queries[: self.research_budget], start=1):
            if query.retrieval_mode == RetrievalMode.QUALIFICATION and not posture_known:
                continue
            court_level = intent.jurisdiction.court_system.value or "unknown"
            requests.append(
                AuthorityResearchRequest(
                    provider_contract_version=provider_contract_version,
                    research_id=f"{research_id_prefix}-{index:03d}",
                    jurisdiction=state.value,
                    court_level=court_level,
                    doctrinal_issue=query.issue_id,
                    target_proposition=query.target_proposition,
                    query_variants=query.query_variants,
                    date_range="BOUNDED" if query.date_from or query.date_to else "ALL_AVAILABLE",
                    date_from=query.date_from,
                    date_to=query.date_to,
                    limit=8 if query.retrieval_mode == RetrievalMode.DISCOVERY else 6,
                    requested_capabilities=query.capabilities_required or ("search",),
                )
            )
        return tuple(requests)


class GuidedResearchExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    explanation_id: str
    translated_summary: str
    facts_treated_as_user_reported: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    clarifications_needed: tuple[str, ...] = ()
    transparency_notes: tuple[str, ...] = (
        "Issue labels are research hypotheses, not legal conclusions.",
        "User-reported facts are not independently verified by intake compilation.",
    )


class QualityGateResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    gate: str
    status: QualityGateStatus
    evidence: tuple[str, ...] = ()
    live_source_qualified: bool = False


class ResearchQualityAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str = RESEARCH_QUALITY_ASSESSMENT_CONTRACT
    schema_version: str = "1.0"
    assessment_id: str
    intent_id: str
    gates: tuple[QualityGateResult, ...] = ()
    unresolved_dimensions: tuple[str, ...] = ()
    same_source_standard_for_all_users: bool = True

    @field_validator("contract")
    @classmethod
    def supported_contract(cls, value: str) -> str:
        if value != RESEARCH_QUALITY_ASSESSMENT_CONTRACT:
            raise ValueError("unsupported ResearchQualityAssessment contract")
        return value

    @field_validator("schema_version")
    @classmethod
    def supported_version(cls, value: str) -> str:
        if value != "1.0":
            raise ValueError("unsupported ResearchQualityAssessment schema version")
        return value


class CompiledNarrativeResearch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    intake: NarrativeResearchIntake
    intent: ResearchIntent
    plan: ResearchPlan
    explanation: GuidedResearchExplanation
    quality: ResearchQualityAssessment

    def provider_requests(self, **kwargs: object) -> tuple[AuthorityResearchRequest, ...]:
        return self.plan.to_provider_requests(self.intent, **kwargs)


_STATE_ALIASES = {
    "alabama": "US-AL", "alaska": "US-AK", "arizona": "US-AZ", "arkansas": "US-AR",
    "california": "US-CA", "colorado": "US-CO", "connecticut": "US-CT", "florida": "US-FL",
    "georgia": "US-GA", "illinois": "US-IL", "indiana": "US-IN", "iowa": "US-IA",
    "kansas": "US-KS", "kentucky": "US-KY", "louisiana": "US-LA", "maine": "US-ME",
    "maryland": "US-MD", "massachusetts": "US-MA", "michigan": "US-MI", "minnesota": "US-MN",
    "mississippi": "US-MS", "missouri": "US-MO", "montana": "US-MT", "nebraska": "US-NE",
    "nevada": "US-NV", "new jersey": "US-NJ", "new mexico": "US-NM", "new york": "US-NY",
    "north carolina": "US-NC", "ohio": "US-OH", "oklahoma": "US-OK", "oregon": "US-OR",
    "pennsylvania": "US-PA", "south carolina": "US-SC", "tennessee": "US-TN", "texas": "US-TX",
    "utah": "US-UT", "virginia": "US-VA", "washington": "US-WA", "wisconsin": "US-WI",
    "wyoming": "US-WY", "district of columbia": "US-DC",
}

_MONTHS = {
    "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
    "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
}

_GENERAL_MAPPINGS = (
    OntologyMapping(
        concept_id="housing.self_help_lockout",
        label="landlord possession and self-help lockout",
        domain="housing", subdomain="possession", procedure_or_substance="substance",
        issue="self_help_lockout", subissue="removal_without_court_process",
        lay_triggers=("landlord", "changed the locks", "locked me out", "stuff outside", "evict"),
        legal_terms=("eviction", "self-help lockout", "possession without court order"),
    ),
    OntologyMapping(
        concept_id="procedure.notice_hearing",
        label="notice, service, and opportunity to be heard",
        domain="procedure", subdomain="notice", procedure_or_substance="procedure",
        issue="notice_service", subissue="hearing_notice_and_service",
        lay_triggers=("never told me", "notice", "hearing", "served", "didn't know about"),
        legal_terms=("notice", "service", "due process", "opportunity to be heard"),
    ),
    OntologyMapping(
        concept_id="evidence.health_information_disclosure",
        label="health-information disclosure and evidentiary use",
        domain="evidence", subdomain="privacy", procedure_or_substance="procedure",
        issue="health_information_evidence", subissue="disclosure_and_admissibility",
        lay_triggers=("hipaa", "medical records", "medical record", "health records"),
        legal_terms=("health information disclosure", "medical records evidence", "admissibility"),
    ),
    OntologyMapping(
        concept_id="procedure.due_process_fairness",
        label="procedural fairness and due process",
        domain="procedure", subdomain="fairness", procedure_or_substance="procedure",
        issue="due_process", subissue="notice_opportunity_and_prejudice",
        lay_triggers=("prosecutor", "in court", "whole case", "unfair"),
        legal_terms=("due process", "notice", "opportunity to be heard", "prejudice"),
    ),
    OntologyMapping(
        concept_id="juvenile.emergency_removal",
        label="emergency removal and temporary custody",
        domain="juvenile", subdomain="child_welfare", procedure_or_substance="procedure",
        issue="emergency_removal", subissue="temporary_custody_and_required_findings",
        lay_triggers=("took my child", "removed my child", "protective custody", "child welfare", "cps"),
        legal_terms=("emergency removal", "temporary custody", "protective custody"),
    ),
    OntologyMapping(
        concept_id="criminal.probation_violation_procedure",
        label="probation violation procedure and excuse",
        domain="criminal", subdomain="probation", procedure_or_substance="procedure",
        issue="probation_violation", subissue="notice_hearing_and_missed_requirement",
        lay_triggers=("probation officer", "probation", "missed appointment", "car broke down"),
        legal_terms=("probation violation procedure", "notice", "violation hearing"),
    ),
    OntologyMapping(
        concept_id="evidence.authentication_preservation",
        label="evidence admission, offer of proof, and preservation",
        domain="evidence", subdomain="admissibility", procedure_or_substance="procedure",
        issue="evidence_ruling", subissue="authentication_and_preservation",
        lay_triggers=("wouldn't look at my evidence", "would not look at my evidence", "evidence", "proof"),
        legal_terms=("admissibility", "authentication", "offer of proof", "preservation", "standard of review"),
    ),
    OntologyMapping(
        concept_id="criminal.speedy_trial",
        label="criminal delay and speedy-trial procedure",
        domain="criminal", subdomain="trial", procedure_or_substance="procedure",
        issue="speedy_trial", subissue="delay_and_prejudice",
        lay_triggers=("speedy trial", "trial was delayed", "kept me waiting", "jail for months"),
        legal_terms=("speedy trial", "delay", "prejudice"),
    ),
)


def _sentences(narrative: str) -> tuple[str, ...]:
    values = re.split(r"(?<=[.!?])\s+|\n+", narrative.strip())
    return tuple(value.strip() for value in values if value.strip())


def _has_any(text: str, terms: Iterable[str]) -> bool:
    lower = text.lower()
    return any(term in lower for term in terms)


def _stable_id(prefix: str, value: str, index: int = 0) -> str:
    digest = hashlib.sha256(value.encode("utf-8")).hexdigest()[:10]
    return f"{prefix}-{digest}-{index:03d}"


def _extract_dates(narrative: str) -> tuple[ExtractedDate, ...]:
    patterns = (
        r"\b(20\d{2}-\d{2}-\d{2})\b",
        r"\b(\d{1,2}/\d{1,2}/20\d{2})\b",
        r"\b((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:,\s*20\d{2})?)\b",
    )
    found: list[ExtractedDate] = []
    for index, match in enumerate(re.finditer("|".join(patterns), narrative, re.I), start=1):
        text = match.group(0)
        context = narrative[max(0, match.start() - 100): min(len(narrative), match.end() + 100)].lower()
        iso = text if re.fullmatch(r"20\d{2}-\d{2}-\d{2}", text) else None
        if re.fullmatch(r"\d{1,2}/\d{1,2}/20\d{2}", text):
            month, day, year = text.split("/")
            iso = f"{year}-{int(month):02d}-{int(day):02d}"
        month_match = re.fullmatch(r"([A-Za-z]+)\s+(\d{1,2})(?:,\s*(20\d{2}))?", text)
        if month_match and month_match.group(3):
            iso = f"{month_match.group(3)}-{_MONTHS[month_match.group(1).lower()]:02d}-{int(month_match.group(2)):02d}"
        material = _has_any(context, ("hearing", "notice", "filed", "deadline", "arrest", "removed", "lock", "trial", "appointment", "served"))
        identity_sensitive = _has_any(context, ("birthday", "born", "social security", "account"))
        found.append(ExtractedDate(
            date_id=f"DATE-{index:03d}", text=text, normalized_date=iso,
            legally_material=material, identity_sensitive=identity_sensitive,
        ))
    for relative in re.finditer(r"\b(yesterday|today|last\s+(?:week|month|tuesday|monday)|a few weeks ago|that day)\b", narrative, re.I):
        found.append(ExtractedDate(
            date_id=f"DATE-REL-{len(found) + 1:03d}", text=relative.group(1),
            state=ResolutionState.UNKNOWN, legally_material=True,
        ))
    return tuple(found)


def extract_narrative_intake(narrative: str, *, intake_id: str = "LAY-INTAKE-001") -> NarrativeResearchIntake:
    """Extract evidence categories without asserting legal meaning."""

    sentences = _sentences(narrative)
    questions = tuple(sentence for sentence in sentences if "?" in sentence or _has_any(sentence, ("what can i do", "what should i do", "can they", "is it legal")))
    interpretations = tuple(
        sentence for sentence in sentences
        if _has_any(sentence, ("hipaa", "violated", "illegal", "no right", "unconstitutional", "due process"))
    )
    facts: list[NarrativeFact] = []
    for index, sentence in enumerate(sentences, start=1):
        if sentence in questions:
            continue
        fact = NarrativeFact(
            fact_id=f"FACT-{index:03d}",
            text=sentence,
            category=EvidenceCategory.USER_INTERPRETATION if sentence in interpretations else EvidenceCategory.USER_ASSERTED_FACT,
            adverse_signal=_has_any(sentence, ("did receive notice", "i did get notice", "missed", "late", "admit", "even though")),
            materially_relevant=_has_any(sentence, ("notice", "hearing", "court", "judge", "deadline", "date", "removed", "lock", "probation", "evidence")),
        )
        facts.append(fact)
    unknowns: list[NarrativeFact] = []
    if not _STATE_ALIASES or not any(alias in narrative.lower() for alias in _STATE_ALIASES):
        unknowns.append(NarrativeFact(fact_id="UNKNOWN-JURISDICTION", text="The controlling state or country is not stated.", category=EvidenceCategory.UNKNOWN_OR_AMBIGUOUS_FACT, state=ResolutionState.UNKNOWN, materially_relevant=True))
    if not _has_any(narrative, ("appeal", "appealed", "trial court", "appellate", "pending hearing", "hearing date")):
        unknowns.append(NarrativeFact(fact_id="UNKNOWN-POSTURE", text="The procedural posture and pending status are unclear.", category=EvidenceCategory.UNKNOWN_OR_AMBIGUOUS_FACT, state=ResolutionState.UNKNOWN, materially_relevant=True))

    docs: list[DocumentReference] = []
    for index, (term, kind) in enumerate((("notice", "notice"), ("hearing", "hearing notice"), ("order", "court order"), ("letter", "letter"), ("records", "records"), ("paperwork", "paperwork")), start=1):
        if term in narrative.lower():
            docs.append(DocumentReference(reference_id=f"DOC-{index:03d}", description=f"User mentioned {term}.", reference_type=kind))

    entities: list[EntityReference] = []
    for index, value in enumerate(sorted(set(re.findall(r"\b(?:PRIVATE_[A-Z0-9_]+|[^\s@]+@[^\s@]+\.[^\s@]+)\b", narrative))), start=1):
        entities.append(EntityReference(entity_id=f"ENTITY-{index:03d}", text=value, entity_type="private_identifier", private=True))
    for index, value in enumerate(sorted(set(re.findall(r"\b[A-Z][a-z]+\s+[A-Z][a-z]+\b", narrative))), start=len(entities) + 1):
        entities.append(EntityReference(entity_id=f"ENTITY-{index:03d}", text=value, entity_type="person_or_entity", private=True))

    locations: list[EntityReference] = []
    for index, value in enumerate(sorted(set(re.findall(r"\b(?:[A-Z][a-z]+\s+){0,2}County\b|\b\d{1,5}\s+[^,.\n]+\s+(?:Street|St|Road|Rd|Avenue|Ave)\b", narrative))), start=1):
        locations.append(EntityReference(entity_id=f"LOCATION-{index:03d}", text=value, entity_type="location", private=True))

    officials = ("probation officer", "prosecutor", "judge", "landlord", "social services", "cps", "agency")
    courts = tuple(EntityReference(entity_id=f"COURT-{index:03d}", text=term, entity_type="court_or_agency", private=False) for index, term in enumerate(officials, start=1) if term in narrative.lower())

    events: list[ProceduralEvent] = []
    event_terms = (("notice", "notice"), ("hearing", "hearing"), ("arrest", "arrest"), ("removed", "removal"), ("changed the locks", "lockout"), ("probation", "probation"), ("filed", "filing"), ("appeal", "appeal"))
    for index, (term, kind) in enumerate(event_terms, start=1):
        if term in narrative.lower():
            fact_id = next((fact.fact_id for fact in facts if term in fact.text.lower()), None)
            events.append(ProceduralEvent(event_id=f"EVENT-{index:03d}", event_type=kind, description=f"Narrative references {term}.", fact_id=fact_id))

    return NarrativeResearchIntake(
        intake_id=intake_id, narrative=narrative,
        user_asserted_facts=tuple(facts),
        user_questions=questions,
        user_interpretations=interpretations,
        unknown_or_ambiguous_facts=tuple(unknowns),
        document_references=tuple(docs),
        dates=_extract_dates(narrative),
        people_or_entities=tuple(entities),
        locations=tuple(locations),
        courts_or_agencies=courts,
        procedural_events=tuple(events),
    )


def _resolve_jurisdiction(intake: NarrativeResearchIntake) -> JurisdictionResolution:
    lower = intake.narrative.lower()
    matches = tuple(sorted({code for alias, code in _STATE_ALIASES.items() if alias in lower}))
    state = ResolvedValue(value=matches[0], state=ResolutionState.KNOWN, evidence_ids=("narrative",)) if len(matches) == 1 else (
        ResolvedValue(state=ResolutionState.CONFLICTING, alternatives=matches, evidence_ids=("narrative",)) if matches else ResolvedValue()
    )
    country = ResolvedValue(value="US", state=ResolutionState.KNOWN if matches else ResolutionState.UNKNOWN) if matches else ResolvedValue()
    county = next((ResolvedValue(value=item.text, state=ResolutionState.KNOWN, evidence_ids=(item.entity_id,)) for item in intake.locations if "county" in item.text.lower()), ResolvedValue())
    court = ResolvedValue(value="state_appellate", state=ResolutionState.INFERRED) if _has_any(lower, ("appeal", "appellate")) else ResolvedValue()
    matter_terms = []
    for domain, terms in (("housing", ("landlord", "rent", "locks")), ("criminal", ("prosecutor", "probation", "arrest", "jail")), ("juvenile", ("child", "cps", "child welfare")), ("evidence", ("evidence", "medical records"))):
        if _has_any(lower, terms):
            matter_terms.append(domain)
    matter = ResolvedValue(value=matter_terms[0], state=ResolutionState.INFERRED) if len(matter_terms) == 1 else (
        ResolvedValue(value="mixed", state=ResolutionState.INFERRED, alternatives=tuple(matter_terms)) if matter_terms else ResolvedValue()
    )
    posture = ResolvedValue(value="appellate", state=ResolutionState.INFERRED) if _has_any(lower, ("appeal", "appealed", "appellate")) else (
        ResolvedValue(value="pending", state=ResolutionState.INFERRED) if _has_any(lower, ("upcoming hearing", "pending hearing", "next week")) else ResolvedValue()
    )
    relevant_date = next((ResolvedValue(value=date.normalized_date, state=ResolutionState.KNOWN, evidence_ids=(date.date_id,)) for date in intake.dates if date.legally_material and date.normalized_date), ResolvedValue())
    return JurisdictionResolution(country=country, state=state, county=county, court_system=court, matter_type=matter, trial_appellate_posture=posture, relevant_event_date=relevant_date)


def _issue_hypotheses(
    intake: NarrativeResearchIntake,
    *,
    p2l_ontology: Optional[PeopleToLawOntology] = None,
) -> tuple[IssueHypothesis, ...]:
    lower = intake.narrative.lower()
    facts = intake.user_asserted_facts
    results: list[IssueHypothesis] = []
    for mapping in _GENERAL_MAPPINGS:
        triggers = tuple(fact.fact_id for fact in facts if _has_any(fact.text, mapping.lay_triggers))
        if not triggers and not _has_any(lower, mapping.lay_triggers):
            continue
        results.append(IssueHypothesis(
            issue_id=mapping.issue,
            concept_id=mapping.concept_id,
            label=mapping.label,
            domain=mapping.domain,
            subdomain=mapping.subdomain,
            procedure_or_substance=mapping.procedure_or_substance,
            issue=mapping.issue,
            subissue=mapping.subissue,
            confidence=mapping.confidence,
            why_inferred=f"Candidate issue inferred from reported facts matching lay-language signals for {mapping.label}.",
            trigger_fact_ids=triggers,
            context_needed=("controlling jurisdiction", "procedural posture", "primary documents") if mapping.jurisdiction_applicability == ("GENERAL",) else ("jurisdiction-specific terminology",),
            legal_terms=mapping.legal_terms,
        ))

    # People-to-Law Child Welfare ontology scanning
    ontology = p2l_ontology or build_canonical_ontology()
    for concept in ontology.match_narrative(intake.narrative):
        issue_id = concept.concept_id.lower().replace("-", "_")
        if any(r.concept_id == concept.concept_id or r.issue_id == issue_id for r in results):
            continue
        triggers = tuple(fact.fact_id for fact in facts if _has_any(fact.text, concept.ordinary_language_aliases))
        context_items = ["controlling jurisdiction", "procedural posture"]
        if concept.disambiguation_questions:
            context_items.extend(concept.disambiguation_questions[:2])
        results.append(
            IssueHypothesis(
                issue_id=issue_id,
                concept_id=concept.concept_id,
                label=concept.preferred_label,
                domain=concept.domain.lower(),
                subdomain=concept.subdomain.lower(),
                procedure_or_substance=concept.procedure_or_substance.lower(),
                issue=issue_id,
                subissue=concept.subdomain.lower(),
                confidence=0.5,
                why_inferred=f"Candidate issue inferred from People-to-Law Child Welfare ontology matching '{concept.preferred_label}'.",
                trigger_fact_ids=triggers,
                context_needed=tuple(context_items),
                legal_terms=concept.candidate_legal_issues + tuple(concept.governing_source_families),
                ontology_source=PEOPLE_TO_LAW_CONTRACT,
                ontology_version=concept.version,
            )
        )

    if not results:
        results.append(IssueHypothesis(
            issue_id="unresolved_legal_issue", concept_id="unresolved.legal_issue",
            label="unresolved legal issue", domain="unknown", subdomain="unknown",
            procedure_or_substance="unknown", issue="unresolved_legal_issue", subissue="issue_spotting_needed",
            status=IssueStatus.UNRESOLVED_ISSUE, confidence=0.1,
            why_inferred="The narrative does not yet contain a reliable general-language trigger.",
            context_needed=("jurisdiction", "matter type", "procedural posture"),
            legal_terms=("governing law", "available procedure", "legal standard"),
        ))
    return tuple(results)


def build_research_intent(
    intake: NarrativeResearchIntake,
    *,
    p2l_ontology: Optional[PeopleToLawOntology] = None,
    source_registry: Optional[JurisdictionSourceRegistry] = None,
) -> ResearchIntent:
    jurisdiction = _resolve_jurisdiction(intake)
    issues = _issue_hypotheses(intake, p2l_ontology=p2l_ontology)
    known = tuple(fact for fact in intake.user_asserted_facts if fact.category == EvidenceCategory.USER_ASSERTED_FACT)
    disputed = tuple(fact for fact in known if _has_any(fact.text, ("they say", "i disagree", "not true", "denied")))
    inferred = tuple(NarrativeFact(fact_id=f"INFERRED-{issue.issue_id}", text=f"The narrative may implicate {issue.label}.", category=EvidenceCategory.USER_INTERPRETATION, state=ResolutionState.INFERRED, materially_relevant=True) for issue in issues)
    clarifications: list[ClarificationQuestion] = []
    if jurisdiction.state.state in {ResolutionState.UNKNOWN, ResolutionState.CONFLICTING}:
        clarifications.append(ClarificationQuestion(question_id="CLARIFY-JURISDICTION", question="Which state is the case in?", information_needed="controlling jurisdiction", expected_research_impact="State law, court hierarchy, deadlines, and remedies may change.", priority="HIGH"))
    if jurisdiction.trial_appellate_posture.state == ResolutionState.UNKNOWN:
        clarifications.append(ClarificationQuestion(question_id="CLARIFY-POSTURE", question="Is this before a trial court, an appeal, or an agency, and is anything currently pending?", information_needed="procedural posture", expected_research_impact="The governing standard and available procedure may change.", priority="HIGH"))
    dates = tuple(date for date in intake.dates if date.legally_material)
    urgency = []
    if dates or _has_any(intake.narrative, ("deadline", "tomorrow", "next week", "hearing")):
        urgency.append("deadline_or_hearing_possible")
    if _has_any(intake.narrative, ("changed the locks", "stuff outside", "homeless")):
        urgency.append("housing_displacement_possible")
    if _has_any(intake.narrative, ("took my child", "removed my child", "protective custody")):
        urgency.append("custody_removal_possible")
    if _has_any(intake.narrative, ("arrest", "jail", "probation")):
        urgency.append("criminal_liberty_possible")

    # Add P2L urgency cues and disambiguation questions
    ontology = p2l_ontology or build_canonical_ontology()
    for concept in ontology.match_narrative(intake.narrative):
        for cue in concept.urgency_cues:
            cue_lower = cue.lower()
            if cue_lower not in urgency:
                urgency.append(cue_lower)
        if concept.subdomain == "EMERGENCY_REMOVAL" and "custody_removal_possible" not in urgency:
            urgency.append("custody_removal_possible")
        for dq in concept.disambiguation_questions:
            if not any(c.question == dq for c in clarifications):
                clarifications.append(
                    ClarificationQuestion(
                        question_id=_stable_id("CLARIFY-P2L", dq),
                        question=dq,
                        information_needed=f"Disambiguate {concept.preferred_label}",
                        expected_research_impact="Determines whether statutory procedural protections or emergency review standards apply.",
                        priority="HIGH" if any(k in dq.lower() for k in ("hearing", "deadline", "appeal", "emergency")) else "MEDIUM",
                    )
                )

    research_questions = tuple(ResearchQuestion(question_id=f"RQ-{index:03d}", issue_id=issue.issue_id, question=f"What law governs {issue.label} in the identified jurisdiction and procedural posture?", why_needed="Translate the hypothesis into a researchable question without treating it as a conclusion.") for index, issue in enumerate(issues, start=1))

    sources: list[GoverningSourceCandidate] = [
        GoverningSourceCandidate(
            source_id=f"SOURCE-{index:03d}",
            description=f"Jurisdiction-specific statutes, rules, and opinions concerning {issue.label}.",
            source_kind="primary_authority",
            issue_id=issue.issue_id,
        )
        for index, issue in enumerate(issues, start=1)
    ]
    if jurisdiction.state.state == ResolutionState.KNOWN and jurisdiction.state.value:
        registry = source_registry or build_canonical_registry()
        lower_narrative = intake.narrative.lower()
        federal_applicable = (
            jurisdiction.state.value in {"US", "US-FED"}
            or any("federal" in i.domain or "civil_rights" in i.subdomain or "icwa" in i.issue_id for i in issues)
            or _has_any(lower_narrative, ("constitution", "civil rights", "1983", "icwa", "title iv-e", "federal"))
        )
        for reg_source in registry.resolve_candidate_sources(
            jurisdiction.state.value,
            include_federal_overlay=federal_applicable,
        ):
            sources.append(
                GoverningSourceCandidate(
                    source_id=reg_source.source_id,
                    description=f"{reg_source.source_name} ({reg_source.provider_name})",
                    source_kind=reg_source.authority_family.value.lower(),
                    status=ResolutionState.INFERRED,
                    official_status=reg_source.official_status.value,
                    authority_level=reg_source.authority_level.value,
                    currentness_capability=reg_source.currentness_capability.value,
                )
            )


    summary = "; ".join(issue.label for issue in issues)
    return ResearchIntent(
        intent_id=_stable_id("INTENT", intake.narrative),
        user_goal="Understand what options and governing law may apply to the reported problem." if not intake.user_questions else " ".join(intake.user_questions),
        user_problem_summary=f"Candidate research areas: {summary}.",
        jurisdiction=jurisdiction,
        jurisdiction_state=jurisdiction.state,
        procedural_posture=jurisdiction.trial_appellate_posture,
        matter_type=jurisdiction.matter_type,
        issue_hypotheses=issues,
        important_dates=dates,
        known_facts=known,
        inferred_facts=inferred,
        unknown_facts=tuple(intake.unknown_or_ambiguous_facts),
        disputed_facts=disputed,
        potential_governing_sources=tuple(sources),
        research_questions=research_questions,
        clarifications_needed=tuple(clarifications),
        urgency_flags=tuple(urgency),
        deadline_questions=("What hearing, filing, appeal, or response deadline applies, and what is its date?",) if urgency else (),
        research_constraints=("Do not treat a user label as a legal conclusion.", "Use the same authority corpus and verification standard for lay and professional modes.", "Send only abstract public-law terms to public providers."),
        source_narrative_sha256=intake.narrative_sha256,
    )



def _query_variants(issue: IssueHypothesis, query_class: QueryClass) -> tuple[str, ...]:
    terms = " ".join(issue.legal_terms)
    if query_class == QueryClass.CONTROLLING_AUTHORITY_QUERY:
        return (f"controlling authority {terms}", f"state supreme appellate {terms}")
    if query_class == QueryClass.STATUTE_RULE_QUERY:
        return (f"statute rule {terms}", f"governing rule {terms}")
    if query_class == QueryClass.FACT_PATTERN_QUERY:
        return (f"fact pattern {terms}", f"remedy procedure {terms}")
    if query_class == QueryClass.PROCEDURAL_POSTURE_QUERY:
        return (f"procedure hearing {terms}", f"standard of review {terms}")
    if query_class == QueryClass.ADVERSE_AUTHORITY_QUERY:
        return (f"contrary authority {terms}", f"adverse authority {terms}")
    if query_class == QueryClass.LIMITING_AUTHORITY_QUERY:
        return (f"limiting authority {terms}", f"distinguish {terms}")
    if query_class == QueryClass.CURRENTNESS_TREATMENT_QUERY:
        return (f"treatment currentness {terms}", f"overruled questioned {terms}")
    if query_class == QueryClass.CITATION_GRAPH_QUERY:
        return (f"citations to {terms}", f"cited by {terms}")
    if query_class == QueryClass.DEFINITION_TERMINOLOGY_QUERY:
        return (f"legal terminology {terms}", f"definition {terms}")
    return (f"legal standard {terms}", f"research doctrine {terms}")


def compile_research_plan(intent: ResearchIntent, *, plan_id: Optional[str] = None) -> ResearchPlan:
    queries: list[ResearchQuery] = []
    qualification_blocked = intent.procedural_posture.state != ResolutionState.KNOWN
    for issue_index, issue in enumerate(intent.issue_hypotheses, start=1):
        for query_index, query_class in enumerate(QueryClass, start=1):
            mode = RetrievalMode.DISCOVERY if query_class in {QueryClass.DOCTRINAL_QUERY, QueryClass.STATUTE_RULE_QUERY, QueryClass.FACT_PATTERN_QUERY, QueryClass.PROCEDURAL_POSTURE_QUERY, QueryClass.DEFINITION_TERMINOLOGY_QUERY} else RetrievalMode.QUALIFICATION
            capabilities = ("search",)
            if query_class == QueryClass.CURRENTNESS_TREATMENT_QUERY:
                capabilities = ("search", "opinion_retrieval")
            elif query_class == QueryClass.CITATION_GRAPH_QUERY:
                capabilities = ("search", "citation_graph_outbound")
            variants = _query_variants(issue, query_class)
            queries.append(ResearchQuery(
                query_id=f"Q-{issue_index:02d}-{query_index:02d}", issue_id=issue.issue_id,
                query_class=query_class, retrieval_mode=mode,
                why_this_query_exists=f"{mode.value.title()} retrieval for the {query_class.value.lower()} dimension of the issue hypothesis.",
                jurisdiction_constraints=(intent.jurisdiction_state.value,) if intent.jurisdiction_state.value else ("UNRESOLVED",),
                court_hierarchy_constraints=(intent.jurisdiction.court_system.value,) if intent.jurisdiction.court_system.value else ("UNRESOLVED",),
                date_from=min((date.normalized_date for date in intent.important_dates if date.normalized_date and not date.identity_sensitive), default=None),
                date_to=max((date.normalized_date for date in intent.important_dates if date.normalized_date and not date.identity_sensitive), default=None),
                capabilities_required=capabilities, query_variants=variants,
                target_proposition=f"Identify authorities that confirm, limit, distinguish, or reject the hypothesis about {issue.label}; do not assume the hypothesis is legally correct.",
            ))
    blocked = []
    if intent.jurisdiction_state.state != ResolutionState.KNOWN:
        blocked.append("jurisdiction_confirmation")
    if qualification_blocked:
        blocked.append("procedural_posture_confirmation")
    assumptions = ("Only general lay-language mappings were used; no state-specific vocabulary was assumed.",)
    return ResearchPlan(
        plan_id=plan_id or _stable_id("PLAN", intent.intent_id), intent_id=intent.intent_id,
        source_narrative_sha256=intent.source_narrative_sha256, queries=tuple(queries),
        blocked_dimensions=tuple(blocked), provisional_assumptions=assumptions,
    )


def compile_narrative(
    narrative: str,
    *,
    intake_id: str = "LAY-INTAKE-001",
    plan_id: Optional[str] = None,
    p2l_ontology: Optional[PeopleToLawOntology] = None,
    source_registry: Optional[JurisdictionSourceRegistry] = None,
) -> CompiledNarrativeResearch:
    intake = extract_narrative_intake(narrative, intake_id=intake_id)
    intent = build_research_intent(intake, p2l_ontology=p2l_ontology, source_registry=source_registry)
    plan = compile_research_plan(intent, plan_id=plan_id)
    quality = ResearchQualityAssessment(
        assessment_id=_stable_id("QUALITY", intake.intake_id), intent_id=intent.intent_id,
        gates=tuple(
            QualityGateResult(
                gate=gate,
                status=QualityGateStatus.BLOCKED_DEPENDENCY if gate == "LAY_LANGUAGE_RETRIEVAL_RECALL" else QualityGateStatus.PASS_FIXTURE_ONLY,
                evidence=("Synthetic qualification vectors",) if gate != "LAY_LANGUAGE_RETRIEVAL_RECALL" else ("Live mirror provider is not integration-ready",),
            )
            for gate in (
                "LAY_NARRATIVE_INGESTION", "JURISDICTION_RESOLUTION", "ISSUE_HYPOTHESIS_GENERATION",
                "QUERY_PLAN_COMPILATION", "PRIVATE_TO_PUBLIC_QUERY_ABSTRACTION",
                "LAY_LANGUAGE_RETRIEVAL_RECALL", "MULTI_PASS_RESEARCH_ORCHESTRATION",
                "PRO_SE_EXPLANATION_FIDELITY",
            )
        ),
        unresolved_dimensions=("live provider retrieval recall",),
    )
    return CompiledNarrativeResearch(
        intake=intake, intent=intent, plan=plan,
        explanation=GuidedResearchExplanation(
            explanation_id=_stable_id("EXPLANATION", intake.intake_id),
            translated_summary=intent.user_problem_summary,
            facts_treated_as_user_reported=tuple(fact.text for fact in intent.known_facts),
            assumptions=plan.provisional_assumptions,
            clarifications_needed=tuple(item.question for item in intent.clarifications_needed),
        ),
        quality=quality,
    )
