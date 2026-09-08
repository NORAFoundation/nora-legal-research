"""People-to-Law (P2L) Ontology V1 for Child Welfare / Juvenile Protection + Civil Rights Overlay.

This ontology maps ordinary lived problems and lay narratives to research hypotheses,
procedural triage questions, and governing authority families without converting user
allegations into unverified legal conclusions.
"""

from __future__ import annotations

import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


PEOPLE_TO_LAW_CONTRACT = "nora.legal-research/PeopleToLawOntology/1.0"


class PeopleToLawConcept(BaseModel):
    """Structured representation of an ordinary-language lived problem family."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    concept_id: str
    preferred_label: str
    ordinary_language_aliases: tuple[str, ...]
    domain: str = "CHILD_WELFARE"
    subdomain: str
    procedure_or_substance: str  # "PROCEDURE", "SUBSTANCE", "PROCEDURE_AND_SUBSTANCE"
    candidate_legal_issues: tuple[str, ...]
    procedural_significance: str
    urgency_cues: tuple[str, ...]
    factual_predicates: tuple[str, ...]
    disambiguation_questions: tuple[str, ...]
    neighboring_concept_ids: tuple[str, ...]
    governing_source_families: tuple[str, ...]
    false_friend_terms: tuple[str, ...]
    user_theory_nomination: Optional[str] = None
    version: str = "1.0"

    @field_validator("concept_id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not v.startswith("P2L-"):
            raise ValueError(f"concept_id must start with 'P2L-': {v}")
        return v

    @model_validator(mode="after")
    def validate_safety_invariants(self) -> "PeopleToLawConcept":
        # Ensure that retaliation or civil rights theories do not masquerade as established legal conclusions
        if "retaliat" in self.preferred_label.lower() or any("retaliat" in a.lower() for a in self.ordinary_language_aliases):
            if not self.user_theory_nomination or not self.user_theory_nomination.startswith("USER_NOMINATED_"):
                raise ValueError("Retaliation concepts must designate a USER_NOMINATED_* hypothesis")
        return self


class PeopleToLawOntology(BaseModel):
    """Collection of versioned People-to-Law concepts."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    contract: str = PEOPLE_TO_LAW_CONTRACT
    schema_version: str = "1.0"
    ontology_id: str = "nora-people-to-law-child-welfare-v1"
    concepts: tuple[PeopleToLawConcept, ...] = ()

    @field_validator("contract")
    @classmethod
    def validate_contract(cls, v: str) -> str:
        if v != PEOPLE_TO_LAW_CONTRACT:
            raise ValueError(f"unsupported PeopleToLaw contract: {v}")
        return v

    @model_validator(mode="after")
    def validate_unique_concepts(self) -> "PeopleToLawOntology":
        seen: set[str] = set()
        for c in self.concepts:
            if c.concept_id in seen:
                raise ValueError(f"Duplicate concept_id: {c.concept_id}")
            seen.add(c.concept_id)
        return self

    def get_concept(self, concept_id: str) -> Optional[PeopleToLawConcept]:
        for c in self.concepts:
            if c.concept_id == concept_id:
                return c
        return None

    def match_narrative(self, text: str) -> list[PeopleToLawConcept]:
        """Deterministic keyword/alias scanner for candidate concept discovery."""
        lowered = text.lower()
        matched: list[PeopleToLawConcept] = []
        for c in self.concepts:
            for alias in c.ordinary_language_aliases:
                pattern = r"\b" + re.escape(alias.lower()) + r"\b"
                if re.search(pattern, lowered) or alias.lower() in lowered:
                    matched.append(c)
                    break
        return matched


