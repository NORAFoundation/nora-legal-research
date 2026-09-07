from __future__ import annotations

import json
from pathlib import Path

import pytest

from nora_legal_research.research_quality import (
    AssessmentStatus,
    AuthorityQualification,
    AuthorityQualificationStatus,
    CompletenessStatus,
    DimensionAssessment,
    EpistemicStatus,
    FactEvidence,
    ProfessionalFinding,
    ProfessionalResearchRecord,
    ResearchCompleteness,
    ResearchDimension,
    SourceEvidence,
    SourceType,
    assess_completeness,
    to_non_lawyer_explanation,
)


ROOT = Path(__file__).parents[1]


def dimensions(status: CompletenessStatus = CompletenessStatus.COMPLETE) -> tuple[DimensionAssessment, ...]:
    return tuple(
        DimensionAssessment(
            dimension=dimension,
            status=status,
            basis="synthetic qualification evidence",
            evidence_ids=(f"E-{index:02d}",),
        )
        for index, dimension in enumerate(ResearchDimension, start=1)
    )


def matrix_dimensions() -> tuple[DimensionAssessment, ...]:
    vector = json.loads((ROOT / "fixtures/research-quality/qualification-matrix.json").read_text())
    return tuple(DimensionAssessment.model_validate(item) for item in vector["dimensions"])


def test_completeness_is_partial_when_material_dimensions_remain_unknown() -> None:
    quality = assess_completeness("QA-001", "R-004", matrix_dimensions())

    assert quality.overall_status == CompletenessStatus.PARTIAL
    assert not quality.stopping_rule_met
    assert ResearchDimension.CURRENTNESS_TREATMENT in quality.blocked_dimensions
    assert ResearchDimension.CURRENTNESS_TREATMENT in quality.unresolved_dimensions


def test_completeness_requires_all_dimensions_and_explicit_stopping_basis() -> None:
    quality = assess_completeness("QA-002", "R-004", dimensions())

    assert quality.overall_status == CompletenessStatus.COMPLETE
    assert quality.stopping_rule_met
    assert quality.stop_basis
    assert quality.unresolved_dimensions == ()

    incomplete = quality.model_dump()
    incomplete["overall_status"] = "COMPLETE"
    incomplete["stopping_rule_met"] = False
    incomplete["stop_basis"] = []
    with pytest.raises(ValueError):
        ResearchCompleteness.model_validate(incomplete)


def test_completeness_rejects_duplicate_or_inconsistent_dimension_ledgers() -> None:
    quality = assess_completeness("QA-002B", "R-004", dimensions())
    duplicate = quality.model_dump()
    duplicate["dimensions"] = (*duplicate["dimensions"], duplicate["dimensions"][0])
    with pytest.raises(ValueError):
        ResearchCompleteness.model_validate(duplicate)

    inconsistent = quality.model_dump()
    inconsistent["unresolved_dimensions"] = [ResearchDimension.JURISDICTION.value]
    with pytest.raises(ValueError):
        ResearchCompleteness.model_validate(inconsistent)


def test_missing_dimension_is_blocked_not_treated_as_no_law() -> None:
    quality = assess_completeness(
        "QA-003",
        "R-004",
        (DimensionAssessment(dimension=ResearchDimension.JURISDICTION, status=CompletenessStatus.UNKNOWN, basis="No state supplied"),),
    )

    assert quality.overall_status == CompletenessStatus.BLOCKED
    assert ResearchDimension.CONTROLLING_AUTHORITY in quality.blocked_dimensions
    assert "NO LAW" not in str(quality.model_dump())


def test_authority_qualification_does_not_promote_retrieval_to_qualified() -> None:
    provisional = AuthorityQualification(
        authority_id="CL-001",
        source_id="SRC-001",
        retrieval=AssessmentStatus.SUPPORTED,
        evidence_ids=("SRC-001",),
        limitations=("Retrieval does not establish treatment or currentness.",),
    )
    assert provisional.qualification_status == AuthorityQualificationStatus.PROVISIONAL

    with pytest.raises(ValueError):
        AuthorityQualification(authority_id="CL-002", qualification_status=AuthorityQualificationStatus.QUALIFIED)