# Canonical V1 child welfare lived problem corpus (25 core families)
CANONICAL_CHILD_WELFARE_CONCEPTS: tuple[PeopleToLawConcept, ...] = (
    # 1. Removal / Temporary Custody
    PeopleToLawConcept(
        concept_id="P2L-CW-001-THEY-TOOK-MY-CHILD",
        preferred_label="Emergency Removal / Temporary Physical Custody",
        ordinary_language_aliases=(
            "they took my child",
            "cps took my kids",
            "police took my child",
            "social worker took my baby",
            "they took my son",
            "they took my daughter",
            "child removed from home",
        ),
        subdomain="EMERGENCY_REMOVAL",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "EMERGENCY_PROTECTIVE_CUSTODY_VALIDITY",
            "EXIGENT_CIRCUMSTANCES_REQUIREMENT",
            "TEMPORARY_PHYSICAL_CUSTODY_HEARING_TIMING",
            "CONSTITUTIONAL_PARENTAL_DUE_PROCESS_NOTICE",
        ),
        procedural_significance="Trigger for statutory 48-hour or 72-hour temporary custody / emergency protective care hearing.",
        urgency_cues=("HOURS_TO_STATUTORY_HEARING", "RECENT_REMOVAL", "NO_COURT_ORDER_YET"),
        factual_predicates=("Child physically removed from parental care by state actor or peace officer.",),
        disambiguation_questions=(
            "Did the removal occur with a prior signed court order or without a warrant?",
            "Has a temporary custody / emergency protective care hearing been scheduled?",
            "What date and hour did the removal occur?",
        ),
        neighboring_concept_ids=("P2L-CW-017-NEED-CHILD-BACK-NOW", "P2L-CW-007-RELATIVE-PLACEMENT"),
        governing_source_families=("Wis. Stat. § 48.19", "Wis. Stat. § 48.21", "Minn. Stat. § 260C.175", "Minn. Stat. § 260C.178", "U.S. Const. amend. XIV"),
        false_friend_terms=("kidnapping", "stolen child", "custody dispute with ex-spouse"),
    ),

    # 2. Case Plan / What parent must do
    PeopleToLawConcept(
        concept_id="P2L-CW-002-WONT-TELL-WHAT-TO-DO",
        preferred_label="Adequacy of Dispositional Conditions and Case Plan Notice",
        ordinary_language_aliases=(
            "they won't tell me what i have to do",
            "no case plan",
            "no one told me what i need to do to get my child back",
            "unclear requirements",
            "they won't give me a list of conditions",
        ),
        subdomain="CASE_PLAN",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "SPECIFICITY_OF_CONDITIONS_FOR_RETURN",
            "REASONABLE_EFFORTS_SERVICES_IDENTIFICATION",
            "DISPOSITIONAL_ORDER_WRITTEN_NOTICE_REQUIREMENTS",
        ),
        procedural_significance="Parent cannot be penalized for failing conditions that were never clearly ordered in writing.",
        urgency_cues=("DISPOSITION_HEARING_PENDING", "CASE_PLAN_DUE_WITHIN_30_DAYS"),
        factual_predicates=("Child in out-of-home placement; agency has not provided clear written conditions.",),
        disambiguation_questions=(
            "Was a dispositional order entered with court-ordered conditions for return?",
            "Did the caseworker give you a written out-of-home placement plan?",
        ),
        neighboring_concept_ids=("P2L-CW-003-CHANGED-CONDITIONS", "P2L-CW-022-AGENCY-DIDNT-HELP-REUNIFY"),
        governing_source_families=("Wis. Stat. § 48.355(2)(b)", "Minn. Stat. § 260C.212", "42 U.S.C. § 675(1)"),
        false_friend_terms=("caseworker bossing me around", "illegal demands"),
    ),

    # 3. Moving the goalposts / changing conditions
    PeopleToLawConcept(
        concept_id="P2L-CW-003-CHANGED-CONDITIONS",
        preferred_label="Modification of Conditions / Moving Dispositional Goalposts",
        ordinary_language_aliases=(
            "they changed what i have to do",
            "moving the goalposts",
            "they added more requirements",
            "they gave me new tasks after i finished the old ones",
            "new conditions added without court order",
        ),
        subdomain="CASE_PLAN",
        procedure_or_substance="PROCEDURE",
        candidate_legal_issues=(
            "UNILATERAL_AGENCY_MODIFICATION_OF_DISPOSITION",
            "COURT_AUTHORIZATION_REQUIRED_FOR_MODIFIED_CONDITIONS",
            "DUE_PROCESS_NOTICE_OF_REVISED_EXPECTATIONS",
        ),
        procedural_significance="Agency cannot unilaterally impose new legally binding conditions without judicial revision under notice.",
        urgency_cues=("REVIEW_HEARING_APPROACHING", "UNAUTHORIZED_CASEWORKER_DEMANDS"),
        factual_predicates=("Parent complied with original court conditions; agency introduced new unadjudicated requirements.",),
        disambiguation_questions=(
            "Are the new requirements written in a signed court order or only in an informal social worker email?",
            "Has the agency filed a formal motion to revise or modify the dispositional order?",
        ),
        neighboring_concept_ids=("P2L-CW-002-WONT-TELL-WHAT-TO-DO", "P2L-CW-009-FAILED-SERVICES"),
        governing_source_families=("Wis. Stat. § 48.363", "Minn. Stat. § 260C.212, subd. 1", "Minn. R. Juv. Prot. P. 51"),
        false_friend_terms=("double jeopardy", "breach of contract"),
    ),

    # 4. Visitation stopped
    PeopleToLawConcept(
        concept_id="P2L-CW-004-STOPPED-VISITS",
        preferred_label="Suspension / Denial of Parental Visitation",
        ordinary_language_aliases=(
            "they stopped my visits",
            "cps cancelled all my visits",
            "i can't see my kid anymore",
            "no contact allowed with my child",
            "they suspended my visits",
        ),
        subdomain="VISITATION",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "STATUTORY_PRESUMPTION_FAVORING_PARENTAL_VISITATION",
            "IMPERMISSIBLE_AGENCY_SUSPENSION_WITHOUT_JUDICIAL_FINDING_OF_HARM",
            "REASONABLE_EFFORTS_VIOLATION_VIA_VISITATION_DENIAL",
            "INTERMEDIATE_RELIEF_MOTION_FOR_VISITATION_ENFORCEMENT",
        ),
        procedural_significance="Parent-child visitation is fundamental to reunification; agency cannot suspend without court order finding harm.",
        urgency_cues=("VISITS_HALTED_RECENTLY", "CRITICAL_PARENT_CHILD_BONDING_IMPACT"),
        factual_predicates=("Parental visits suspended by caseworker or foster caregiver without formal judicial modification.",),
        disambiguation_questions=(
            "Did the judge sign an order suspending visits or did the social worker cancel them on their own?",
            "What stated reason was given for stopping the visits?",
        ),
        neighboring_concept_ids=("P2L-CW-005-REDUCED-VISITS", "P2L-CW-022-AGENCY-DIDNT-HELP-REUNIFY"),
        governing_source_families=("Wis. Stat. § 48.355(3)", "Minn. Stat. § 260C.178, subd. 3", "Minn. Stat. § 260C.212, subd. 2"),
        false_friend_terms=("contempt of court by caseworker", "custody visitation battle"),
    ),

    # 5. Visitation reduced
    PeopleToLawConcept(
        concept_id="P2L-CW-005-REDUCED-VISITS",
        preferred_label="Reduction of Visitation Frequency / Supervision Escalation",
        ordinary_language_aliases=(
            "they reduced my visits",
            "cut my visit time",
            "from unsupervised to supervised",
            "they only let me see them once a month now",
            "fewer hours with my baby",
        ),
        subdomain="VISITATION",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "PROGRESSIVE_REUNIFICATION_VISITATION_STANDARDS",
            "ARBITRARY_SUPERVISION_ESCALATION",
            "EVIDENTIARY_JUSTIFICATION_FOR_VISIT_REDUCTION",
        ),
        procedural_significance="Reduction impairs progress toward reunification and can trigger adverse permanency findings.",
        urgency_cues=("REDUCED_CONTACT_CREATES_PERMANENCY_RISK",),
        factual_predicates=("Visitation schedule reduced in frequency or subjected to heightened supervision.",),
        disambiguation_questions=(
            "What incident or allegation led to the reduction in visit time?",
            "Was a formal court hearing held before the visits were decreased?",
        ),
        neighboring_concept_ids=("P2L-CW-004-STOPPED-VISITS", "P2L-CW-015-RETALIATION"),
        governing_source_families=("Wis. Stat. § 48.355(3)", "Minn. Stat. § 260C.178, subd. 3"),
        false_friend_terms=("punishment", "harassment"),
    ),

    # 6. Moved child / Placement change
    PeopleToLawConcept(
        concept_id="P2L-CW-006-MOVED-MY-CHILD",
        preferred_label="Change in Placement / Foster Care Transfer Notice",
        ordinary_language_aliases=(
            "they moved my child",
            "transferred my kid to a new foster home",
            "changed foster homes without telling me",
            "they moved my child without notice",
            "abrupt placement change",
        ),
        subdomain="PLACEMENT",
        procedure_or_substance="PROCEDURE",
        candidate_legal_issues=(
            "MANDATORY_PARENTAL_NOTICE_PRIOR_TO_CHANGE_IN_PLACEMENT",
            "RIGHT_TO_REQUEST_HEARING_ON_PLACEMENT_CHANGE",
            "LEAST_RESTRICTIVE_SETTING_STANDARD",
        ),
        procedural_significance="Statutes require written notice to parents prior to non-emergency placement changes and provide a 10-day objection right.",
        urgency_cues=("TEN_DAY_OBJECTION_DEADLINE", "UNANNOUNCED_TRANSFER"),
        factual_predicates=("Child moved between foster homes, shelters, or residential facilities.",),
        disambiguation_questions=(
            "Did you receive a written Notice of Change in Placement before or after the move?",
            "How many days ago was the child moved?",
        ),
        neighboring_concept_ids=("P2L-CW-007-RELATIVE-PLACEMENT", "P2L-CW-008-OUT-OF-STATE-PLACEMENT"),
        governing_source_families=("Wis. Stat. § 48.357", "Minn. Stat. § 260C.212, subd. 2"),
        false_friend_terms=("kidnapping across town", "foster parent abduction"),
    ),

    # 7. Placement with relatives
    PeopleToLawConcept(
        concept_id="P2L-CW-007-RELATIVE-PLACEMENT",
        preferred_label="Statutory Kinship / Relative Placement Preference",
        ordinary_language_aliases=(
            "they placed my child with relatives",
            "they refused to place with grandma",
            "kinship care denied",
            "relative placement ignored",
            "my sister wanted to take the kids but cps said no",
            "family placement preference",
        ),
        subdomain="RELATIVE_PLACEMENT",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "STATUTORY_MANDATE_FOR_RELATIVE_SEARCH_AND_ENGAGEMENT",
            "KINSHIP_PREFERENCE_IN_OUT_OF_HOME_PLACEMENT",
            "STANDARD_FOR_DENYING_FIT_AND_WILLING_RELATIVE",
            "RELATIVE_STANDING_TO_INTERVENE_OR_PETITION",
        ),
        procedural_significance="State agencies have strict 30-day statutory duties to identify, locate, and notify adult relatives.",
        urgency_cues=("EARLY_PLACEMENT_BONDS_FORMING_WITH_STRANGER_FOSTER_CARE",),
        factual_predicates=("Fit and willing relative requested placement; agency bypassed or rejected without valid statutory grounds.",),
        disambiguation_questions=(
            "Did the relative undergo a formal background check or home study?",
            "Did the court make a specific written finding why relative placement was not in the child's best interests?",
        ),
        neighboring_concept_ids=("P2L-CW-006-MOVED-MY-CHILD", "P2L-CW-018-GOAL-TO-ADOPTION"),
        governing_source_families=("Wis. Stat. § 48.355(1)", "Minn. Stat. § 260C.221", "42 U.S.C. § 671(a)(29)"),
        false_friend_terms=("family rights trump all", "automatic relative custody"),
    ),

    # 8. Sent out of state / ICPC
    PeopleToLawConcept(
        concept_id="P2L-CW-008-OUT-OF-STATE-PLACEMENT",
        preferred_label="Interstate Placement / ICPC Compliance",
        ordinary_language_aliases=(
            "they sent my child out of state",
            "interstate placement",
            "placed across state lines",
            "sending my kid to another state",
            "icpc delays",
        ),
        subdomain="INTERSTATE_COMPACT",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "INTERSTATE_COMPACT_ON_PLACEMENT_OF_CHILDREN_COMPLIANCE",
            "JURISDICTIONAL_RETENTION_DURING_INTERSTATE_PLACEMENT",
            "IMPACT_OF_DISTANCE_ON_REUNIFICATION_VISITATION",
        ),
        procedural_significance="Interstate placement without ICPC approval is legally defective and severely burdens visitation rights.",
        urgency_cues=("DISTANCE_DESTROYS_PHYSICAL_VISITS", "ICPC_APPROVAL_PENDING"),
        factual_predicates=("Child moved or proposed to move across state boundaries.",),
        disambiguation_questions=(
            "Was an Interstate Compact on the Placement of Children (ICPC) request filed and approved?",
            "How does the agency propose to facilitate weekly parent-child visits across state lines?",
        ),
        neighboring_concept_ids=("P2L-CW-004-STOPPED-VISITS", "P2L-CW-006-MOVED-MY-CHILD"),
        governing_source_families=("Wis. Stat. § 48.988", "Minn. Stat. § 260.851", "Minn. Stat. § 260.855"),
        false_friend_terms=("extradition of child", "interstate kidnapping"),
    ),

    # 9. Failed services allegation
    PeopleToLawConcept(
        concept_id="P2L-CW-009-FAILED-SERVICES",
        preferred_label="Noncompliance with Services Allegation / Substantial Compliance",
        ordinary_language_aliases=(
            "they say i failed services",
            "cps says i didn't complete my plan",
            "caseworker claims i was noncompliant",
            "they discharged me from therapy",
            "missed parenting class",
        ),
        subdomain="SERVICE_COMPLIANCE",
        procedure_or_substance="SUBSTANCE",
        candidate_legal_issues=(
            "SUBSTANTIAL_COMPLIANCE_DOCTRINE",
            "AVAILABILITY_AND_ACCESSIBILITY_OF_COURT_ORDERED_SERVICES",
            "BURDEN_OF_PROOF_ON_PARENTAL_EFFORT_VS_AGENCY_FACILITATION",
        ),
        procedural_significance="Allegations of noncompliance form the primary factual predicate for TPR; documentation of actual efforts is required.",
        urgency_cues=("PERMANENCY_OR_TPR_TRIAL_SCHEDULED",),
        factual_predicates=("Agency reports to court that parent failed or refused required dispositional programming.",),
        disambiguation_questions=(
            "Did the agency provide referrals, transportation, or fee waivers for the ordered services?",
            "Did you complete some or all of the classes, and do you have certificates of attendance?",
        ),
        neighboring_concept_ids=("P2L-CW-022-AGENCY-DIDNT-HELP-REUNIFY", "P2L-CW-019-TPR"),
        governing_source_families=("Wis. Stat. § 48.415(2)", "Minn. Stat. § 260C.301, subd. 1(b)(5)"),
        false_friend_terms=("bad parenting charge", "failing a school test"),
    ),

    # 10. Drug test requested
    PeopleToLawConcept(
        concept_id="P2L-CW-010-WANT-DRUG-TEST",
        preferred_label="Compelled Substance Testing / Search & Due Process Limits",
        ordinary_language_aliases=(
            "they want me to take a drug test",
            "caseworker demanding urine screen",
            "forced drug test",
            "random drug testing demand",
            "they said if i don't pee in a cup they will keep my kids",
        ),
        subdomain="SUBSTANCE_TESTING",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "FOURTH_AMENDMENT_SEARCH_CONSTRAINTS_ON_BODILY_TESTING",
            "COURT_ORDER_REQUIREMENT_FOR_INVASIVE_TESTING",
            "CONSEQUENCES_OF_REFUSAL_UNDER_DISPOSITIONAL_TERMS",
            "REASONABLE_SUSPICION_NEXUS_TO_CHILD_SAFETY",
        ),
        procedural_significance="Drug screens are searches; agency demands must be grounded in an existing court order or valid consent.",
        urgency_cues=("IMMEDIATE_TESTING_DEADLINE_ASSERTED_BY_CASEWORKER",),
        factual_predicates=("Agency demanding urinalysis, hair follicle, or oral swab without explicit parent consent.",),
        disambiguation_questions=(
            "Does the current signed dispositional order explicitly mandate random chemical testing?",
            "Is substance abuse one of the specific adjudicated jurisdictional grounds in your CHIPS petition?",
        ),
        neighboring_concept_ids=("P2L-CW-011-DRUG-TEST-WRONG", "P2L-CW-025-CRIMINAL-OVERLAY"),
        governing_source_families=("Wis. Stat. § 48.355(2)(c)", "Minn. Stat. § 260C.201", "U.S. Const. amend. IV"),
        false_friend_terms=("illegal police search", "drug bust"),
    ),

    # 11. Drug test dispute / false positive
    PeopleToLawConcept(
        concept_id="P2L-CW-011-DRUG-TEST-WRONG",
        preferred_label="Evidentiary Challenge to Substance Test Accuracy / Chain of Custody",
        ordinary_language_aliases=(
            "the drug test is wrong",
            "drug test is wrong",
            "drug test wrong",
            "false positive drug test",
            "i was clean and the test lied",
            "prescription medication caused drug test positive",
            "chain of custody broken for drug test",
            "instant cup test wrong",
            "instant cup drug test",
        ),
        subdomain="SUBSTANCE_TESTING",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "SCIENTIFIC_RELIABILITY_AND_DAUBERT_MACK_CHALLENGE",
            "CONFIRMATION_TESTING_REQUIREMENT_GAS_CHROMATOGRAPHY",
            "CHAIN_OF_CUSTODY_EVIDENTIARY_FOUNDATION",
            "CROSS_REACTIVITY_AND_PRESCRIPTION_EXPLANATION",
        ),
        procedural_significance="Instant screening cups are unreliable for adjudicative findings without GC/MS laboratory confirmation.",
        urgency_cues=("IMMINENT_DETENTION_OR_VISIT_SUSPENSION_ON_TEST_RESULT",),
        factual_predicates=("State relying on positive drug test parent disputes as inaccurate or unconfirmed.",),
        disambiguation_questions=(
            "Was the test an instant immunoassay dipstick or a certified laboratory GC/MS confirmation?",
            "Were you taking prescribed medications (e.g. Adderall, Sudafed) that cross-react?",
        ),
        neighboring_concept_ids=("P2L-CW-010-WANT-DRUG-TEST", "P2L-CW-013-NOT-ALLOWED-CHALLENGE-EVIDENCE"),
        governing_source_families=("Wis. Stat. § 907.02", "Minn. R. Evid. 702", "State v. Mack standard"),
        false_friend_terms=("drug lab fraud", "crooked lab"),
    ),

    # 12. Records access denied
    PeopleToLawConcept(
        concept_id="P2L-CW-012-WONT-SHOW-RECORDS",
        preferred_label="Discovery Denial / Denial of Access to Social Services Records",
        ordinary_language_aliases=(
            "they won't show me the records",
            "cps refusing to give me case notes",
            "denied access to my child's medical records",
            "hidden court report",
            "social worker won't give me discovery",
        ),
        subdomain="DISCOVERY_AND_ACCESS",
        procedure_or_substance="PROCEDURE",
        candidate_legal_issues=(
            "STATUTORY_RIGHT_TO_INSPECT_SOCIAL_SERVICES_FILE",
            "RULE_OF_DISCOVERY_COMPLIANCE_IN_JUVENILE_COURT",
            "MANDATORY_TIMELY_DISCLOSURE_OF_COURT_REPORTS_PRIOR_TO_HEARING",
            "IN_CAMERA_INSPECTION_OF_PRIVILEGED_DOCUMENTS",
        ),
        procedural_significance="Parent is entitled by statute and due process to inspect agency records and court reports prior to hearings.",
        urgency_cues=("HEARING_WITHIN_48_HOURS_WITHOUT_FILE_ACCESS",),
        factual_predicates=("Agency withholding case records, court reports, or documentary evidence prior to an adjudicative hearing.",),
        disambiguation_questions=(
            "Have you or your attorney filed a formal written Demand for Discovery?",
            "How many days before the upcoming hearing are you, and has the agency submitted its court report?",
        ),
        neighboring_concept_ids=("P2L-CW-013-NOT-ALLOWED-CHALLENGE-EVIDENCE", "P2L-CW-023-CASEWORKER-MAKING-THINGS-UP"),
        governing_source_families=("Wis. Stat. § 48.293", "Minn. R. Juv. Prot. P. 17", "Minn. Stat. § 260C.171"),
        false_friend_terms=("foia violation", "freedom of information request"),
    ),

    # 13. Evidentiary challenge blocked
    PeopleToLawConcept(
        concept_id="P2L-CW-013-NOT-ALLOWED-CHALLENGE-EVIDENCE",
        preferred_label="Procedural Due Process / Right to Cross-Examine and Challenge Evidence",
        ordinary_language_aliases=(
            "i wasn't allowed to challenge the evidence",
            "judge wouldn't let me cross examine the social worker",
            "hearsay admitted without objection",
            "judge took the agency's word as fact",
            "denied a contested evidentiary hearing",
        ),
        subdomain="EVIDENTIARY_DUE_PROCESS",
        procedure_or_substance="PROCEDURE",
        candidate_legal_issues=(
            "CONSTITUTIONAL_RIGHT_TO_CONTESTED_EVIDENTIARY_HEARING",
            "CROSS_EXAMINATION_OF_ADVERSE_WITNESSES",
            "INADMISSIBLE_HEARSAY_IN_DISPOSITIONAL_AND_ADJUDICATIVE_PHASES",
            "PRESERVATION_OF_EVIDENTIARY_ERROR_FOR_APPEAL",
        ),
        procedural_significance="Adjudication of dependency or termination requires formal evidence; reports cannot be accepted without right to cross-examine.",
        urgency_cues=("POST_HEARING_TIMELINES_TO_RECONSIDER_OR_APPEAL",),
        factual_predicates=("Court entered order based on proffer, summary report, or hearsay over parent's request for contested hearing.",),
        disambiguation_questions=(
            "Did you or your attorney formally object on the record and request witness cross-examination?",
            "Was the hearing an informal review hearing or a contested trial/adjudication?",
        ),
        neighboring_concept_ids=("P2L-CW-014-IGNORED-MY-EVIDENCE", "P2L-CW-020-WANT-TO-APPEAL"),
        governing_source_families=("Wis. Stat. § 48.299", "Minn. R. Juv. Prot. P. 3.02", "Minn. R. Evid. 802", "U.S. Const. amend. XIV"),
        false_friend_terms=("kangaroo court", "corrupt judge lawsuit"),
    ),

    # 14. Parent's evidence ignored
    PeopleToLawConcept(
        concept_id="P2L-CW-014-IGNORED-MY-EVIDENCE",
        preferred_label="Failure to Consider Rebuttal Evidence / Evidentiary Proffer",
        ordinary_language_aliases=(
            "they ignored evidence i gave them",
            "judge wouldn't look at my papers",
            "i gave them clean drug tests and they ignored them",
            "they omitted my completion certificates",
            "my proof was excluded",
        ),
        subdomain="EVIDENTIARY_DUE_PROCESS",
        procedure_or_substance="PROCEDURE",
        candidate_legal_issues=(
            "EVIDENTIARY_PROFFER_AND_OFFER_OF_PROOF",
            "DUTY_OF_TRIER_OF_FACT_TO_WEIGH_REBUTTAL_EVIDENCE",
            "REASONABLE_EFFORTS_DEFENSE_SUPPORTED_BY_EXCLUDED_EVIDENCE",
        ),
        procedural_significance="Evidence omitted from the formal court record cannot be reviewed on appeal without an offer of proof.",
        urgency_cues=("UPCOMING_HEARING_WHERE_EVIDENCE_MUST_BE_FORMALLY_OFFERED",),
        factual_predicates=("Parent possesses exculpatory or compliance documentation that agency failed to present to court.",),
        disambiguation_questions=(
            "Was the evidence formally marked as an exhibit and offered during testimony on the record?",
            "Did the judge state on the record why the documents were not admitted?",
        ),
        neighboring_concept_ids=("P2L-CW-024-TEXTS-RECORDINGS-PROOF", "P2L-CW-013-NOT-ALLOWED-CHALLENGE-EVIDENCE"),
        governing_source_families=("Wis. Stat. § 901.03", "Minn. R. Evid. 103"),
        false_friend_terms=("tampering with evidence", "obstruction of justice"),
    ),

    # 15. Alleged retaliation
    PeopleToLawConcept(
        concept_id="P2L-CW-015-RETALIATION",
        preferred_label="Allegation of Agency Retaliation for Protected Speech / Grievance",
        ordinary_language_aliases=(
            "they retaliated after i complained",
            "social worker punished me for speaking up",
            "they filed against me because i fired my lawyer",
            "caseworker got mad when i asked for a supervisor and took my kids",
            "retaliation for filing a grievance",
        ),
        subdomain="CIVIL_RIGHTS_OVERLAY",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "USER_NOMINATED_RETALIATION_THEORY",
            "FIRST_AMENDMENT_PROTECTED_PETITIONING_ACTIVITY",
            "REASONABLE_EFFORTS_INQUIRY_INTO_AGENCY_ANIMUS",
            "INDEPENDENT_PROBABLE_CAUSE_DEFENSE_TO_RETALIATION",
            "SECTION_1983_RETALIATION_ELEMENTS_AND_IMMUNITY_BARRIERS",
        ),
        procedural_significance="Parent claims animus; juvenile court focuses on child safety, while federal §1983 faces qualified immunity and Younger abstention.",
        urgency_cues=("PENDING_STATE_CHIPS_PROCEEDING_OUTRANKS_FEDERAL_CLAIM",),
        factual_predicates=("Parent engaged in protected grievance; adverse child-welfare action followed shortly thereafter.",),
        disambiguation_questions=(
            "What was the exact date of your complaint and the exact date of the agency's action?",
            "Did the agency articulate independent safety facts in its sworn petition?",
        ),
        neighboring_concept_ids=("P2L-CW-023-CASEWORKER-MAKING-THINGS-UP", "P2L-CW-004-STOPPED-VISITS"),
        governing_source_families=("42 U.S.C. § 1983", "U.S. Const. amend. I", "Wis. Stat. § 48.21", "Minn. Stat. § 260C.178"),
        false_friend_terms=("suing the social worker immediately stops the case", "criminal civil rights charges"),
        user_theory_nomination="USER_NOMINATED_RETALIATION_THEORY",
    ),

    # 16. Judge won't hear motion
    PeopleToLawConcept(
        concept_id="P2L-CW-016-JUDGE-WONT-HEAR-MOTION",
        preferred_label="Refusal to Schedule Hearing / Judicial Inaction / Writ of Mandamus",
        ordinary_language_aliases=(
            "the judge won't hear my motion",
            "court clerk won't give me a hearing date",
            "motion sitting for months with no ruling",
            "judge refused to let me speak",
            "they won't put my motion on the calendar",
        ),
        subdomain="JUDICIAL_PROCEDURE",
        procedure_or_substance="PROCEDURE",
        candidate_legal_issues=(
            "STATUTORY_TIMEFRAME_FOR_HEARING_PARENTAL_MOTIONS",
            "PRO_SE_MOTION_PROCESSING_REQUIREMENTS",
            "PETITION_FOR_SUPERVISORY_WRIT_OR_MANDAMUS",
            "REPRESENTATION_BY_COUNSEL_RULE_AGAINST_HYBRID_REPRESENTATION",
        ),
        procedural_significance="If parent has appointed counsel, court may refuse to accept pro se motions under rules against hybrid representation.",
        urgency_cues=("UNREMEDIED_ONGOING_DEPRIVATION_OF_PARENTAL_CONTACT",),
        factual_predicates=("Motion filed with court clerk but no hearing scheduled after statutory period.",),
        disambiguation_questions=(
            "Are you currently represented by an appointed or retained attorney?",
            "Did you file a formal notice of motion and certificate of service?",
        ),
        neighboring_concept_ids=("P2L-CW-017-NEED-CHILD-BACK-NOW", "P2L-CW-020-WANT-TO-APPEAL"),
        governing_source_families=("Wis. Stat. § 809.51", "Minn. R. Civ. App. P. 120", "Minn. R. Juv. Prot. P. 15"),
        false_friend_terms=("suing the judge", "filing judicial ethics complaint to overturn order"),
    ),

    # 17. Immediate return requested
    PeopleToLawConcept(
        concept_id="P2L-CW-017-NEED-CHILD-BACK-NOW",
        preferred_label="Emergency Motion for Immediate Return / Custody Release",
        ordinary_language_aliases=(
            "i need my child back now",
            "emergency custody motion",
            "immediate return of child",
            "safety hazard has been resolved return child immediately",
            "get my baby home today",
        ),
        subdomain="EMERGENCY_REMOVAL",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "EMERGENCY_MOTION_TO_REVISE_TEMPORARY_CUSTODY",
            "CHANGE_OF_CIRCUMSTANCES_DISPELLING_PRIMA_FACIE_HAZARD",
            "TRIAL_HOME_VISIT_AUTHORIZATION",
        ),
        procedural_significance="Statutes allow parent to petition at any time for hearing on return if circumstances have materially changed.",
        urgency_cues=("URGENT_CHANGED_SAFETY_CIRCUMSTANCES",),
        factual_predicates=("Underlying safety hazard that prompted removal has ceased to exist.",),
        disambiguation_questions=(
            "What specific changed circumstance has resolved the safety issue identified at removal?",
            "Have you requested a trial home visit or conditional release under protective supervision?",
        ),
        neighboring_concept_ids=("P2L-CW-001-THEY-TOOK-MY-CHILD", "P2L-CW-002-WONT-TELL-WHAT-TO-DO"),
        governing_source_families=("Wis. Stat. § 48.21(7)", "Minn. Stat. § 260C.178, subd. 1", "Minn. Stat. § 260C.201, subd. 1"),
        false_friend_terms=("self-help repossession of child", "calling the police to get child back"),
    ),

    # 18. Goal changed to adoption
    PeopleToLawConcept(
        concept_id="P2L-CW-018-GOAL-TO-ADOPTION",
        preferred_label="Permanency Plan Shift to Adoption / ASFA Timelines",
        ordinary_language_aliases=(
            "they are changing the goal to adoption",
            "agency wants to adopt out my baby",
            "permanency goal changed from reunification",
            "giving up on reunification",
            "they want to give my child to the foster parents",
        ),
        subdomain="PERMANENCY_TPR",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "PERMANENCY_HEARING_TIMELINES_AND_STANDARDS",
            "ASFA_15_OF_22_MONTH_RULE_AND_EXCEPTIONS",
            "COMPELLING_REASONS_NOT_TO_PURSUATION_TERMINATION",
            "REASONABLE_EFFORTS_FINDING_AS_PREREQUISITE_TO_GOAL_CHANGE",
        ),
        procedural_significance="Permanency goal change is the critical procedural turning point shifting state resources away from reunification.",
        urgency_cues=("PERMANENCY_HEARING_WITHIN_30_DAYS", "12_MONTH_OUT_OF_HOME_THRESHOLD"),
        factual_predicates=("Child approaching 12 or 15 months in placement; agency proposing adoption at permanency review.",),
        disambiguation_questions=(
            "How many total months has your child spent in out-of-home placement?",
            "Did the court make an explicit finding that the agency made reasonable efforts up to this point?",
        ),
        neighboring_concept_ids=("P2L-CW-019-TPR", "P2L-CW-022-AGENCY-DIDNT-HELP-REUNIFY"),
        governing_source_families=("Wis. Stat. § 48.38", "Minn. Stat. § 260C.201, subd. 11", "Minn. Stat. § 260C.503", "42 U.S.C. § 675(5)(E)"),
        false_friend_terms=("foster parents stole my child", "child sold for federal money"),
    ),

    # 19. Termination of Parental Rights (TPR)
    PeopleToLawConcept(
        concept_id="P2L-CW-019-TPR",
        preferred_label="Termination of Parental Rights (TPR) Petition",
        ordinary_language_aliases=(
            "they want to terminate my rights",
            "tpr petition filed",
            "permanently take my kids away",
            "severing parental rights",
            "termination of parental rights summons",
        ),
        subdomain="PERMANENCY_TPR",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "STATUTORY_GROUNDS_FOR_TERMINATION",
            "CLEAR_AND_CONVINCING_EVIDENCE_STANDARD_OF_PROOF",
            "BEST_INTERESTS_OF_THE_CHILD_BIFURCATED_DISPOSITION",
            "RIGHT_TO_JURY_TRIAL_WISCONSIN_SPECIFIC",
            "RIGHT_TO_COURT_APPOINTED_COUNSEL",
        ),
        procedural_significance="Most severe state intervention; requires strict constitutional scrutiny (Santosky v. Kramer) and clear statutory proof.",
        urgency_cues=("SUMMONS_ANSWER_DEADLINE", "INITIAL_APPEARANCE_MANDATORY", "DEMAND_FOR_JURY_DEADLINE"),
        factual_predicates=("Formal summons and petition for termination of parental rights served on parent.",),
        disambiguation_questions=(
            "What specific statutory grounds are alleged in the petition (e.g., continuing CHIPS, abandonment, failure to assume responsibility)?",
            "If in Wisconsin, has a timely demand for a jury trial been filed within statutory deadlines?",
        ),
        neighboring_concept_ids=("P2L-CW-018-GOAL-TO-ADOPTION", "P2L-CW-020-WANT-TO-APPEAL"),
        governing_source_families=("Wis. Stat. § 48.415", "Wis. Stat. § 48.424", "Minn. Stat. § 260C.301", "Santosky v. Kramer, 455 U.S. 745"),
        false_friend_terms=("criminal conviction", "felony parental unfitness"),
    ),

    # 20. Want to appeal
    PeopleToLawConcept(
        concept_id="P2L-CW-020-WANT-TO-APPEAL",
        preferred_label="Appellate Review of Juvenile Order / Strict Notice Deadlines",
        ordinary_language_aliases=(
            "i want to appeal",
            "appeal juvenile court ruling",
            "take this to the court of appeals",
            "fight the judge's decision in higher court",
            "appeal my chips case",
        ),
        subdomain="APPELLATE_REVIEW",
        procedure_or_substance="PROCEDURE",
        candidate_legal_issues=(
            "SHORTENED_STATUTORY_DEADLINE_FOR_NOTICE_OF_APPEAL",
            "FINALITY_OF_ORDER_FOR_PURPOSES_OF_APPEAL",
            "APPOINTMENT_OF_APPELLATE_COUNSEL_FOR_INDIGENT_PARENT",
            "PRESERVATION_OF_ISSUES_IN_TRIAL_COURT_RECORD",
        ),
        procedural_significance="Juvenile appeals have jurisdictional, non-extendable deadlines (e.g. 20 days in MN under MRJPP 23; 30-day notice of intent in WI under § 809.107).",
        urgency_cues=("CRITICAL_JURISDICTIONAL_APPEAL_DEADLINE_DAYS_REMAINING",),
        factual_predicates=("Adverse final dispositional, permanency, or TPR order signed by juvenile court judge.",),
        disambiguation_questions=(
            "What was the exact date the written order was signed and entered into the court record?",
            "Has your trial attorney filed a Notice of Intent to Pursue Post-Disposition Relief?",
        ),
        neighboring_concept_ids=("P2L-CW-021-WHAT-ORDER-CAN-APPEAL", "P2L-CW-019-TPR"),
        governing_source_families=("Wis. Stat. § 809.107", "Minn. R. Juv. Prot. P. 23", "Minn. R. Civ. App. P. 104"),
        false_friend_terms=("standard 30-day civil appeal window", "appealing to supreme court first"),
    ),

    # 21. What order can I appeal?
    PeopleToLawConcept(
        concept_id="P2L-CW-021-WHAT-ORDER-CAN-APPEAL",
        preferred_label="Finality of Order / Interlocutory vs Final Appealable Orders",
        ordinary_language_aliases=(
            "i don't know what order i can appeal",
            "can i appeal a review hearing order",
            "interlocutory appeal",
            "is the emergency custody order appealable",
            "can i appeal the magistrate's decision",
        ),
        subdomain="APPELLATE_REVIEW",
        procedure_or_substance="PROCEDURE",
        candidate_legal_issues=(
            "APPEALABILITY_OF_INTERLOCUTORY_TEMPORARY_ORDERS",
            "FINAL_DISPOSITIONAL_ORDER_DOCTRINE",
            "PETITION_FOR_DISCRETIONARY_INTERLOCUTORY_REVIEW",
            "TIMELY_FILING_OF_OBJECTION_TO_REFEREE_MAGISTRATE_RULING",
        ),
        procedural_significance="Review hearings and temporary orders are generally interlocutory; attempting to appeal non-final orders leads to dismissal.",
        urgency_cues=("POTENTIAL_WAIVER_IF_WRONG_VEHICLE_CHOSEN",),
        factual_predicates=("Parent dissatisfied with intermediate ruling prior to formal disposition or TPR final judgment.",),
        disambiguation_questions=(
            "Was the order entered by a referee/magistrate requiring judge review first (e.g. MN MRJPP 22)?",
            "Does the order dispose of all claims, or is a dispositional hearing still scheduled?",
        ),
        neighboring_concept_ids=("P2L-CW-020-WANT-TO-APPEAL", "P2L-CW-016-JUDGE-WONT-HEAR-MOTION"),
        governing_source_families=("Wis. Stat. § 808.03", "Minn. R. Civ. App. P. 103.03", "Minn. R. Juv. Prot. P. 22"),
        false_friend_terms=("appealing any paperwork", "referee decision is final supreme order"),
    ),

    # 22. Agency didn't help reunify / Reasonable efforts
    PeopleToLawConcept(
        concept_id="P2L-CW-022-AGENCY-DIDNT-HELP-REUNIFY",
        preferred_label="Lack of Reasonable Efforts by Child Welfare Agency",
        ordinary_language_aliases=(
            "the agency didn't help me reunify",
            "cps did nothing to help me",
            "no reasonable efforts by social worker",
            "caseworker didn't provide required services",
            "they set me up to fail with no help",
            "agency refused to pay for court ordered treatment",
        ),
        subdomain="REASONABLE_EFFORTS",
        procedure_or_substance="SUBSTANCE",
        candidate_legal_issues=(
            "STATUTORY_MANDATE_FOR_REASONABLE_EFFORTS_TO_REUNIFY",
            "TIMELINESS_AVAILABILITY_AND_APPROPRIATENESS_OF_SERVICES",
            "FAILURE_TO_MAKE_REASONABLE_EFFORTS_BARS_GOAL_CHANGE_OR_TPR",
            "AMERICANS_WITH_DISABILITIES_ACT_ACCOMMODATION_IN_SERVICES",
        ),
        procedural_significance="Agency must prove by clear evidence that it made affirmative, customized efforts to help parent satisfy conditions.",
        urgency_cues=("EVERY_PERMANENCY_HEARING_REQUIRES_REASONABLE_EFFORTS_FINDING",),
        factual_predicates=("Parent willing to participate; agency failed to provide referrals, transportation, or required services.",),
        disambiguation_questions=(
            "Did you request specific services in writing that were ignored or refused?",
            "Did the court make a 'reasonable efforts made' finding at the last review hearing without parental objection?",
        ),
        neighboring_concept_ids=("P2L-CW-002-WONT-TELL-WHAT-TO-DO", "P2L-CW-009-FAILED-SERVICES"),
        governing_source_families=("Wis. Stat. § 48.355(2c)", "Minn. Stat. § 260.012", "42 U.S.C. § 671(a)(15)"),
        false_friend_terms=("agency owes me compensation", "sue worker for bad customer service"),
    ),

    # 23. Caseworker fabricating allegations
    PeopleToLawConcept(
        concept_id="P2L-CW-023-CASEWORKER-MAKING-THINGS-UP",
        preferred_label="Allegation of Fabricated Evidence / Perjury / Impeachment of Social Worker",
        ordinary_language_aliases=(
            "the caseworker is making things up",
            "cps worker lied in court report",
            "fabricated allegations in petition",
            "social worker perjury",
            "false statements in affidavit",
        ),
        subdomain="EVIDENTIARY_DUE_PROCESS",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "USER_NOMINATED_DEFAMATION_OR_PERJURY_THEORY",
            "IMPEACHMENT_OF_WITNESS_WITH_PRIOR_INCONSISTENT_STATEMENTS",
            "CONSTITUTIONAL_CLAIM_FOR_FABRICATION_OF_EVIDENCE_DEVEREUX",
            "MOTION_TO_STRIKE_FALSE_STATEMENTS_FROM_COURT_REPORT",
        ),
        procedural_significance="Juvenile court remedies focus on evidentiary impeachment and exclusion; civil liability faces qualified immunity bars.",
        urgency_cues=("IMPENDING_HEARING_WHERE_REPORT_WILL_BE_ACCEPTED_UNLESS_CHALLENGED",),
        factual_predicates=("Court report contains factual statements contradicted by objective documentary evidence.",),
        disambiguation_questions=(
            "Do you have objective records (e.g. time-stamped texts, provider attendance logs) proving the statement is false?",
            "Has your attorney prepared cross-examination to impeach the caseworker on the stand?",
        ),
        neighboring_concept_ids=("P2L-CW-024-TEXTS-RECORDINGS-PROOF", "P2L-CW-013-NOT-ALLOWED-CHALLENGE-EVIDENCE"),
        governing_source_families=("Wis. Stat. § 906.07", "Minn. R. Evid. 607", "Devereaux v. Abbey, 263 F.3d 1070"),
        false_friend_terms=("pressing criminal charges against social worker", "suing for slander in juvenile court"),
        user_theory_nomination="USER_NOMINATED_FABRICATION_THEORY",
    ),

    # 24. Texts/recordings evidence
    PeopleToLawConcept(
        concept_id="P2L-CW-024-TEXTS-RECORDINGS-PROOF",
        preferred_label="Authentication and Admissibility of Electronic Evidence and Recordings",
        ordinary_language_aliases=(
            "i have texts proving it",
            "i have recordings proving it",
            "i recorded the social worker",
            "screenshots of texts with caseworker",
            "audio recording of visit",
        ),
        subdomain="EVIDENTIARY_DUE_PROCESS",
        procedure_or_substance="PROCEDURE",
        candidate_legal_issues=(
            "EVIDENTIARY_AUTHENTICATION_OF_DIGITAL_COMMUNICATIONS",
            "STATE_ONE_PARTY_CONSENT_RECORDING_STATUTES",
            "BEST_EVIDENCE_RULE_AND_COMPLETE_TRANSCRIPTS",
            "FOUNDATION_FOR_ADMITTING_SCREENSHOTS",
        ),
        procedural_significance="Wisconsin and Minnesota are one-party consent states, but electronic evidence must be authenticated and submitted in admissible form.",
        urgency_cues=("EVIDENCE_PRESERVATION_AND_EXTRACT_CREATION",),
        factual_predicates=("Parent holds digital files (audio, SMS, email) contradicting agency allegations.",),
        disambiguation_questions=(
            "Have you preserved full message threads with dates/timestamps rather than selective cropped screenshots?",
            "Has a certified transcript of the audio recording been prepared with speaker identification?",
        ),
        neighboring_concept_ids=("P2L-CW-023-CASEWORKER-MAKING-THINGS-UP", "P2L-CW-014-IGNORED-MY-EVIDENCE"),
        governing_source_families=("Wis. Stat. § 909.01", "Wis. Stat. § 968.31", "Minn. R. Evid. 901", "Minn. Stat. § 626A.02"),
        false_friend_terms=("illegal wiretapping assumption", "showing my phone screen to the judge on the bench"),
    ),

    # 25. Concurrent criminal case
    PeopleToLawConcept(
        concept_id="P2L-CW-025-CRIMINAL-OVERLAY",
        preferred_label="Fifth Amendment Privilege / Parallel Child Welfare & Criminal Proceedings",
        ordinary_language_aliases=(
            "my criminal case is affecting the child-welfare case",
            "parallel criminal charges and cps",
            "i can't testify because of criminal charges",
            "pleading the fifth in juvenile court",
            "social worker sharing my statements with prosecutor",
        ),
        subdomain="CIVIL_RIGHTS_OVERLAY",
        procedure_or_substance="PROCEDURE_AND_SUBSTANCE",
        candidate_legal_issues=(
            "FIFTH_AMENDMENT_PRIVILEGE_AGAINST_SELF_INCRIMINATION",
            "ADVERSE_INFERENCE_IN_CIVIL_CHILD_PROTECTION_PROCEEDINGS",
            "USE_IMMUNITY_FOR_PARENTAL_STATEMENTS_IN_CHIPS_ASSESSMENTS",
            "MOTION_TO_STAY_CHIPS_PROCEEDINGS_PENDING_CRIMINAL_RESOLUTION",
        ),
        procedural_significance="Parent faces dilemma: testifying in CHIPS risks criminal indictment; invoking 5th Amendment permits adverse civil inference.",
        urgency_cues=("CRIMINAL_TRIAL_PENDING_CONCURRENT_WITH_CHIPS_TRIAL",),
        factual_predicates=("Parent subject to open criminal investigation or charges arising from same events as CHIPS petition.",),
        disambiguation_questions=(
            "Are your criminal defense attorney and child-welfare attorney coordinating strategy?",
            "Has a motion for use immunity or in camera testimony been requested?",
        ),
        neighboring_concept_ids=("P2L-CW-010-WANT-DRUG-TEST", "P2L-CW-015-RETALIATION"),
        governing_source_families=("U.S. Const. amend. V", "Wis. Stat. § 48.299(4)", "Minn. Stat. § 260C.163, subd. 6"),
        false_friend_terms=("double jeopardy prevents cps case", "pleading the fifth means child is returned"),
    ),
)


def build_canonical_ontology() -> PeopleToLawOntology:
    return PeopleToLawOntology(
        ontology_id="nora-people-to-law-child-welfare-v1",
        concepts=CANONICAL_CHILD_WELFARE_CONCEPTS,
    )