def test_qualified_authority_requires_identity_hierarchy_voice_fit_quote_currentness_and_treatment() -> None:
    qualified = AuthorityQualification(
        authority_id="CL-003",
        source_id="SRC-003",
        retrieval=AssessmentStatus.VERIFIED,
        identity=AssessmentStatus.VERIFIED,
        jurisdiction=AssessmentStatus.VERIFIED,
        hierarchy=AssessmentStatus.VERIFIED,
        opinion_voice=AssessmentStatus.VERIFIED,
        procedural_fit=AssessmentStatus.VERIFIED,
        quote_verification=AssessmentStatus.VERIFIED,
        currentness=AssessmentStatus.VERIFIED,
        treatment=AssessmentStatus.VERIFIED,
        qualification_status=AuthorityQualificationStatus.QUALIFIED,
        evidence_ids=("SRC-003",),
    )

    assert qualified.qualification_status == AuthorityQualificationStatus.QUALIFIED


def test_guided_explanation_preserves_epistemic_boundaries() -> None:
    completeness = assess_completeness("QA-004", "R-004", dimensions(CompletenessStatus.PARTIAL))
    record = ProfessionalResearchRecord(
        record_id="PR-004",
        research_id="R-004",
        facts=(
            FactEvidence(fact_id="F-USER", statement="The user says notice was confusing.", epistemic_status=EpistemicStatus.USER_REPORTED, source_ids=("S-NARRATIVE",)),
            FactEvidence(fact_id="F-PRIMARY", statement="The filed order states a hearing date.", epistemic_status=EpistemicStatus.PRIMARY_SOURCE_VERIFIED, source_ids=("S-ORDER",)),
        ),
        sources=(
            SourceEvidence(source_id="S-NARRATIVE", source_type=SourceType.USER_NARRATIVE, epistemic_status=EpistemicStatus.USER_REPORTED),
            SourceEvidence(source_id="S-ORDER", source_type=SourceType.PRIMARY_AUTHORITY, public=True, epistemic_status=EpistemicStatus.PRIMARY_SOURCE_VERIFIED),
        ),
        findings=(
            ProfessionalFinding(finding_id="FIND-1", statement="The order contains a hearing date.", status=EpistemicStatus.PRIMARY_SOURCE_VERIFIED, evidence_ids=("F-PRIMARY",)),
            ProfessionalFinding(finding_id="FIND-2", statement="Notice adequacy remains unresolved.", status=EpistemicStatus.INFERRED, evidence_ids=("F-USER",)),
        ),
        completeness=completeness,
        review_required=("Verify currentness and procedural posture.",),
    )
    explanation = to_non_lawyer_explanation(record, explanation_id="EXP-004", user_summary="I translated your story into research questions.")

    assert explanation.reported_facts == ("The user says notice was confusing.",)
    assert explanation.independently_verified_findings == ("The order contains a hearing date.",)
    assert "Notice adequacy remains unresolved." in explanation.unresolved_or_disputed
    assert "underlying research standard is unchanged" in explanation.research_standard_note


def test_professional_record_rejects_unknown_finding_evidence() -> None:
    with pytest.raises(ValueError):
        ProfessionalResearchRecord(
            record_id="PR-005",
            research_id="R-005",
            findings=(ProfessionalFinding(finding_id="FIND-5", statement="Unsupported", status=EpistemicStatus.INFERRED, evidence_ids=("MISSING",)),),
            completeness=assess_completeness("QA-005", "R-005", dimensions()),
        )


def test_professional_record_rejects_unknown_fact_source_evidence() -> None:
    with pytest.raises(ValueError):
        ProfessionalResearchRecord(
            record_id="PR-006",
            research_id="R-006",
            facts=(FactEvidence(
                fact_id="F-006", statement="Reported fact", epistemic_status=EpistemicStatus.USER_REPORTED,
                source_ids=("MISSING-SOURCE",),
            ),),
            completeness=assess_completeness("QA-006", "R-006", dimensions()),
        )
